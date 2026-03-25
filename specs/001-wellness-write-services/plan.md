# Implementation Plan: Wellness Data Write Support

**Branch**: `001-wellness-write-services` | **Date**: 2026-03-25 | **Spec**: [/Users/ms/Projects/private/hass-intervals-icu/specs/001-wellness-write-services/spec.md](/Users/ms/Projects/private/hass-intervals-icu/specs/001-wellness-write-services/spec.md)
**Input**: Feature specification from `/specs/001-wellness-write-services/spec.md`

## Summary

Add Home Assistant write actions for Intervals.icu wellness fields (weight and nutrition). Default target date to current Home Assistant local date when date is omitted. Enforce strict partial-update semantics by sending only provided writable fields to Intervals.icu so omitted fields remain unchanged. Trigger coordinator refresh after successful writes.

## Technical Context

**Language/Version**: Python 3.13+ (Home Assistant custom integration runtime)  
**Primary Dependencies**: Home Assistant core helpers/config entries/services, aiohttp client  
**Storage**: N/A (remote API + in-memory coordinator cache)  
**Testing**: `python3 -m compileall custom_components/intervals_icu` and manual HA service-call validation  
**Target Platform**: Home Assistant Core (custom integration)  
**Project Type**: Home Assistant custom integration (single project)  
**Performance Goals**: Service call completion within normal API roundtrip (<5s typical)  
**Constraints**: No secret leakage in logs/errors; maintain existing entity behavior and backward compatibility  
**Scale/Scope**: Per-config-entry athlete wellness updates; support frequent automation-triggered writes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] HA UX and entity stability: config entry/options flow unaffected; existing entity `unique_id`s unchanged.
- [x] Coordinator-first design: all reads remain coordinator-driven; write path is explicit action call, not entity I/O.
- [x] Metric semantics and freshness: writable field mapping, default date semantics, and partial update behavior are explicitly defined.
- [x] Security and diagnostics: API key remains in config entry only; service logging avoids secrets.
- [x] Release impact declared: backward-compatible feature (`MINOR` release), changelog/release notes required.

## Project Structure

### Documentation (this feature)

```text
specs/001-wellness-write-services/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── wellness-write-services.md
└── tasks.md
```

### Source Code (repository root)

```text
custom_components/intervals_icu/
├── __init__.py
├── api.py
├── const.py
├── coordinator.py
├── sensor.py
├── services.yaml            # new
├── strings.json             # update if service metadata text is added
└── translations/
    └── en.json              # update if service metadata text is added

README.md                    # optional service usage examples
```

**Structure Decision**: Extend existing single integration module by adding service registration in `__init__.py`, API write method(s) in `api.py`, and service schema/metadata in `services.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
