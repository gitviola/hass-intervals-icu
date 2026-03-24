"""Data coordinator for Intervals.icu."""

from __future__ import annotations

import logging
from datetime import date, timedelta
import re
from decimal import Decimal
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    IntervalsIcuApiClient,
    IntervalsIcuApiError,
    IntervalsIcuAuthError,
    IntervalsIcuConnectionError,
)
from .const import (
    CONF_ATHLETE_ID,
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

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
        self._rollover_cache: dict[str, dict[str, Any]] = {
            "summary": {},
            "wellness": {},
            "wellness_sport_metrics": {},
        }

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
            wellness = await self._async_fetch_latest_wellness(summary)
        except IntervalsIcuAuthError as err:
            raise ConfigEntryAuthFailed from err
        except IntervalsIcuConnectionError as err:
            raise UpdateFailed(str(err)) from err
        wellness = self._apply_rollover(
            "wellness", wellness, no_rollover_keys=_WELLNESS_NO_ROLLOVER_KEYS
        )
        wellness_sport_metrics = self._apply_rollover(
            "wellness_sport_metrics",
            _flatten_wellness_sport_info(wellness),
            no_rollover_keys=set(),
        )

        return {
            "athlete": athlete,
            "summary": summary,
            "wellness": wellness,
            "wellness_sport_metrics": wellness_sport_metrics,
        }

    async def _async_fetch_latest_wellness(
        self, summary: dict[str, Any]
    ) -> dict[str, Any]:
        """Fetch the latest wellness record if available."""
        recent_id = summary.get("mostRecentWellnessId")
        if isinstance(recent_id, str) and recent_id:
            try:
                return await self.api.get_wellness_record(self.athlete_id, recent_id)
            except (IntervalsIcuAuthError, IntervalsIcuConnectionError):
                raise
            except IntervalsIcuApiError as err:
                _LOGGER.debug(
                    "Failed loading wellness record %s for athlete %s: %s",
                    recent_id,
                    self.athlete_id,
                    err,
                )

        try:
            newest = date.today().isoformat()
            oldest = (date.today() - timedelta(days=45)).isoformat()
            records = await self.api.list_wellness_records(
                self.athlete_id, oldest=oldest, newest=newest
            )
        except (IntervalsIcuAuthError, IntervalsIcuConnectionError):
            raise
        except IntervalsIcuApiError as err:
            _LOGGER.debug(
                "Failed loading wellness list for athlete %s: %s",
                self.athlete_id,
                err,
            )
            return {}

        if not records:
            return {}
        return max(records, key=_wellness_sort_key)

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
