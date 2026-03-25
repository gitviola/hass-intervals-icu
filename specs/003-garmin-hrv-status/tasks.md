# Tasks: Garmin-Like HRV Status and Baseline Ranges

**Input**: Design documents from `/specs/003-garmin-hrv-status/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Automated tests are not explicitly required by the feature spec and
this repository currently relies on compile checks plus manual Home Assistant
validation for feature verification.

**Organization**: Tasks are grouped by user story so each story can be
implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare HRV-status scaffolding and documentation anchors.

- [ ] T001 Add HRV status source keys/window constants in `custom_components/intervals_icu/const.py` and `custom_components/intervals_icu/coordinator.py`
- [ ] T002 Add coordinator helper skeletons for rolling-window derivation and Garmin label mapping in `custom_components/intervals_icu/coordinator.py`
- [ ] T003 [P] Add placeholder metric entries for HRV status/baseline outputs in `docs/API_METRICS.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared HRV data/derivation primitives required by all user stories.

**⚠️ CRITICAL**: No user story work should proceed until this phase is complete.

- [ ] T004 Extend API wellness-history access for bounded reads of the configured athlete (`athlete_id`, including `0`) in `custom_components/intervals_icu/api.py`
- [ ] T005 Implement wellness HRV normalization and per-date deduplication by `updated` timestamp in `custom_components/intervals_icu/coordinator.py`
- [ ] T006 Implement rolling derivation formulas (7-day status value, 21-day baseline range, low threshold) in `custom_components/intervals_icu/coordinator.py`
- [ ] T007 Implement age-norm lookup and poor-status persistence evaluation in `custom_components/intervals_icu/coordinator.py` (and `custom_components/intervals_icu/const.py` if constants are split)
- [ ] T008 Implement HRV source fingerprinting and cache invalidation/change-detection primitives in `custom_components/intervals_icu/coordinator.py`
- [ ] T009 Implement shared `wellness_hrv_status` coordinator payload defaults for `ok`/`insufficient_data`/`error` states in `custom_components/intervals_icu/coordinator.py`

**Checkpoint**: Shared HRV derivation foundation is ready for sensor exposure.

---

## Phase 3: User Story 1 - See Garmin-Like Daily HRV Status (Priority: P1) 🎯 MVP

**Goal**: Expose numeric HRV status and Garmin-style humanized level for the configured athlete.

**Independent Test**: With sufficient historical overnight HRV, verify Home Assistant exposes both `HRV Status` and `HRV Status (Level)` with correct Garmin label resolution.

- [ ] T010 [US1] Wire coordinator refresh to compute and publish latest `wellness_hrv_status.value` and `wellness_hrv_status.level` from wellness history in `custom_components/intervals_icu/coordinator.py`
- [ ] T011 [US1] Add new sensor descriptions for numeric `HRV Status` and text `HRV Status (Level)` in `custom_components/intervals_icu/sensor.py`
- [ ] T012 [US1] Implement `(Level)` label transformation to `Balanced`/`Unbalanced`/`Low`/`Poor`/`No status` using existing project naming conventions in `custom_components/intervals_icu/sensor.py`
- [ ] T013 [US1] Expose status attributes (`calculation_date`, `source_status`, `sample_count_7d`, `sample_count_21d`) on new status entities in `custom_components/intervals_icu/sensor.py`
- [ ] T014 [US1] Document `HRV Status` and `HRV Status (Level)` semantics/sources in `docs/API_METRICS.md`

**Checkpoint**: Daily Garmin-like HRV status value + level are available and independently testable.

---

## Phase 4: User Story 2 - Visualize Dynamic Baseline Bands (Priority: P2)

**Goal**: Expose baseline boundaries and low threshold as chart-ready numeric entities.

**Independent Test**: Verify `HRV Baseline Lower`, `HRV Baseline Upper`, and `HRV Low Threshold` are exposed, update with new overnight HRV, and can be plotted with `HRV Status`.

