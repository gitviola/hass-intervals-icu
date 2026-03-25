# Implementation Plan: Garmin-Like HRV Status and Baseline Ranges

**Branch**: `003-garmin-hrv-status` | **Date**: 2026-03-25 | **Spec**: [/Users/ms/Projects/private/hass-intervals-icu/specs/003-garmin-hrv-status/spec.md](/Users/ms/Projects/private/hass-intervals-icu/specs/003-garmin-hrv-status/spec.md)
**Input**: Feature specification from `/specs/003-garmin-hrv-status/spec.md`

## Summary

Add Garmin-like HRV derived metrics on top of existing overnight wellness HRV: a numeric
seven-day `HRV Status` trend value, a Garmin-style humanized `HRV Status (Level)` label,
and dynamic baseline range boundaries suitable for charting. The design will bootstrap from
historical wellness HRV when first enabled, then use incremental/cached recalculation when
source HRV data is unchanged or only partially changed.

## Technical Context

**Language/Version**: Python 3.13+ (Home Assistant custom integration runtime)  
**Primary Dependencies**: Home Assistant coordinator/entity helpers, aiohttp client, Intervals.icu REST API, Python `statistics` module  
**Storage**: N/A (remote API + in-memory coordinator cache; recorder-backed entity history in Home Assistant)  
**Testing**: `python3 -m compileall custom_components/intervals_icu` and manual Home Assistant sensor/attribute validation  
**Target Platform**: Home Assistant Core (custom integration)  
**Project Type**: Home Assistant custom integration (single project)  
**Performance Goals**: Maintain normal polling responsiveness; avoid repeated full-history recomputation when HRV input unchanged  
**Constraints**: Preserve existing entity semantics/IDs; keep entity property reads I/O-free; no secret leakage; bounded history retrieval for bootstrap/recompute  
**Scale/Scope**: Single configured athlete per config entry (`athlete_id`, including `0` for current user), with daily HRV derivation from recent weeks-to-months of wellness records

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Post-design re-check result: PASS.

- [x] HA UX and entity stability: additive entities only; existing `wellness_hrv` behavior unchanged; stable `unique_id` strategy retained.
- [x] Coordinator-first design: all API reads and HRV derivation run in coordinator update path; entities remain memory-only reads.
- [x] Metric semantics and freshness: explicit source (`wellness.hrv`), seven-day trend semantics, baseline freshness rules, and null/insufficient-data behavior defined.
- [x] Security and diagnostics: no credential changes; logs and diagnostics remain secret-safe.
- [x] Release impact declared: backward-compatible feature (`MINOR`) with changelog/release-note updates required.

## Project Structure

### Documentation (this feature)

```text
specs/003-garmin-hrv-status/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── hrv-status-and-baseline.md
└── tasks.md
```

### Source Code (repository root)

```text
custom_components/intervals_icu/
├── api.py                # ensure wellness history fetch supports efficient range/fields usage
├── coordinator.py        # compute/cached HRV status + baseline derivations
├── sensor.py             # expose numeric and humanized HRV status + baseline sensors
├── const.py              # optional constants/keys for derived HRV sources
└── __init__.py           # unchanged setup flow unless registration wiring is needed

docs/
└── API_METRICS.md        # update metric inventory and semantics

README.md                 # optional usage/interpretation notes for new HRV sensors
```

**Structure Decision**: Extend the existing integration module in-place. Derived HRV logic
will live in coordinator-sourced data slices, with sensor exposure in `sensor.py` and no
new external service endpoints required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
