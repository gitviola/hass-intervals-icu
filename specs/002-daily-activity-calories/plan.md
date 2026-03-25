# Implementation Plan: Daily Activity Calories Sensor

**Branch**: `002-daily-activity-calories` | **Date**: 2026-03-25 | **Spec**: [/Users/ms/Projects/private/hass-intervals-icu/specs/002-daily-activity-calories/spec.md](/Users/ms/Projects/private/hass-intervals-icu/specs/002-daily-activity-calories/spec.md)
**Input**: Feature specification from `/specs/002-daily-activity-calories/spec.md`

## Summary

Introduce a new day-level "activity calories burned" metric that sums calories from
same-day activities while keeping existing summary calories unchanged. Compute the
daily metric during coordinator refresh, expose it as a separate sensor, and define
clear semantics for date anchoring, missing calorie fields, no-activity days, and
error handling.

## Technical Context

**Language/Version**: Python 3.13+ (Home Assistant custom integration runtime)  
**Primary Dependencies**: Home Assistant coordinator/entity helpers, aiohttp client, Intervals.icu REST API  
**Storage**: N/A (remote API + in-memory coordinator cache)  
**Testing**: `python3 -m compileall custom_components/intervals_icu` and manual Home Assistant sensor validation  
**Target Platform**: Home Assistant Core (custom integration)  
**Project Type**: Home Assistant custom integration (single project)  
**Performance Goals**: Keep refresh within normal polling expectations; avoid user-visible lag for normal daily activity volume  
**Constraints**: Preserve existing entity IDs/semantics, no secret leakage, keep entity property reads I/O-free  
**Scale/Scope**: Per-athlete daily activity aggregation for each configured integration entry

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Post-design re-check result: PASS.

- [x] HA UX and entity stability: existing summary calories semantics preserved; new metric added as separate entity with stable `unique_id`.
- [x] Coordinator-first design: daily activity read and aggregation occur in coordinator update path only.
- [x] Metric semantics and freshness: explicit day-level source, no-rollover behavior, and missing-value handling defined.
- [x] Security and diagnostics: no credential logging; API failures handled without exposing secrets.
- [x] Release impact declared: backward-compatible feature (`MINOR`) with changelog and release-note updates required.

## Project Structure

### Documentation (this feature)

```text
specs/002-daily-activity-calories/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── daily-activity-calories.md
└── tasks.md
```

### Source Code (repository root)

```text
custom_components/intervals_icu/
├── api.py                # add activities read helper(s) for date window
├── coordinator.py        # compute and store daily activity calories aggregate
├── sensor.py             # expose new day-level calories sensor entity
├── const.py              # optional new source keys/constants
└── translations/
    └── en.json           # update if new sensor names/descriptions require localization keys

docs/
└── API_METRICS.md        # update source/semantics inventory

README.md                 # optional mention of new sensor semantics
```

**Structure Decision**: Extend the existing integration module in-place: API client
for additional read path, coordinator for shared aggregation logic, and sensor module
for entity exposure. No new packages or services are required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