- [ ] T015 [US2] Extend coordinator-derived HRV payload with `baseline_low`, `baseline_high`, and `low_cutoff` fields for the latest calculation day in `custom_components/intervals_icu/coordinator.py`
- [ ] T016 [US2] Add sensor descriptions for baseline lower/upper/low-threshold entities in `custom_components/intervals_icu/sensor.py`
- [ ] T017 [US2] Add units/state-class/precision handling for baseline sensors in `custom_components/intervals_icu/sensor.py`
- [ ] T018 [P] [US2] Update charting guidance and metric definitions for baseline overlays in `docs/API_METRICS.md` and `README.md`
- [ ] T019 [US2] Implement null-safe exposure behavior for baseline/threshold entities when status is `No status` or baseline display should be suppressed in `custom_components/intervals_icu/coordinator.py` and `custom_components/intervals_icu/sensor.py`

**Checkpoint**: Dynamic baseline boundaries are available for Garmin-like chart overlays.

---

## Phase 5: User Story 3 - Efficient Bootstrap and Incremental Recalculation (Priority: P3)

**Goal**: Automatically bootstrap from history and avoid unnecessary recomputation when inputs are unchanged.

**Independent Test**: First refresh with historical HRV computes outputs immediately; unchanged refreshes hit cache; changed/new HRV triggers recalculation.

- [ ] T020 [US3] Implement historical bootstrap load window (default 120 days) for the configured athlete in `custom_components/intervals_icu/coordinator.py`
- [ ] T021 [US3] Implement unchanged-source cache-hit path to reuse derived HRV outputs in `custom_components/intervals_icu/coordinator.py`
- [ ] T022 [US3] Implement incremental recalculation path when latest HRV or corrected historical HRV changes in `custom_components/intervals_icu/coordinator.py`
- [ ] T023 [US3] Expose cache/recompute diagnostics (`cache_hit`, derivation metadata) via coordinator payload and sensor attributes in `custom_components/intervals_icu/coordinator.py` and `custom_components/intervals_icu/sensor.py`
- [ ] T024 [US3] Ensure unchanged polling cycles avoid unnecessary full-history processing while preserving correctness in `custom_components/intervals_icu/coordinator.py`

**Checkpoint**: Bootstrap and efficient incremental recalculation behavior are functioning.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, release readiness, and regression checks.

- [ ] T025 Run `python3 -m compileall custom_components/intervals_icu`
- [ ] T026 Perform manual HA validation for US1 scenarios using `specs/003-garmin-hrv-status/quickstart.md`
- [ ] T027 Perform manual HA validation for US2 scenarios using `specs/003-garmin-hrv-status/quickstart.md`
- [ ] T028 Perform manual HA validation for US3 scenarios using `specs/003-garmin-hrv-status/quickstart.md`
- [ ] T029 [P] Update `CHANGELOG.md` under unreleased notes with SemVer classification (`MINOR`) for this feature

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) -> Foundational (Phase 2) -> User stories (Phases 3-5) -> Polish (Phase 6)

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational phase only and delivers MVP value.
- **US2 (P2)**: Depends on Foundational phase and US1 entity plumbing for aligned sensor presentation.
- **US3 (P3)**: Depends on Foundational phase and US1 computation path; optimizes and hardens recalculation behavior.

### Parallel Opportunities

- T003 can run in parallel with T001/T002.
- T018 can run in parallel with T015/T016/T017.
- T029 can run in parallel with other polish tasks.

## Parallel Example: User Story 2

```bash
# Parallelizable US2 work once T015 is complete:
Task: "Add sensor descriptions for baseline lower/upper/low-threshold entities in custom_components/intervals_icu/sensor.py"
Task: "Update charting guidance and metric definitions for baseline overlays in docs/API_METRICS.md and README.md"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independently before expanding scope.

### Incremental Delivery

1. Deliver US1 (numeric + level Garmin-like status).
2. Add US2 (baseline ranges and threshold sensors).
3. Add US3 (bootstrap and efficiency/caching behavior).
4. Run polish validation and release-prep tasks.
