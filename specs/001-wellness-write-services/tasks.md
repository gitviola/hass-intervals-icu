# Tasks: Wellness Data Write Support

**Input**: Design documents from `/specs/001-wellness-write-services/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Automated tests are desirable, but this repository currently has no test harness configured. Validation tasks include compile checks and manual HA service-call verification.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare integration metadata and service schema scaffolding.

- [ ] T001 Add service name/field constants for wellness writes in `custom_components/intervals_icu/const.py`
- [ ] T002 Create `custom_components/intervals_icu/services.yaml` with `set_wellness` service fields and descriptions
- [ ] T003 [P] Update `custom_components/intervals_icu/strings.json` and `custom_components/intervals_icu/translations/en.json` if service localization metadata is needed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared write-path primitives required by all stories.

**⚠️ CRITICAL**: No user story work should proceed until this phase is complete.

- [ ] T004 Add API client write method for `PUT /api/v1/athlete/{id}/wellness/{date}` in `custom_components/intervals_icu/api.py`
- [ ] T005 Implement shared payload mapping and validation helpers for writable wellness fields in `custom_components/intervals_icu/__init__.py` (or a new helper module under `custom_components/intervals_icu/`)
- [ ] T006 Implement central write error handling and result logging (without secrets) in `custom_components/intervals_icu/__init__.py`

**Checkpoint**: Write-path primitives exist and can be reused by service handlers.

---

## Phase 3: User Story 1 - Log Today's Weight and Nutrition (Priority: P1) 🎯 MVP

**Goal**: Allow writing weight/nutrition values without providing a date.

**Independent Test**: Call `intervals_icu.set_wellness` without `date`; verify target date resolves to local today and values are written.

- [ ] T007 [US1] Register `intervals_icu.set_wellness` service in `custom_components/intervals_icu/__init__.py`
- [ ] T008 [US1] Implement default-date behavior (HA local date) in service handler in `custom_components/intervals_icu/__init__.py`
- [ ] T009 [US1] Map service fields (`weight`, `kcal_consumed`, `carbohydrates`, `protein`, `fat_total`, `hydration_volume`) to Intervals wellness payload keys in `custom_components/intervals_icu/__init__.py`
- [ ] T010 [US1] Trigger coordinator refresh after successful write in `custom_components/intervals_icu/__init__.py`

**Checkpoint**: Daily no-date writes function end-to-end.

---

## Phase 4: User Story 2 - Backfill or Correct a Specific Day (Priority: P2)

**Goal**: Support explicit date writes for past/current days.

**Independent Test**: Call service with valid explicit date and verify only that date is updated; invalid date returns clear error.

- [ ] T011 [US2] Add explicit date validation (`YYYY-MM-DD`) in service handler in `custom_components/intervals_icu/__init__.py`
- [ ] T012 [US2] Ensure explicit date is passed to API path parameter in `custom_components/intervals_icu/api.py` call site
- [ ] T013 [P] [US2] Add usage examples for explicit date writes in `README.md`

**Checkpoint**: Backfill/correction writes work with deterministic date targeting.

---

## Phase 5: User Story 3 - Safe Partial Updates (Priority: P3)

**Goal**: Ensure omitted fields are never cleared or overwritten.

**Independent Test**: Update one field on a day with existing data and verify non-submitted fields remain unchanged.

- [ ] T014 [US3] Enforce "at least one writable field" rule and fail fast when none are provided in `custom_components/intervals_icu/__init__.py`
- [ ] T015 [US3] Ensure outbound payload includes only explicitly provided fields in `custom_components/intervals_icu/__init__.py`
- [ ] T016 [US3] Validate non-destructive failure behavior: on API error, do not mutate local coordinator cache and return actionable error in `custom_components/intervals_icu/__init__.py`

**Checkpoint**: Partial update safety is guaranteed.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and release readiness.

- [ ] T017 Run `python3 -m compileall custom_components/intervals_icu`
- [ ] T018 Verify `services.yaml` fields align with handler validation and docs
- [ ] T019 [P] Update release docs/changelog if feature is included in next release
- [ ] T020 Manual HA smoke test: no-date write, explicit-date write, empty payload failure, invalid-date failure

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) -> Foundational (Phase 2) -> User stories (Phases 3-5) -> Polish (Phase 6)

### User Story Dependencies

- US1 depends on Foundational phase only.
- US2 depends on Foundational phase and can build on US1 handler logic.
- US3 depends on Foundational phase and should validate behavior introduced in US1/US2.

### Parallel Opportunities

- T003 can run in parallel with T001/T002.
- T013 can run in parallel with T011/T012.
- T019 can run in parallel with other polish tasks.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 (Phase 3).
3. Validate no-date writes in HA.

### Incremental Delivery

1. Add US2 explicit date support.
2. Add US3 partial update safety guarantees.
3. Complete polish validation before release.
