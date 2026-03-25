# Feature Specification: Wellness Data Write Support

**Feature Branch**: `001-wellness-write-services`  
**Created**: 2026-03-25  
**Status**: Draft  
**Input**: User description: "Allow updating/setting Intervals.icu wellness data from Home Assistant; if no date is provided use current date; only provided fields are updated and omitted fields must remain unchanged."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Log Today's Weight and Nutrition (Priority: P1)

As a Home Assistant user, I want to write weight and nutrition values for today without
manually providing a date, so I can quickly log daily wellness values from automations
or dashboards.

**Why this priority**: This is the primary value: fast day-to-day capture with minimal
friction.

**Independent Test**: Execute a wellness update action with weight and nutrition fields,
without a date, and verify the values are stored for today's record.

**Acceptance Scenarios**:

1. **Given** the integration is configured and authenticated, **When** the user submits
   weight and kcal consumed with no date, **Then** the integration writes to the
   current local date record.
2. **Given** only protein is submitted for today's update, **When** the action runs,
   **Then** only protein is changed and other nutrition fields remain unchanged.

---

### User Story 2 - Backfill or Correct a Specific Day (Priority: P2)

As a user, I want to provide an explicit date when updating wellness values, so I can
backfill or correct past entries.

**Why this priority**: Backfill/correction is important but secondary to daily logging.

**Independent Test**: Submit an update with an explicit date and verify the target date
record is updated rather than today's record.

**Acceptance Scenarios**:

1. **Given** an explicit ISO date is provided, **When** the update action runs,
   **Then** the integration writes values to that exact date.
2. **Given** an invalid date string, **When** the user runs the action,
   **Then** the integration rejects the request with a clear validation error.

---

### User Story 3 - Safe Partial Updates (Priority: P3)

As a user, I want partial updates to never clear unrelated wellness fields, so I can
update one metric safely without accidental data loss.

**Why this priority**: Data safety is critical and should be guaranteed for all writes.

**Independent Test**: Pre-populate a day with multiple wellness fields, submit an update
for a single field, and verify non-submitted fields remain unchanged.

**Acceptance Scenarios**:

1. **Given** existing values for weight, protein, and carbohydrates, **When** only
   weight is submitted, **Then** protein and carbohydrates remain unchanged.
2. **Given** no writable wellness fields are provided, **When** the action runs,
   **Then** the integration fails fast with a clear "no update fields provided" error.

---

### Edge Cases

- Request omits date and runs around local midnight boundary.
- Request includes unsupported field names.
- Request includes invalid numeric values (for example negative nutrition grams).
- Intervals API returns auth/network/server error during write.
- Two updates target the same date in quick succession.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a Home Assistant action to submit wellness field
  updates for an athlete.
- **FR-002**: The system MUST support writing at least weight and nutrition-related
  wellness fields (kcal consumed, carbohydrates, protein, fat total, hydration volume).
- **FR-003**: If `date` is not provided, the system MUST target the current local date.
- **FR-004**: If `date` is provided, the system MUST target that exact ISO-8601 day.
- **FR-005**: The system MUST perform partial update semantics: only explicitly provided
  writable fields are submitted for change.
- **FR-006**: The system MUST NOT alter non-provided wellness fields in the target record.
- **FR-007**: The system MUST reject requests that provide no writable wellness fields.
- **FR-008**: The system MUST validate input types/formats and return actionable errors
  for invalid inputs.
- **FR-009**: The system MUST report action outcome (success/failure) with sufficient
  context for Home Assistant automation traces.
- **FR-010**: After a successful write, the system MUST refresh integration data so
  entities reflect updated values without requiring manual reload.

### Non-Functional Requirements

- **NFR-001**: The action response SHOULD complete within 5 seconds for normal API
  conditions.
- **NFR-002**: The system MUST redact secrets from logs and error output.
- **NFR-003**: Failed writes MUST be non-destructive (no local mutation that implies a
  successful remote write).

### Data Semantics & Freshness *(required when exposing metrics/data fields)*

- Source of truth for persisted wellness values is Intervals.icu.
- Date default uses Home Assistant local date at execution time.
- Omitted fields in an update request are treated as "no change," not null.
- Sensors refresh after successful write and continue to follow existing freshness/
  rollover rules.

### Key Entities *(include if feature involves data)*

- **Wellness Update Request**: User-submitted payload containing optional `date` and
  one or more writable wellness fields.
- **Writable Wellness Field Set**: Allowed subset of wellness fields accepted by this
  feature for write operations.
- **Wellness Update Result**: Structured outcome containing success status, target date,
  and error details when applicable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successful no-date updates target the current local date.
- **SC-002**: 100% of partial updates preserve non-submitted fields in the target
  wellness record.
- **SC-003**: 100% of invalid requests (bad date/no writable fields/invalid values)
  return explicit, actionable errors.
- **SC-004**: Updated sensor values are visible within one normal refresh cycle after
  successful writes.
