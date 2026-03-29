#!/usr/bin/env python3
"""Replay Garmin HRV exports day by day against the current baseline model."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.test_hrv_status_logic import _load_coordinator_module  # noqa: E402


MONTH_MAP = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


@dataclass(slots=True)
class DiagnosticRow:
    day: date
    overnight_hrv: float | None
    expected_baseline_low: int | None
    expected_baseline_high: int | None
    expected_status_avg: int | None
    actual_baseline_low: int | None
    actual_baseline_high: int | None
    actual_status_avg: int | None
    baseline_low_error: int | None
    baseline_high_error: int | None
    status_error: int | None
    baseline_window_mode: str
    baseline_window_days: int | None
    baseline_lag_days: int | None
    sample_count_baseline: int
    sample_count_7d: int
    source_status: str

    @property
    def baseline_abs_error_sum(self) -> int | None:
        if self.baseline_low_error is None or self.baseline_high_error is None:
            return None
        return self.baseline_low_error + self.baseline_high_error


def _coordinator() -> tuple[Any, Any]:
    mod = _load_coordinator_module()
    const_mod = __import__("custom_components.intervals_icu.const", fromlist=["*"])
    config_entries_mod = __import__("homeassistant.config_entries", fromlist=["ConfigEntry"])
    entry = config_entries_mod.ConfigEntry(
        data={
            const_mod.CONF_ATHLETE_ID: "0",
            const_mod.CONF_SCAN_INTERVAL_MINUTES: 30,
        },
        options={},
    )
    return mod, mod.IntervalsIcuCoordinator(hass=object(), entry=entry, api=object())


def _infer_rows(paths: list[Path], start_year: int) -> tuple[list[dict[str, Any]], dict[date, dict[str, int | None]]]:
    rows: list[dict[str, Any]] = []
    expected: dict[date, dict[str, int | None]] = {}
    year = start_year
    previous_day: date | None = None

    for path in paths:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            source_rows = list(csv.DictReader(handle))

        # Garmin exports are newest -> oldest. Replay oldest -> newest.
        for raw in reversed(source_rows):
            day_raw = str(raw["Date"]).strip()
            day_number_raw, month_name = day_raw.split()
            month_number = MONTH_MAP[month_name]
            day_number = int(day_number_raw)

            if previous_day is not None and month_number < previous_day.month:
                year += 1

            current_day = date(year, month_number, day_number)
            previous_day = current_day

            overnight_raw = str(raw["Overnight HRV"]).strip()
            overnight_hrv = (
                None if overnight_raw == "--" else float(overnight_raw.replace("ms", "").strip())
            )

            baseline_raw = str(raw["Baseline"]).strip()
            baseline_low: int | None = None
            baseline_high: int | None = None
            if baseline_raw != "--":
                baseline_low_raw, baseline_high_raw = [part.strip() for part in baseline_raw.split("-")]
                baseline_low = int(round(float(baseline_low_raw.replace("ms", "").strip())))
                baseline_high = int(round(float(baseline_high_raw.replace("ms", "").strip())))

            status_avg_raw = str(raw["7d Avg"]).strip()
            status_avg = None if status_avg_raw == "--" else int(round(float(status_avg_raw.replace("ms", "").strip())))

            rows.append(
                {
                    "id": current_day.isoformat(),
                    "hrv": overnight_hrv,
                    "updated": f"{current_day.isoformat()}T06:00:00Z",
                }
            )
            expected[current_day] = {
                "baseline_low": baseline_low,
                "baseline_high": baseline_high,
                "status_avg": status_avg,
            }

    return rows, expected


def _diagnostic_rows(
    *,
    mod: Any,
    coordinator: Any,
    rows: list[dict[str, Any]],
    expected: dict[date, dict[str, int | None]],
    birthdate: date,
    sex: str,
) -> list[DiagnosticRow]:
    samples_by_date = mod._normalize_wellness_hrv_samples(rows)
    ordered_dates = sorted(samples_by_date)
    points_by_date, _ = coordinator._derive_hrv_points(
        ordered_dates=ordered_dates,
        samples_by_date=samples_by_date,
        birthdate=birthdate,
        sex=sex,
    )

    diagnostics: list[DiagnosticRow] = []
    for day in sorted(expected):
        point = points_by_date.get(day, {})
        exp = expected[day]

        actual_low_raw = point.get("baseline_low")
        actual_high_raw = point.get("baseline_high")
        actual_status_raw = point.get("value")

        actual_low = None if actual_low_raw is None else int(round(float(actual_low_raw)))
        actual_high = None if actual_high_raw is None else int(round(float(actual_high_raw)))
        actual_status = None if actual_status_raw is None else int(round(float(actual_status_raw)))

        expected_low = exp["baseline_low"]
        expected_high = exp["baseline_high"]
        expected_status = exp["status_avg"]

        diagnostics.append(
            DiagnosticRow(
                day=day,
                overnight_hrv=samples_by_date.get(day),
                expected_baseline_low=expected_low,
                expected_baseline_high=expected_high,
                expected_status_avg=expected_status,
                actual_baseline_low=actual_low,
                actual_baseline_high=actual_high,
                actual_status_avg=actual_status,
                baseline_low_error=(
                    None if expected_low is None or actual_low is None else abs(actual_low - expected_low)
                ),
                baseline_high_error=(
                    None if expected_high is None or actual_high is None else abs(actual_high - expected_high)
                ),
                status_error=(
                    None
                    if expected_status is None or actual_status is None
                    else abs(actual_status - expected_status)
                ),
                baseline_window_mode=str(point.get("baseline_window_mode") or ""),
                baseline_window_days=(
                    None
                    if point.get("baseline_window_days") is None
                    else int(point["baseline_window_days"])
                ),
                baseline_lag_days=(
                    None if point.get("baseline_lag_days") is None else int(point["baseline_lag_days"])
                ),
                sample_count_baseline=int(point.get("sample_count_baseline") or 0),
                sample_count_7d=int(point.get("sample_count_7d") or 0),
                source_status=str(point.get("source_status") or ""),
            )
        )

    return diagnostics


def _write_csv(path: Path, rows: list[DiagnosticRow]) -> None:
    fieldnames = [
        "day",
        "overnight_hrv",
        "expected_baseline_low",
        "expected_baseline_high",
        "expected_status_avg",
        "actual_baseline_low",
        "actual_baseline_high",
        "actual_status_avg",
        "baseline_low_error",
        "baseline_high_error",
        "status_error",
        "baseline_window_mode",
        "baseline_window_days",
        "baseline_lag_days",
        "sample_count_baseline",
        "sample_count_7d",
        "source_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "day": row.day.isoformat(),
                    "overnight_hrv": row.overnight_hrv,
                    "expected_baseline_low": row.expected_baseline_low,
                    "expected_baseline_high": row.expected_baseline_high,
                    "expected_status_avg": row.expected_status_avg,
                    "actual_baseline_low": row.actual_baseline_low,
                    "actual_baseline_high": row.actual_baseline_high,
                    "actual_status_avg": row.actual_status_avg,
                    "baseline_low_error": row.baseline_low_error,
                    "baseline_high_error": row.baseline_high_error,
                    "status_error": row.status_error,
                    "baseline_window_mode": row.baseline_window_mode,
                    "baseline_window_days": row.baseline_window_days,
                    "baseline_lag_days": row.baseline_lag_days,
                    "sample_count_baseline": row.sample_count_baseline,
                    "sample_count_7d": row.sample_count_7d,
                    "source_status": row.source_status,
                }
            )


def _print_summary(rows: list[DiagnosticRow], top_n: int) -> None:
    baseline_rows = [row for row in rows if row.baseline_abs_error_sum is not None]
    status_rows = [row for row in rows if row.status_error is not None]
    baseline_visible_expected = [
        row
        for row in rows
        if row.expected_baseline_low is not None and row.expected_baseline_high is not None
    ]
    baseline_visible_actual = [
        row
        for row in baseline_visible_expected
        if row.actual_baseline_low is not None and row.actual_baseline_high is not None
    ]

    baseline_mae = 0.0
    if baseline_rows:
        baseline_mae = sum(row.baseline_abs_error_sum or 0 for row in baseline_rows) / (
            2 * len(baseline_rows)
        )

    status_mae = 0.0
    if status_rows:
        status_mae = sum(row.status_error or 0 for row in status_rows) / len(status_rows)

    print("Summary")
    print(f"- Total days replayed: {len(rows)}")
    print(
        f"- Baseline days compared: {len(baseline_rows)} "
        f"(visible on {len(baseline_visible_actual)}/{len(baseline_visible_expected)} Garmin baseline days)"
    )
    print(f"- Baseline MAE: {baseline_mae:.3f} ms")
    print(f"- 7-day status MAE: {status_mae:.3f} ms")

    mode_counts: dict[str, int] = {}
    for row in rows:
        mode = row.baseline_window_mode or "none"
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
    print("- Baseline mode counts:")
    for mode, count in sorted(mode_counts.items()):
        print(f"  - {mode}: {count}")

    print("\nWorst Baseline Days")
    worst_rows = sorted(
        [row for row in baseline_rows if row.baseline_abs_error_sum is not None],
        key=lambda row: (
            row.baseline_abs_error_sum or 0,
            row.baseline_high_error or 0,
            row.baseline_low_error or 0,
        ),
        reverse=True,
    )[:top_n]
    for row in worst_rows:
        print(
            f"- {row.day.isoformat()}: "
            f"expected {row.expected_baseline_low}-{row.expected_baseline_high}, "
            f"actual {row.actual_baseline_low}-{row.actual_baseline_high}, "
            f"errors low/high {row.baseline_low_error}/{row.baseline_high_error}, "
            f"mode={row.baseline_window_mode}, "
            f"samples={row.sample_count_baseline}, 7d={row.sample_count_7d}"
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay Garmin HRV export CSVs in chronological chunk order and compare "
            "the current baseline model against Garmin's baseline column."
        )
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Garmin export CSV paths in chronological chunk order (oldest chunk first).",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2025,
        help="Calendar year for the oldest chunk's rows. Default: 2025.",
    )
    parser.add_argument(
        "--birthdate",
        default="1990-01-01",
        help="Birthdate used for coordinator derivation context. Default: 1990-01-01.",
    )
    parser.add_argument(
        "--sex",
        default="male",
        help="Sex used for coordinator derivation context. Default: male.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=15,
        help="Number of worst baseline rows to print. Default: 15.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        help="Optional path to write full day-by-day diagnostic output as CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    mod, coordinator = _coordinator()
    birthdate = date.fromisoformat(args.birthdate)
    rows, expected = _infer_rows(args.paths, start_year=args.start_year)
    diagnostics = _diagnostic_rows(
        mod=mod,
        coordinator=coordinator,
        rows=rows,
        expected=expected,
        birthdate=birthdate,
        sex=str(args.sex).lower(),
    )
    _print_summary(diagnostics, top_n=args.top)
    if args.output_csv is not None:
        _write_csv(args.output_csv, diagnostics)
        print(f"\nWrote day-by-day diagnostic CSV to {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
