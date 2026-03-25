"""Data coordinator for Intervals.icu."""

from __future__ import annotations

import hashlib
import logging
import math
import re
from datetime import date, timedelta
from decimal import Decimal
from statistics import mean, stdev
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    IntervalsIcuApiClient,
    IntervalsIcuApiError,
    IntervalsIcuAuthError,
    IntervalsIcuConnectionError,
)
from .const import (
    CONF_ATHLETE_ID,
    CONF_BIRTHDATE,
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    HRV_BASELINE_LAG_DAYS,
    HRV_BASELINE_LOWER_PERCENTILE,
    HRV_BASELINE_MIN_SAMPLES,
    HRV_BASELINE_UPPER_PERCENTILE,
    HRV_BASELINE_WINDOW_DAYS,
    HRV_LOW_CUTOFF_MIN_DELTA_MS,
    HRV_LOW_CUTOFF_RANGE_FACTOR,
    HRV_POOR_PERSISTENCE_DAYS,
    HRV_STATUS_HISTORY_DAYS,
    HRV_STATUS_BOOTSTRAP_DAYS,
    HRV_STATUS_MIN_SAMPLES,
    HRV_STATUS_WINDOW_DAYS,
)

_LOGGER = logging.getLogger(__name__)

_ACTIVITY_DAILY_FIELDS = ("id", "start_date_local", "calories")

_WELLNESS_NO_ROLLOVER_KEYS = {
    "id",
    "updated",
    "comments",
    "locked",
    "sleepSecs",
    "sleepScore",
    "sleepQuality",
    "avgSleepingHR",
    "steps",
    "kcalConsumed",
    "carbohydrates",
    "protein",
    "fatTotal",
    "hydrationVolume",
}

_HRV_LEVEL_BALANCED = "balanced"
_HRV_LEVEL_UNBALANCED = "unbalanced"
_HRV_LEVEL_LOW = "low"
_HRV_LEVEL_POOR = "poor"
_HRV_LEVEL_NO_STATUS = "no_status"

_HRV_SOURCE_STATUS_OK = "ok"
_HRV_SOURCE_STATUS_INSUFFICIENT = "insufficient_data"
_HRV_SOURCE_STATUS_ERROR = "error"

_HRV_BASELINE_SUPPRESS_WHEN_POOR = True

_HRV_LEVEL_COMPACT_CODES = {
    _HRV_LEVEL_BALANCED: "b",
    _HRV_LEVEL_UNBALANCED: "u",
    _HRV_LEVEL_LOW: "l",
    _HRV_LEVEL_POOR: "p",
    _HRV_LEVEL_NO_STATUS: "n",
}

_AGE_NORM_LOWER_BOUNDS_BY_SEX: dict[str, tuple[tuple[int, int, float], ...]] = {
    "female": (
        (18, 24, 32.0),
        (25, 34, 30.0),
        (35, 44, 27.0),
        (45, 54, 24.0),
        (55, 64, 21.0),
        (65, 120, 18.0),
    ),
    "male": (
        (18, 24, 30.0),
        (25, 34, 28.0),
        (35, 44, 25.0),
        (45, 54, 22.0),
        (55, 64, 19.0),
        (65, 120, 16.0),
    ),
    "unknown": (
        (18, 24, 31.0),
        (25, 34, 29.0),
        (35, 44, 26.0),
        (45, 54, 23.0),
        (55, 64, 20.0),
        (65, 120, 17.0),
    ),
}


class IntervalsIcuCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate Intervals.icu API polling for all entities in one config entry."""

    def __init__(
        self,
        hass,
        entry: ConfigEntry,
        api: IntervalsIcuApiClient,
    ) -> None:
        self.api = api
        self.athlete_id = str(entry.data[CONF_ATHLETE_ID])
        self._birthdate_override = _parse_iso_date(
            entry.options.get(CONF_BIRTHDATE) or entry.data.get(CONF_BIRTHDATE)
        )
        self._rollover_cache: dict[str, dict[str, Any]] = {
            "summary": {},
            "wellness": {},
            "wellness_sport_metrics": {},
        }
        self._hrv_status_cache: dict[str, Any] = {}
        self._hrv_history_days = HRV_STATUS_BOOTSTRAP_DAYS

        scan_interval = int(
            entry.options.get(
                CONF_SCAN_INTERVAL_MINUTES,
                entry.data.get(CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES),
            )
        )

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(minutes=scan_interval),
            always_update=False,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest Intervals.icu data used by sensors."""
        try:
            athlete = await self.api.get_athlete(self.athlete_id)
            summary_rows = await self.api.get_athlete_summary(self.athlete_id)
        except IntervalsIcuAuthError as err:
            raise ConfigEntryAuthFailed from err
        except IntervalsIcuConnectionError as err:
            raise UpdateFailed(str(err)) from err
        except IntervalsIcuApiError as err:
            raise UpdateFailed(str(err)) from err

        athlete_id = str(athlete.get("id") or self.athlete_id)
        summary = self._apply_rollover(
            "summary",
            _select_latest_summary(summary_rows, athlete_id),
            no_rollover_keys=set(),
        )

        try:
            activity_daily = await self._async_fetch_daily_activity_calories()
        except IntervalsIcuAuthError as err:
            raise ConfigEntryAuthFailed from err

        try:
            wellness_rows, wellness_error = await self._async_fetch_wellness_history(summary)
        except IntervalsIcuAuthError as err:
            raise ConfigEntryAuthFailed from err
        except IntervalsIcuConnectionError as err:
            raise UpdateFailed(str(err)) from err

        wellness = self._apply_rollover(
            "wellness",
            _select_latest_wellness_row(wellness_rows),
            no_rollover_keys=_WELLNESS_NO_ROLLOVER_KEYS,
        )
        wellness_sport_metrics = self._apply_rollover(
            "wellness_sport_metrics",
            _flatten_wellness_sport_info(wellness),
            no_rollover_keys=set(),
        )
        wellness_hrv_status = self._derive_hrv_status_payload(
            athlete=athlete,
            wellness_rows=wellness_rows,
            source_error=wellness_error,
        )

        return {
            "athlete": athlete,
            "summary": summary,
            "activity_daily": activity_daily,
            "wellness": wellness,
            "wellness_sport_metrics": wellness_sport_metrics,
            "wellness_hrv_status": wellness_hrv_status,
        }

    async def _async_fetch_daily_activity_calories(self) -> dict[str, Any]:
        """Fetch and aggregate day-level activity calories."""
        calculation_date = dt_util.now().date().isoformat()
        oldest, newest = _activity_window_bounds(calculation_date)

        try:
            activities = await self.api.list_activities(
                self.athlete_id,
                oldest=oldest,
                newest=newest,
                fields=_ACTIVITY_DAILY_FIELDS,
            )
        except IntervalsIcuAuthError:
            raise
        except (IntervalsIcuConnectionError, IntervalsIcuApiError) as err:
            _LOGGER.debug(
                "Failed loading day activities for athlete %s (%s): %s",
                self.athlete_id,
                calculation_date,
                err,
            )
            return _activity_daily_error_payload(calculation_date, str(err))

        return _aggregate_daily_activity_calories(activities, calculation_date)

    async def _async_fetch_wellness_history(
        self, summary: dict[str, Any]
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch bounded wellness history used for latest wellness and HRV derivation."""
        newest = dt_util.now().date().isoformat()
        oldest = (dt_util.now().date() - timedelta(days=self._hrv_history_days - 1)).isoformat()

        try:
            rows = await self.api.list_wellness_records(
                self.athlete_id,
                oldest=oldest,
                newest=newest,
            )
            error: str | None = None
        except IntervalsIcuAuthError:
            raise
        except IntervalsIcuConnectionError:
            raise
        except IntervalsIcuApiError as err:
            _LOGGER.debug(
                "Failed loading wellness history for athlete %s (%s -> %s): %s",
                self.athlete_id,
                oldest,
                newest,
                err,
            )
            rows = []
            error = str(err)

        if rows:
            return rows, error

        recent_id = summary.get("mostRecentWellnessId")
        if isinstance(recent_id, str) and recent_id:
            try:
                row = await self.api.get_wellness_record(self.athlete_id, recent_id)
                return [row], error
            except IntervalsIcuAuthError:
                raise
            except IntervalsIcuConnectionError:
                raise
            except IntervalsIcuApiError as err:
                _LOGGER.debug(
                    "Failed loading fallback wellness record %s for athlete %s: %s",
                    recent_id,
                    self.athlete_id,
                    err,
                )
                if error is None:
                    error = str(err)

        return [], error

    def _derive_hrv_status_payload(
        self,
        *,
        athlete: dict[str, Any],
        wellness_rows: list[dict[str, Any]],
        source_error: str | None,
    ) -> dict[str, Any]:
        """Derive Garmin-like HRV status payload for sensor entities."""
        samples_by_date = _normalize_wellness_hrv_samples(wellness_rows)
        if not samples_by_date:
            self._hrv_status_cache = {}
            return _hrv_status_empty_payload(source_error=source_error)

        fingerprint = _hrv_sample_fingerprint(samples_by_date)
        cached_fingerprint = self._hrv_status_cache.get("fingerprint")
        cached_payload = self._hrv_status_cache.get("latest_payload")
        if cached_fingerprint == fingerprint and isinstance(cached_payload, dict):
            reused_payload = dict(cached_payload)
            reused_payload["cache_hit"] = True
            if source_error and reused_payload.get("error") is None:
                reused_payload["error"] = source_error
            return reused_payload

        birthdate, birthdate_source = _resolve_birthdate(
            athlete=athlete,
            birthdate_override=self._birthdate_override,
        )
        sex = _normalize_sex(athlete.get("sex"))

        ordered_dates = sorted(samples_by_date)
        points_by_date, last_index_recomputed = self._derive_hrv_points(
            ordered_dates=ordered_dates,
            samples_by_date=samples_by_date,
            birthdate=birthdate,
            sex=sex,
        )

        latest_date = ordered_dates[-1]
        latest_point = points_by_date.get(latest_date)
        if not isinstance(latest_point, dict):
            self._hrv_status_cache = {}
            return _hrv_status_empty_payload(source_error=source_error)

        payload = _build_hrv_status_payload(
            latest_date=latest_date,
            latest_point=latest_point,
            overnight_hrv=samples_by_date.get(latest_date),
            source_error=source_error,
            cache_hit=False,
            birthdate_source=birthdate_source,
            sex=sex,
            recompute_mode=(
                "full"
                if last_index_recomputed == 0
                else "incremental"
            ),
            points_total=len(points_by_date),
        )
        payload["history_28d"] = _build_hrv_history_28d(
            ordered_dates=ordered_dates,
            samples_by_date=samples_by_date,
            points_by_date=points_by_date,
        )

        self._hrv_status_cache = {
            "fingerprint": fingerprint,
            "samples_by_date": {day.isoformat(): value for day, value in samples_by_date.items()},
            "points_by_date": {day.isoformat(): point for day, point in points_by_date.items()},
            "latest_payload": payload,
        }

        return payload

    def _derive_hrv_points(
        self,
        *,
        ordered_dates: list[date],
        samples_by_date: dict[date, float],
        birthdate: date | None,
        sex: str,
    ) -> tuple[dict[date, dict[str, Any]], int]:
        """Derive point-by-point HRV status values, reusing cached prefixes when safe."""
        points_by_date: dict[date, dict[str, Any]] = {}
        start_index = 0
        poor_streak = 0

        previous_samples = _deserialize_cached_samples(
            self._hrv_status_cache.get("samples_by_date")
        )
        previous_points = _deserialize_cached_points(self._hrv_status_cache.get("points_by_date"))

        if previous_samples and previous_points:
            changed_date = _earliest_changed_date(previous_samples, samples_by_date)
            if changed_date is not None:
                start_index = _first_index_on_or_after(ordered_dates, changed_date)

                reusable_dates = ordered_dates[:start_index]
                if reusable_dates and all(day in previous_points for day in reusable_dates):
                    for day in reusable_dates:
                        points_by_date[day] = dict(previous_points[day])
                    prior_point = points_by_date[reusable_dates[-1]]
                    poor_streak = int(prior_point.get("_poor_streak") or 0)
                else:
                    points_by_date.clear()
                    start_index = 0
                    poor_streak = 0

        for day in ordered_dates[start_index:]:
            point = _derive_hrv_point_for_day(
                day=day,
                samples_by_date=samples_by_date,
                birthdate=birthdate,
                sex=sex,
                previous_poor_streak=poor_streak,
            )
            poor_streak = int(point.get("_poor_streak") or 0)
            points_by_date[day] = point

        return points_by_date, start_index

    def _apply_rollover(
        self, source: str, data: dict[str, Any], *, no_rollover_keys: set[str]
    ) -> dict[str, Any]:
        """Keep last non-null values for fields that should roll over day-to-day."""
        if not data:
            return data

        cache = self._rollover_cache.setdefault(source, {})
        merged: dict[str, Any] = {}

        for key, value in data.items():
            if value is None:
                if key in no_rollover_keys:
                    merged[key] = None
                else:
                    merged[key] = cache.get(key)
                continue

            merged[key] = value
            if _is_cacheable_value(value):
                cache[key] = value

        return merged


def _select_latest_summary(
    rows: list[dict[str, Any]], athlete_id: str
) -> dict[str, Any]:
    """Pick the newest summary row, preferring rows matching the authenticated athlete."""
    if not rows:
        return {}

    own_rows = [row for row in rows if str(row.get("athlete_id", "")) == athlete_id]
    candidates = own_rows or rows
    return max(candidates, key=_summary_sort_key)


def _summary_sort_key(row: dict[str, Any]) -> tuple[str, int]:
    """Sort key for summary rows by date and time."""
    date_part = str(row.get("date") or "")
    time_part = int(row.get("time") or 0)
    return (date_part, time_part)


def _select_latest_wellness_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Select latest wellness row from a list."""
    if not rows:
        return {}
    return max(rows, key=_wellness_sort_key)


def _activity_window_bounds(local_day: str) -> tuple[str, str]:
    """Build start/end timestamps for one local day."""
    return (f"{local_day}T00:00:00", f"{local_day}T23:59:59")


def _aggregate_daily_activity_calories(
    rows: list[dict[str, Any]], calculation_date: str
) -> dict[str, Any]:
    """Aggregate calories from unique activities for one local day."""
    unique_rows: dict[str, dict[str, Any]] = {}

    for row in rows:
        activity_id = str(row.get("id") or "").strip()
        if not activity_id:
            continue

        start_date_local = row.get("start_date_local")
        if (
            isinstance(start_date_local, str)
            and len(start_date_local) >= 10
            and start_date_local[:10] != calculation_date
        ):
            continue

        existing = unique_rows.get(activity_id)
        if existing is None:
            unique_rows[activity_id] = row
            continue

        existing_calories = _coerce_non_negative_int(existing.get("calories"))
        current_calories = _coerce_non_negative_int(row.get("calories"))
        if existing_calories is None and current_calories is not None:
            unique_rows[activity_id] = row

    total_calories = 0
    activity_count_total = 0
    activity_count_with_calories = 0
    activity_count_missing_calories = 0

    for row in unique_rows.values():
        activity_count_total += 1
        calories = _coerce_non_negative_int(row.get("calories"))
        if calories is None:
            activity_count_missing_calories += 1
            continue

        activity_count_with_calories += 1
        total_calories += calories

    source_status = "partial" if activity_count_missing_calories > 0 else "ok"
    return {
        "calories": total_calories,
        "calculation_date": calculation_date,
        "source_status": source_status,
        "activity_count_total": activity_count_total,
        "activity_count_with_calories": activity_count_with_calories,
        "activity_count_missing_calories": activity_count_missing_calories,
        "error": None,
    }


def _activity_daily_error_payload(calculation_date: str, error: str) -> dict[str, Any]:
    """Return payload for day-level activity metrics when fetch fails."""
    return {
        "calories": None,
        "calculation_date": calculation_date,
        "source_status": "error",
        "activity_count_total": 0,
        "activity_count_with_calories": 0,
        "activity_count_missing_calories": 0,
        "error": error,
    }


def _normalize_wellness_hrv_samples(rows: list[dict[str, Any]]) -> dict[date, float]:
    """Normalize wellness rows to one HRV value per day using latest updated row."""
    latest_rows_by_day: dict[date, tuple[str, int, dict[str, Any]]] = {}

    for idx, row in enumerate(rows):
        day = _parse_iso_date(row.get("id"))
        if day is None:
            continue

        updated = str(row.get("updated") or "")
        existing = latest_rows_by_day.get(day)
        if existing is None or (updated, idx) >= (existing[0], existing[1]):
            latest_rows_by_day[day] = (updated, idx, row)

    samples_by_date: dict[date, float] = {}
    for day, (_, _, row) in latest_rows_by_day.items():
        hrv_value = _coerce_positive_float(row.get("hrv"))
        if hrv_value is None:
            continue
        samples_by_date[day] = hrv_value

    return samples_by_date


def _derive_hrv_point_for_day(
    *,
    day: date,
    samples_by_date: dict[date, float],
    birthdate: date | None,
    sex: str,
    previous_poor_streak: int,
) -> dict[str, Any]:
    """Derive one day of Garmin-like HRV status output."""
    values_7d = _window_values(samples_by_date, day, HRV_STATUS_WINDOW_DAYS)
    values_baseline = _window_values(
        samples_by_date,
        day,
        HRV_BASELINE_WINDOW_DAYS,
        lag_days=HRV_BASELINE_LAG_DAYS,
    )

    sample_count_7d = len(values_7d)
    sample_count_baseline = len(values_baseline)

    # Allow early bootstrap if lagged window does not yet have enough samples.
    if sample_count_baseline < HRV_BASELINE_MIN_SAMPLES:
        values_baseline = _window_values(samples_by_date, day, HRV_BASELINE_WINDOW_DAYS)
        sample_count_baseline = len(values_baseline)

    if sample_count_7d < HRV_STATUS_MIN_SAMPLES or sample_count_baseline < HRV_BASELINE_MIN_SAMPLES:
        return {
            "value": None,
            "baseline_mean": None,
            "baseline_sd": None,
            "baseline_low": None,
            "baseline_high": None,
            "low_cutoff": None,
            "age_norm_lower_bound": None,
            "level": _HRV_LEVEL_NO_STATUS,
            "source_status": _HRV_SOURCE_STATUS_INSUFFICIENT,
            "sample_count_7d": sample_count_7d,
            "sample_count_baseline": sample_count_baseline,
            "_poor_candidate": False,
            "_poor_streak": 0,
        }

    status_value = mean(values_7d)
    baseline_mean = mean(values_baseline)
    baseline_sd = stdev(values_baseline) if len(values_baseline) > 1 else 0.0
    baseline_low = _percentile(values_baseline, HRV_BASELINE_LOWER_PERCENTILE)
    baseline_high = _percentile(values_baseline, HRV_BASELINE_UPPER_PERCENTILE)

    if baseline_low is None or baseline_high is None:
        return {
            "value": None,
            "baseline_mean": None,
            "baseline_sd": None,
            "baseline_low": None,
            "baseline_high": None,
            "low_cutoff": None,
            "age_norm_lower_bound": None,
            "level": _HRV_LEVEL_NO_STATUS,
            "source_status": _HRV_SOURCE_STATUS_INSUFFICIENT,
            "sample_count_7d": sample_count_7d,
            "sample_count_baseline": sample_count_baseline,
            "_poor_candidate": False,
            "_poor_streak": 0,
        }

    if baseline_high < baseline_low:
        baseline_high = baseline_low

    baseline_range = max(0.0, baseline_high - baseline_low)
    low_delta = max(
        HRV_LOW_CUTOFF_MIN_DELTA_MS,
        baseline_range * HRV_LOW_CUTOFF_RANGE_FACTOR,
    )
    low_cutoff = baseline_low - low_delta

    age_norm_lower_bound = _age_norm_lower_bound(day=day, birthdate=birthdate, sex=sex)
    poor_candidate = (
        age_norm_lower_bound is not None
        and status_value < age_norm_lower_bound
        and baseline_mean < age_norm_lower_bound
    )

    poor_streak = previous_poor_streak + 1 if poor_candidate else 0

    if poor_streak >= HRV_POOR_PERSISTENCE_DAYS:
        level = _HRV_LEVEL_POOR
    elif status_value < low_cutoff:
        level = _HRV_LEVEL_LOW
    elif baseline_low <= status_value <= baseline_high:
        level = _HRV_LEVEL_BALANCED
    else:
        level = _HRV_LEVEL_UNBALANCED

    return {
        "value": status_value,
        "baseline_mean": baseline_mean,
        "baseline_sd": baseline_sd,
        "baseline_low": baseline_low,
        "baseline_high": baseline_high,
        "low_cutoff": low_cutoff,
        "age_norm_lower_bound": age_norm_lower_bound,
        "level": level,
        "source_status": _HRV_SOURCE_STATUS_OK,
        "sample_count_7d": sample_count_7d,
        "sample_count_baseline": sample_count_baseline,
        "_poor_candidate": poor_candidate,
        "_poor_streak": poor_streak,
    }


def _window_values(
    samples_by_date: dict[date, float],
    end_day: date,
    window_days: int,
    *,
    lag_days: int = 0,
) -> list[float]:
    """Collect sample values in a trailing calendar-day window."""
    effective_end_day = end_day - timedelta(days=lag_days)
    start_day = effective_end_day - timedelta(days=window_days - 1)
    return [
        value
        for sample_day, value in samples_by_date.items()
        if start_day <= sample_day <= effective_end_day
    ]


def _percentile(values: list[float], percentile: float) -> float | None:
    """Return percentile via linear interpolation (inclusive endpoints)."""
    if not values:
        return None

    ordered = sorted(values)
    if percentile <= 0:
        return ordered[0]
    if percentile >= 100:
        return ordered[-1]

    index = (len(ordered) - 1) * (percentile / 100.0)
    low_index = math.floor(index)
    high_index = math.ceil(index)
    if low_index == high_index:
        return ordered[low_index]

    fraction = index - low_index
    return ordered[low_index] + (ordered[high_index] - ordered[low_index]) * fraction


def _build_hrv_status_payload(
    *,
    latest_date: date,
    latest_point: dict[str, Any],
    overnight_hrv: float | None,
    source_error: str | None,
    cache_hit: bool,
    birthdate_source: str,
    sex: str,
    recompute_mode: str,
    points_total: int,
) -> dict[str, Any]:
    """Build coordinator payload for current HRV status sensors."""
    level = str(latest_point.get("level") or _HRV_LEVEL_NO_STATUS)
    baseline_low = latest_point.get("baseline_low")
    baseline_high = latest_point.get("baseline_high")
    low_cutoff = latest_point.get("low_cutoff")

    baseline_suppressed = False
    if _HRV_BASELINE_SUPPRESS_WHEN_POOR and level == _HRV_LEVEL_POOR:
        baseline_low = None
        baseline_high = None
        low_cutoff = None
        baseline_suppressed = True

    source_status = str(latest_point.get("source_status") or _HRV_SOURCE_STATUS_INSUFFICIENT)
    if source_status == _HRV_SOURCE_STATUS_INSUFFICIENT and source_error:
        source_status = _HRV_SOURCE_STATUS_ERROR

    return {
        "value": latest_point.get("value"),
        "hrv_7d_avg": latest_point.get("value"),
        "overnight_hrv": overnight_hrv,
        "level": level,
        "baseline_low": baseline_low,
        "baseline_high": baseline_high,
        "low_cutoff": low_cutoff,
        "calculation_date": latest_date.isoformat(),
        "source_status": source_status,
        "sample_count_7d": int(latest_point.get("sample_count_7d") or 0),
        "sample_count_baseline": int(latest_point.get("sample_count_baseline") or 0),
        # Keep legacy key for backward-compatible attribute consumers.
        "sample_count_21d": int(latest_point.get("sample_count_baseline") or 0),
        "age_norm_lower_bound": latest_point.get("age_norm_lower_bound"),
        "cache_hit": cache_hit,
        "status_window_days": HRV_STATUS_WINDOW_DAYS,
        "baseline_window_days": HRV_BASELINE_WINDOW_DAYS,
        "baseline_lag_days": HRV_BASELINE_LAG_DAYS,
        "baseline_lower_percentile": HRV_BASELINE_LOWER_PERCENTILE,
        "baseline_upper_percentile": HRV_BASELINE_UPPER_PERCENTILE,
        "poor_persistence_days": HRV_POOR_PERSISTENCE_DAYS,
        "baseline_suppressed": baseline_suppressed,
        "birthdate_source": birthdate_source,
        "sex": sex,
        "recompute_mode": recompute_mode,
        "points_total": points_total,
        "error": source_error,
    }


def _build_hrv_history_28d(
    *,
    ordered_dates: list[date],
    samples_by_date: dict[date, float],
    points_by_date: dict[date, dict[str, Any]],
) -> dict[str, Any]:
    """Build compact 28-day chart history for frontend rendering.

    Structure is intentionally short-keyed to reduce attribute payload size.
    """
    recent_dates = ordered_dates[-HRV_STATUS_HISTORY_DAYS:]

    history_dates: list[str] = []
    overnight_values: list[float | None] = []
    status_values: list[float | None] = []
    baseline_lows: list[float | None] = []
    baseline_highs: list[float | None] = []
    level_codes: list[str] = []

    for day in recent_dates:
        point = points_by_date.get(day, {})
        level = str(point.get("level") or _HRV_LEVEL_NO_STATUS)
        history_dates.append(day.isoformat())
        overnight_values.append(_round_history_value(samples_by_date.get(day)))
        status_values.append(_round_history_value(point.get("value")))
        baseline_lows.append(_round_history_value(point.get("baseline_low")))
        baseline_highs.append(_round_history_value(point.get("baseline_high")))
        level_codes.append(_HRV_LEVEL_COMPACT_CODES.get(level, "n"))

    return {
        "v": 1,
        "d": history_dates,
        "o": overnight_values,
        "s": status_values,
        "bl": baseline_lows,
        "bh": baseline_highs,
        "lv": level_codes,
    }


def _round_history_value(value: Any) -> float | None:
    """Return compact float representation for chart history attributes."""
    if value is None or isinstance(value, bool):
        return None

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    return round(numeric, 2)


def _hrv_status_empty_payload(*, source_error: str | None) -> dict[str, Any]:
    """Return default payload when no HRV samples are available."""
    return {
        "value": None,
        "hrv_7d_avg": None,
        "overnight_hrv": None,
        "level": _HRV_LEVEL_NO_STATUS,
        "baseline_low": None,
        "baseline_high": None,
        "low_cutoff": None,
        "calculation_date": None,
        "source_status": _HRV_SOURCE_STATUS_ERROR if source_error else _HRV_SOURCE_STATUS_INSUFFICIENT,
        "sample_count_7d": 0,
        "sample_count_baseline": 0,
        "sample_count_21d": 0,
        "age_norm_lower_bound": None,
        "cache_hit": False,
        "status_window_days": HRV_STATUS_WINDOW_DAYS,
        "baseline_window_days": HRV_BASELINE_WINDOW_DAYS,
        "baseline_lag_days": HRV_BASELINE_LAG_DAYS,
        "baseline_lower_percentile": HRV_BASELINE_LOWER_PERCENTILE,
        "baseline_upper_percentile": HRV_BASELINE_UPPER_PERCENTILE,
        "poor_persistence_days": HRV_POOR_PERSISTENCE_DAYS,
        "baseline_suppressed": False,
        "birthdate_source": "unavailable",
        "sex": "unknown",
        "recompute_mode": "full",
        "points_total": 0,
        "history_28d": {
            "v": 1,
            "d": [],
            "o": [],
            "s": [],
            "bl": [],
            "bh": [],
            "lv": [],
        },
        "error": source_error,
    }


def _deserialize_cached_samples(raw: Any) -> dict[date, float]:
    """Deserialize cached date->float sample map."""
    if not isinstance(raw, dict):
        return {}

    samples: dict[date, float] = {}
    for day_raw, value_raw in raw.items():
        day = _parse_iso_date(day_raw)
        value = _coerce_positive_float(value_raw)
        if day is None or value is None:
            continue
        samples[day] = value
    return samples


def _deserialize_cached_points(raw: Any) -> dict[date, dict[str, Any]]:
    """Deserialize cached point map keyed by ISO day strings."""
    if not isinstance(raw, dict):
        return {}

    points: dict[date, dict[str, Any]] = {}
    for day_raw, point_raw in raw.items():
        day = _parse_iso_date(day_raw)
        if day is None or not isinstance(point_raw, dict):
            continue
        points[day] = point_raw
    return points


def _earliest_changed_date(
    previous: dict[date, float],
    current: dict[date, float],
) -> date | None:
    """Return earliest date where normalized HRV samples changed."""
    all_dates = sorted(set(previous) | set(current))
    for day in all_dates:
        if previous.get(day) != current.get(day):
            return day
    return None


def _first_index_on_or_after(days: list[date], target: date) -> int:
    """Return index of first day >= target in an ordered day list."""
    for idx, day in enumerate(days):
        if day >= target:
            return idx
    return len(days)


def _hrv_sample_fingerprint(samples_by_date: dict[date, float]) -> str:
    """Build stable fingerprint from normalized date->HRV values."""
    joined = "|".join(
        f"{day.isoformat()}:{samples_by_date[day]:.3f}" for day in sorted(samples_by_date)
    )
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _resolve_birthdate(
    *,
    athlete: dict[str, Any],
    birthdate_override: date | None,
) -> tuple[date | None, str]:
    """Resolve birthdate source precedence: option override, then athlete profile."""
    if birthdate_override is not None:
        return birthdate_override, "option"

    for key in ("icu_date_of_birth", "date_of_birth", "birthdate"):
        parsed = _parse_iso_date(athlete.get(key))
        if parsed is not None:
            return parsed, "api"

    return None, "unavailable"


def _normalize_sex(value: Any) -> str:
    """Normalize athlete sex to female/male/unknown."""
    if not isinstance(value, str):
        return "unknown"

    cleaned = value.strip().lower()
    if cleaned.startswith("f"):
        return "female"
    if cleaned.startswith("m"):
        return "male"
    return "unknown"


def _age_norm_lower_bound(*, day: date, birthdate: date | None, sex: str) -> float | None:
    """Return age/sex lower bound for poor-status detection."""
    if birthdate is None:
        return None

    age = _age_on_day(birthdate, day)
    if age is None:
        return None

    bands = _AGE_NORM_LOWER_BOUNDS_BY_SEX.get(sex, _AGE_NORM_LOWER_BOUNDS_BY_SEX["unknown"])
    for min_age, max_age, lower_bound in bands:
        if min_age <= age <= max_age:
            return lower_bound

    return bands[-1][2]


def _age_on_day(birthdate: date, target_day: date) -> int | None:
    """Return age in full years at target day."""
    if target_day < birthdate:
        return None

    age = target_day.year - birthdate.year
    if (target_day.month, target_day.day) < (birthdate.month, birthdate.day):
        age -= 1
    return age


def _parse_iso_date(value: Any) -> date | None:
    """Parse YYYY-MM-DD-like value to date."""
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    candidate = cleaned[:10]
    try:
        return date.fromisoformat(candidate)
    except ValueError:
        return None


def _wellness_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    """Sort key for wellness records by id date and updated timestamp."""
    return (str(row.get("id") or ""), str(row.get("updated") or ""))


def _flatten_wellness_sport_info(wellness: dict[str, Any]) -> dict[str, Any]:
    """Flatten sportInfo wellness array into scalar metrics for sensors."""
    sport_info = wellness.get("sportInfo")
    if not isinstance(sport_info, list):
        return {}

    flattened: dict[str, Any] = {}
    for entry in sport_info:
        if not isinstance(entry, dict):
            continue

        sport_type = entry.get("type")
        if not isinstance(sport_type, str) or not sport_type:
            continue
        sport_slug = _slugify(sport_type)

        for key, value in entry.items():
            if key == "type":
                continue
            if value is None or isinstance(value, bool) or isinstance(value, (list, dict)):
                continue

            metric_slug = _camel_to_snake(key)
            flattened[f"{sport_slug}__{metric_slug}"] = value

    return flattened


def _slugify(value: str) -> str:
    """Convert display text to a simple snake_case key."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _camel_to_snake(value: str) -> str:
    """Convert camelCase or mixedCase names to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def _is_cacheable_value(value: Any) -> bool:
    """Return True when value can be safely cached and reused on null updates."""
    return isinstance(value, (str, int, float, bool, date, Decimal))


def _coerce_positive_float(value: Any) -> float | None:
    """Return positive float for numeric values, otherwise None."""
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        parsed = float(value)
        if not math.isfinite(parsed) or parsed <= 0:
            return None
        return parsed

    if isinstance(value, Decimal):
        if not value.is_finite() or value <= 0:
            return None
        return float(value)

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            parsed = float(cleaned)
        except ValueError:
            return None
        if not math.isfinite(parsed) or parsed <= 0:
            return None
        return parsed

    return None


def _coerce_non_negative_int(value: Any) -> int | None:
    """Return non-negative integer for numeric values, otherwise None."""
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value if value >= 0 else None

    if isinstance(value, float):
        if not math.isfinite(value) or value < 0:
            return None
        return int(value)

    if isinstance(value, Decimal):
        if not value.is_finite() or value < 0:
            return None
        return int(value)

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            parsed = float(cleaned)
        except ValueError:
            return None
        if not math.isfinite(parsed) or parsed < 0:
            return None
        return int(parsed)

    return None
