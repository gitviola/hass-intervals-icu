# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/gitviola/hass-intervals-icu/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.4.0
[0.3.1]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.3.1
[0.3.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.3.0
[0.2.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.2.0
[0.1.0]: https://github.com/gitviola/hass-intervals-icu/releases/tag/v0.1.0
