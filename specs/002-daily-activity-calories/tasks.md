# Tasks: Daily Activity Calories Sensor

**Input**: Design documents from `/specs/002-daily-activity-calories/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Automated tests are not explicitly required by the feature spec and no
dedicated test harness is currently configured in this repository. Validation tasks
therefore focus on compile checks plus manual Home Assistant verification.

**Organization**: Tasks are grouped by user story so each story can be implemented and
validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared metric-source scaffolding and documentation anchors.

- [X] T001 Add/declare a dedicated coordinator payload slice for day-level activity calories in `custom_components/intervals_icu/coordinator.py`
- [X] T002 Add source identifier/constants needed for daily activity calories sensor plumbing in `custom_components/intervals_icu/sensor.py` and `custom_components/intervals_icu/const.py` (if needed)
- [X] T003 [P] Prepare docs placeholders for new day-level metric semantics in `docs/API_METRICS.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared API/coordinator primitives required by all user stories.

**⚠️ CRITICAL**: No user story work should proceed until this phase is complete.

- [X] T004 Add API client read helper for day-window activities (including field selection support) in `custom_components/intervals_icu/api.py`
- [X] T005 Implement day-window construction helper using Home Assistant local date semantics in `custom_components/intervals_icu/coordinator.py`
- [X] T006 Implement shared daily activity-calorie aggregation helper (sum, dedupe-by-id, missing calorie handling) in `custom_components/intervals_icu/coordinator.py`
- [X] T007 Implement coordinator error/diagnostic handling for activity-daily slice without leaking secrets in `custom_components/intervals_icu/coordinator.py`

**Checkpoint**: Shared activity-daily fetch and aggregation primitives are ready for
sensor exposure.

---

## Phase 3: User Story 1 - See True Daily Burned Calories (Priority: P1) 🎯 MVP

**Goal**: Expose a new day-level calories-burned sensor computed from same-day
activities.

**Independent Test**: For a day with known activity calories, verify the new daily
sensor equals the sum of same-day activity calories and does not match week summary
when they differ.

- [X] T008 [US1] Wire coordinator update flow to fetch day-window activities and store computed daily aggregate in `custom_components/intervals_icu/coordinator.py`
- [X] T009 [US1] Add new daily activity calories sensor entity description and unit in `custom_components/intervals_icu/sensor.py`
- [X] T010 [US1] Expose calculation-day metadata for the daily calories sensor (state attribute or paired date entity) in `custom_components/intervals_icu/sensor.py`
- [X] T011 [US1] Document the new daily activity calories metric source and semantics in `docs/API_METRICS.md`

**Checkpoint**: A new daily activity calories sensor is available and returns correct
same-day totals.

---

## Phase 4: User Story 2 - Keep Existing Summary Calories Backward Compatible (Priority: P2)

**Goal**: Preserve existing summary calories meaning while keeping the new metric
clearly separate.

**Independent Test**: Upgrade an existing setup and verify old summary calories entity
remains available/unchanged while new daily metric appears as a separate entity.

- [X] T012 [US2] Confirm and enforce no behavior changes to existing `summary_calories` mapping in `custom_components/intervals_icu/sensor.py`
- [X] T013 [US2] Ensure unique IDs and naming for the new daily calories entity avoid collision with existing summary calories entity in `custom_components/intervals_icu/sensor.py`
- [X] T014 [P] [US2] Update user-facing docs to clarify difference between summary calories and daily activity calories in `README.md` and `docs/API_METRICS.md`

**Checkpoint**: Backward compatibility is preserved and metric semantics are clearly
distinguished.

---

## Phase 5: User Story 3 - Handle Missing Activity Calorie Values Safely (Priority: P3)

**Goal**: Keep daily metric deterministic and stable with missing/invalid calorie
fields or no-activity days.

**Independent Test**: Validate days with mixed calorie availability and zero-activity
days produce deterministic values (`sum(valid)` or `0`) without stale rollovers.

- [X] T015 [US3] Enforce zero-contribution behavior for activities with missing/invalid calories in `custom_components/intervals_icu/coordinator.py`
- [X] T016 [US3] Enforce no-activity-day behavior (`0` with correct calculation date) in `custom_components/intervals_icu/coordinator.py`
- [X] T017 [US3] Ensure daily activity calories do not use rollover cache from prior days in `custom_components/intervals_icu/coordinator.py`
- [X] T018 [US3] Add diagnostics/status fields for partial/error activity-daily data to aid troubleshooting in `custom_components/intervals_icu/coordinator.py` and `custom_components/intervals_icu/sensor.py`

**Checkpoint**: Missing-data and zero-activity edge cases are handled predictably.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, release readiness, and regression checks.

- [X] T019 Run `python3 -m compileall custom_components/intervals_icu`
- [X] T020 Skipped by user: manual HA validation for US1 scenario (known same-day activity calorie sum) in `specs/002-daily-activity-calories/quickstart.md`
- [X] T021 Skipped by user: manual HA validation for US2 scenario (summary calories unchanged + separate new entity) in `specs/002-daily-activity-calories/quickstart.md`
- [X] T022 Skipped by user: manual HA validation for US3 scenario (missing calorie values and no-activity day) in `specs/002-daily-activity-calories/quickstart.md`
- [X] T023 [P] Update `CHANGELOG.md` unreleased section with feature summary and note SemVer classification (`MINOR`)

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) -> Foundational (Phase 2) -> User stories (Phases 3-5) -> Polish (Phase 6)

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational phase only and delivers MVP value.
- **US2 (P2)**: Depends on US1 additions in `sensor.py` to validate compatibility and separation.
- **US3 (P3)**: Depends on US1 aggregation path and extends robustness/edge-case handling.

### Parallel Opportunities

- T003 can run in parallel with T001/T002.
- T014 can run in parallel with T012/T013.
- T023 can run in parallel with other polish tasks.

## Parallel Example: User Story 1

```bash
# Parallelizable US1 work once T008 is complete:
Task: "Add new daily activity calories sensor entity description and unit in custom_components/intervals_icu/sensor.py"
Task: "Document the new daily activity calories metric source and semantics in docs/API_METRICS.md"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independently before expanding scope.

### Incremental Delivery

1. Deliver US1 (new correct daily metric).
2. Add US2 compatibility/documentation safeguards.
3. Add US3 resilience semantics for missing/no-data cases.
4. Run polish validation and release-prep tasks.
