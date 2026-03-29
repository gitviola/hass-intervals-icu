# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.2] - 2026-03-29

### Changed

- Retuned Garmin-like HRV baseline derivation to better match gap-heavy Garmin
  exports:
  - Normal mode keeps a lagged 28-day baseline window with percentile bounds
    tuned to `32/97`.
  - Seasoned-history mode now promotes mature accounts to a lagged 56-day
    baseline window with percentile bounds `32/95`.
  - Gap recovery expands the lagged lookback up to 66 days and narrows
    percentile bounds to `33/95` when recent history is sparse.
  - Baseline bounds can now remain available even when a fresh 7-day HRV status
    value is still unavailable after a data gap.

### Added

- Added baseline derivation metadata attributes for HRV status entities and a
  maintainer replay tool to compare calculated Garmin-like HRV baselines against
  exported Garmin history day by day.

## [0.8.1] - 2026-03-25

### Changed

- HRV status attributes now expose both raw and unit-suffixed tile-card fields
  (`overnight_hrv` + `overnight_hrv_with_unit`,
  `hrv_7d_avg` + `hrv_7d_avg_with_unit`) and round HRV attribute values to
  whole milliseconds.

## [0.8.0] - 2026-03-25

### Added

- Added HRV status attributes for tile-card customization:
  `overnight_hrv`, `hrv_7d_avg`, and shared `hrv_unit` (`ms`).

## [0.7.3] - 2026-03-25

### Changed

- Renamed development compose file from `docker-compose.yml` to `compose.yml`.

### Added

- Added compact `history_28d` attribute on `HRV Status (7-Day Avg)` for
  chart-ready bootstrap data (dates, overnight HRV, 7-day status, baseline
  lower/upper, and compact level codes).

## [0.7.2] - 2026-03-25

### Changed

- Retuned Garmin-like HRV baseline derivation using expanded Jan-Mar fixture
  coverage:
  - Baseline window `56d -> 28d`
  - Baseline lag `4d -> 6d`
  - Baseline percentiles `40/95 -> 30/97`
  - Baseline minimum samples `18 -> 12` for earlier 2-4 week bootstrapping
    when history is limited.

### Added

- Added combined Garmin export fixture `garmin_hrv_status_q1_2026.csv` and a
  regression test asserting bounded baseline error across the full Q1 window.

## [0.7.1] - 2026-03-25

### Changed

- Reworked Garmin-like HRV baseline derivation to a lagged long-window model:
  56-day overnight history, 4-day lag, percentile bounds (40th/95th), and an
  explicit low-threshold offset from baseline width.
- Renamed HRV entities for clarity of source semantics:
  - `HRV` -> `Overnight HRV`
  - `HRV Status` -> `HRV Status (7-Day Avg)`
  - `HRV Low Threshold` -> `HRV Low Threshold (7-Day Avg)`
- Expanded HRV status attributes with baseline derivation metadata
  (`sample_count_baseline`, baseline lag/percentiles) while keeping legacy
  `sample_count_21d` for compatibility.

### Added

- Added fixture-driven regression coverage to validate Garmin CSV-like baseline
  range behavior and guard against baseline drift regressions.

## [0.7.0] - 2026-03-25

### Added

- Added Garmin-like HRV derived sensors:
  - `HRV Status`
  - `HRV Status (Level)`
  - `HRV Baseline Lower`
  - `HRV Baseline Upper`
  - `HRV Low Threshold`
- Added coordinator-side HRV derivation cache and change detection so unchanged
  wellness HRV inputs reuse previous derived outputs.
- Added optional integration option `Birthdate override (YYYY-MM-DD)` used for
  age-context HRV `Poor` classification when profile birthdate data is missing.
- Added fixture-based unit tests for HRV derivation logic in
  `tests/test_hrv_status_logic.py`.

### Changed

- Wellness history reads now include a bounded rolling window used to bootstrap
  and maintain HRV status/baseline calculations for the configured athlete ID.
- Updated docs (`README.md`, `docs/API_METRICS.md`) with HRV status semantics,
  age-context behavior, and chart-ready range outputs.

## [0.6.0] - 2026-03-25

### Added

- Expanded `intervals_icu.set_wellness` writable fields to cover a broad set of
  Intervals wellness metrics (body, recovery, sleep, vitals, nutrition, and
  notes/flags).

### Changed

- Documented and exposed templated-value usage for wellness service calls in
  Home Assistant YAML mode.

## [0.5.0] - 2026-03-25

### Added

- Added `Activity Calories Burned (Daily)` sensor that sums same-day activity
  calories from Intervals activity rows.

### Changed

- Published a mainline release that includes both merged feature sets:
  `intervals_icu.set_wellness` write support and daily activity calories.

## [0.4.0] - 2026-03-25

### Added

- Added `intervals_icu.set_wellness` service to update selected Intervals.icu
  wellness values (`weight`, `kcal_consumed`, `carbohydrates`, `protein`,
  `fat_total`, `hydration_volume`) with optional explicit `date`.
- Added Home Assistant service metadata in `services.yaml` and localized service
  labels/descriptions.

### Changed

- Default wellness write date now resolves to Home Assistant local date when the
  `date` field is omitted or blank.
- Wellness write validation now enforces non-negative numeric inputs and
  returns clearer actionable service errors.

## [0.3.1] - 2026-03-24

### Fixed

- Fixed a Home Assistant options/configure flow crash on some HA versions
  (`Config flow could not be loaded: 500 Internal Server Error`) by making
  options flow construction compatible across HA constructor variants.

## [0.3.0] - 2026-03-24

### Added

- Added a humanized sleep duration sensor formatted as `Xh Ym`.
- Added default `suggested_display_precision` hints for numeric sensors.

### Changed

- Set metric-specific display precision defaults (for example integer display
  for HRV/CTL/ATL/Fatigue/Form/Fitness/watts and 1 decimal for ramp rate).

## [0.2.0] - 2026-03-24

### Added

- Added humanized wellness scale sensors (Sleep Quality, Fatigue, Stress,
  Soreness, Mood, Motivation, Injury, Hydration level mappings).

### Changed

- Standardized naming conventions for humanized sensors.
- Improved icon mapping for wellness and dynamic `sportInfo` sensors.
- Updated integration branding to the official Intervals.icu logo.

### Fixed

- Removed unsupported `SensorDeviceClass.HEART_RATE` usage for HA compatibility.
- Fixed HACS/hassfest metadata and manifest validation issues.

## [0.1.0] - 2026-03-24

### Added

- Initial publish-ready custom integration scaffold for Intervals.icu.
- Config flow + options flow, DataUpdateCoordinator polling, API client,
  summary/wellness sensors, HACS metadata, docs, CI validation setup.

### Documentation

- Added AGENTS release workflow guidance for ongoing maintenance.

[Unreleased]: https://github.com/gitviola/hass-intervals-icu/compare/v0.8.2...HEAD
[0.8.2]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.8.2
[0.8.1]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.8.1
[0.8.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.8.0
[0.7.3]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.7.3
[0.7.2]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.7.2
[0.7.1]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.7.1
[0.7.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.7.0
[0.6.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.6.0
[0.5.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.5.0
[0.4.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.4.0
[0.3.1]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.3.1
[0.3.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.3.0
[0.2.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.2.0
[0.1.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.1.0
