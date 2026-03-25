# Feature Specification: Daily Activity Calories Sensor

**Feature Branch**: `002-daily-activity-calories`  
**Created**: 2026-03-25  
**Status**: Draft  
**Input**: User description: "Create a spec to fix calories because the current summary calories reflects week-level totals; introduce a day-level calories burned metric based on activities from the day."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See True Daily Burned Calories (Priority: P1)

As a Home Assistant user, I want a calories sensor that reflects only calories burned
from my activities for one day, so dashboards and automations can use correct daily
activity energy.

**Why this priority**: This addresses the primary correctness bug and prevents weekly
totals from being misread as daily values.

**Independent Test**: Configure the integration for an athlete with known activity
calorie values on one day and verify the daily calories sensor equals the sum of that
day's activity calories.

**Acceptance Scenarios**:

1. **Given** two activities on the same day with 420 and 610 calories burned, **When**
   data refresh runs, **Then** the daily activity calories metric reports 1030.
2. **Given** the weekly summary calories value differs from that day's activity total,
   **When** the integration refreshes, **Then** the daily activity calories metric still
   reports the day-level activity total, not the weekly aggregate.

---

### User Story 2 - Keep Existing Summary Calories Backward Compatible (Priority: P2)

As an existing user, I want current summary calories behavior preserved, so upgrades do
not silently change the meaning of existing entities in my dashboards.

**Why this priority**: Backward compatibility avoids breaking existing automations and
historical expectations.

**Independent Test**: Upgrade from a version with only the summary calories sensor and
verify the old entity remains available and continues to represent summary data.

**Acceptance Scenarios**:

1. **Given** an existing installation using summary calories, **When** the feature is
   deployed, **Then** the summary calories entity remains present with unchanged
   semantics.
2. **Given** the new feature is deployed, **When** users inspect entities, **Then** the
   day-level activity calories metric is clearly separate and distinguishable from
   summary calories.

---

### User Story 3 - Handle Missing Activity Calorie Values Safely (Priority: P3)

As a user, I want predictable behavior when one or more activities do not include a
calorie value, so the daily metric does not fail or show stale data.

**Why this priority**: Real-world activity feeds may have incomplete fields, and sensor
stability is required for reliable automations.

**Independent Test**: Use a test day where one activity has calories and one does not,
and verify the metric stays available and sums only valid calorie values.

**Acceptance Scenarios**:

1. **Given** activities for a day include missing calorie fields, **When** data is
   refreshed, **Then** the daily activity calories metric is computed from available
   calorie values only.
2. **Given** no activities exist for the target day, **When** data is refreshed, **Then**
   the daily activity calories metric reports zero for that day.

---

### Edge Cases

- Athlete has activities on the day, but all returned entries omit calorie values.
- Activities occur around midnight and span two local dates.
- Partial API failure occurs while collecting day activity data.
- Duplicate activity records are returned for the same activity identifier.
- The service returns stale week summary data while day activity data is current.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a distinct day-level metric for "activity
  calories burned" that is separate from existing summary calories.
- **FR-002**: The day-level metric MUST be computed as the sum of calorie values from
  activities that belong to the target local day.
- **FR-003**: The default target day MUST be the current Home Assistant local calendar
  day at refresh time.
- **FR-004**: The system MUST continue to expose the existing summary calories metric
  with unchanged meaning and value source.
- **FR-005**: Activities without a valid calorie value MUST NOT cause refresh failure
  and MUST contribute zero to the day-level sum.
- **FR-006**: If no activities exist for the target day, the day-level metric MUST be
  reported as zero rather than reusing a prior non-zero value.
- **FR-007**: The system MUST avoid double-counting by ensuring each activity
  identifier contributes at most once to a day's calorie sum.
- **FR-008**: The day-level metric MUST expose the calculation day so users can confirm
  which date the value represents.
- **FR-009**: The system MUST refresh the day-level metric on normal integration update
  cycles without requiring manual reload.
- **FR-010**: The system MUST surface clear error state behavior when day activity data
  cannot be fetched, without leaking credentials.

### Non-Functional Requirements

- **NFR-001**: Daily activity calories data SHOULD appear within one normal polling
  cycle after new activities are available upstream.
- **NFR-002**: Normal refresh behavior MUST remain responsive for users with typical
  daily activity volume.
- **NFR-003**: Logging and diagnostics MUST redact sensitive authentication data.

### Data Semantics & Freshness *(required when exposing metrics/data fields)*

- Summary calories and day-level activity calories are distinct metrics with different
  semantics and must not be conflated.
- Day-level activity calories source of truth is per-activity calorie values for one
  local calendar day.
- Day-level activity calories does not roll over from prior days; each refresh
  recomputes the value for its target day.
- Missing calorie values in individual activities are treated as absent input (zero
  contribution), not as carry-forward from prior activities.

### Key Entities *(include if feature involves data)*

- **Daily Activity Window**: The local calendar day for which activity calories are
  computed.
- **Activity Calorie Record**: A single activity entry with an identifier, local start
  date/time, and optional calorie value.
- **Daily Activity Calories Metric**: The surfaced day-level numeric metric produced by
  summing valid calories from all activity calorie records in the window.

### Assumptions & Dependencies

- Activity calorie values represent kilocalories and are consistent across activities.
- The integration has sufficient read access to retrieve per-activity calorie data for
  the configured athlete.
- Existing summary calories remains useful for users who want multi-day aggregate
  context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For test days with known expected values, 100% of day-level outputs equal
  the sum of same-day activity calories.
- **SC-002**: 100% of existing summary calories entities remain available and unchanged
  in meaning after upgrade.
- **SC-003**: 100% of refreshes with missing activity calorie fields complete without
  crashing and produce a deterministic numeric result.
- **SC-004**: Users can determine the represented day for the metric directly from
  exposed entity information in all refresh states.
