# Feature Specification: Garmin-Like HRV Status and Baseline Ranges

**Feature Branch**: `003-garmin-hrv-status`  
**Created**: 2026-03-25  
**Status**: Draft  
**Input**: User description: "Mimic Garmin HRV status as closely as possible, expose numeric HRV status and Garmin-style humanized status, compute dynamic personalized baseline ranges, support efficient cached recalculation, and automatically bootstrap from available historical data for chart-ready outputs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Garmin-Like Daily HRV Status (Priority: P1)

As a Home Assistant user, I want a daily HRV status value and a Garmin-style status label,
so I can quickly understand my current recovery state from overnight HRV trends.

**Why this priority**: This is the core feature value and directly mirrors the Garmin
experience users expect.

**Independent Test**: Provide sufficient historical overnight HRV data and verify the
integration exposes a numeric status value plus a humanized status label for today.

**Acceptance Scenarios**:

1. **Given** at least 7 recent valid overnight HRV data points, **When** the integration
   refreshes, **Then** it exposes a numeric daily HRV status value derived from a
   seven-day trend.
2. **Given** valid baseline and trend data, **When** the daily status is evaluated,
   **Then** the humanized status is one of Garmin-style labels: `Balanced`,
   `Unbalanced`, `Low`, `Poor`, or `No status`.
3. **Given** insufficient data to compute the seven-day trend, **When** status is
   evaluated, **Then** the humanized status is `No status`.

---

### User Story 2 - Visualize Dynamic Baseline Bands (Priority: P2)

As a user building dashboards, I want baseline boundaries and related thresholds exposed as
entities, so I can build charts that mimic Garmin-style HRV visuals with moving ranges.

**Why this priority**: The charting use case requires explicit range boundaries, not just a
single status label.

**Independent Test**: Verify baseline low/high and low-threshold outputs exist and update
as new overnight HRV data is received.

**Acceptance Scenarios**:

1. **Given** enough personalization history, **When** the integration refreshes,
   **Then** it exposes today's baseline lower and upper boundaries.
2. **Given** data sufficient for low-status detection, **When** thresholds are computed,
   **Then** the integration exposes the "well below baseline" cutoff used for `Low`
   classification.
3. **Given** ongoing daily data over multiple days, **When** baseline is recalculated,
   **Then** baseline boundaries can move over time and are retained as day-by-day sensor
   history in Home Assistant.

---

### User Story 3 - Efficient Bootstrap and Incremental Recalculation (Priority: P3)

As a user, I want the feature to automatically calculate from existing historical HRV data
and only recompute when needed, so I get immediate usefulness without unnecessary API or CPU
cost.

**Why this priority**: Practical reliability and efficiency are required for always-on Home
Assistant integrations.

**Independent Test**: Start from no prior derived status in Home Assistant but with
historical wellness HRV available upstream, then verify status/baseline appear after
bootstrap and remain stable between unchanged updates.

**Acceptance Scenarios**:

1. **Given** historical overnight HRV exists upstream but no derived local history exists,
   **When** the first refresh runs, **Then** the integration automatically bootstraps
   status and baseline from available past data.
2. **Given** no new overnight HRV record and no modified upstream HRV record,
   **When** periodic refresh runs, **Then** costly full recalculation is skipped.
3. **Given** a new or changed overnight HRV record arrives, **When** refresh runs,
   **Then** affected daily status and baseline outputs are recalculated.

---

### Edge Cases

- Fewer than 7 valid overnight HRV points in the recent window.
- Enough points for a seven-day value but not enough personalization depth for a stable
  baseline range.
- Missing age and/or sex information required for age-based `Poor` classification.
- Historical HRV backfill contains gaps (non-consecutive days) or null HRV values.
- Upstream historical record corrections change a past day's HRV after status was already
  computed.
- Time-zone/day-boundary differences between source data and Home Assistant local date.
- Baseline qualifies as `Poor`, where Garmin semantics suppress baseline range display.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose a numeric daily `HRV Status` value representing a
  seven-day trend of overnight HRV values.
- **FR-002**: The system MUST expose a humanized `HRV Status (Level)` value using Garmin
  label names: `Balanced`, `Unbalanced`, `Low`, `Poor`, `No status`.
- **FR-003**: The system MUST derive all status calculations from overnight HRV values
  sourced from wellness records.
- **FR-004**: The system MUST evaluate status labels with deterministic precedence so each
  day resolves to exactly one label.
- **FR-005**: The system MUST classify `Balanced` when the seven-day HRV status value is
  within the personalized baseline range.
- **FR-006**: The system MUST classify `Unbalanced` when the seven-day HRV status value is
  outside the personalized baseline range but not in `Low` or `Poor` conditions.
- **FR-007**: The system MUST classify `Low` when the seven-day HRV status value is well
  below the personalized baseline (using a distinct low cutoff below baseline lower bound).
- **FR-008**: The system MUST classify `Poor` when the athlete's personal HRV baseline is
  below age-based healthy norms.
- **FR-009**: The system MUST classify `No status` when there is insufficient data for a
  reliable seven-day status value.
- **FR-010**: The system MUST expose current-day baseline lower boundary and baseline upper
  boundary as separate numeric entities.
- **FR-011**: The system MUST expose the low-status cutoff threshold used in `Low`
  classification as a separate numeric entity.
- **FR-012**: The system MUST expose enough metadata (for example calculation date and data
  sufficiency indicators) for users to understand whether status and bounds are valid.
- **FR-013**: The system MUST calculate baseline boundaries per day so the personalized
  baseline can evolve over time.
- **FR-014**: The system MUST automatically bootstrap calculations from available historical
  HRV data when derived status is not yet present locally.
- **FR-015**: If historical upstream data is sufficient at bootstrap time, the system MUST
  produce status and baseline outputs without waiting for newly collected future days.
- **FR-016**: The system MUST detect unchanged source wellness HRV data and avoid full
  recalculation on refresh cycles where inputs are unchanged.
- **FR-017**: The system MUST recalculate status/baseline when a new overnight HRV point is
  available or when relevant historical HRV values have changed upstream.
- **FR-018**: The system MUST keep existing overnight HRV sensor behavior intact and treat
  derived status metrics as additive entities.
- **FR-019**: The system MUST follow existing project naming convention for humanized scale
  sensors by exposing the text variant as a `(Level)` entity.
- **FR-020**: The system MUST ensure outputs are chart-friendly in core Home Assistant by
  surfacing status value and range boundaries as regular numeric sensor entities with
  historical state tracking semantics.

### Non-Functional Requirements

- **NFR-001**: Under unchanged source data, refresh cycles SHOULD not perform repeated full
  historical recalculation.
- **NFR-002**: The feature MUST keep normal integration polling responsive for typical
  wellness history sizes.
- **NFR-003**: Source-data fetches and processing MUST be bounded to the minimum historical
  span needed for status and baseline correctness.
- **NFR-004**: Logs and diagnostics MUST not expose credentials or sensitive account data.

### Data Semantics & Freshness *(required when exposing metrics/data fields)*

- Source of truth for overnight HRV is Intervals.icu wellness data.
- The numeric `HRV Status` reflects a seven-day trend value (daily rolling computation),
  not the single latest overnight HRV measurement.
- The existing overnight HRV sensor remains the source for the latest single-night HRV.
- Baseline lower/upper boundaries and low cutoff are date-scoped derived values that can
  change as new overnight HRV data is incorporated.
- `No status` indicates insufficient data for reliable seven-day trend and/or baseline
  context.
- `Poor` follows Garmin-like semantics tied to age-based health norms and may suppress
  display of baseline range values when active.

### Key Entities *(include if feature involves data)*

- **Overnight HRV Observation**: A daily wellness HRV value tied to a specific local date,
  used as raw input.
- **Daily HRV Status Point**: Derived per-day record containing status value, status label,
  and data-sufficiency outcome.
- **Personalized Baseline Range**: Per-day lower and upper boundaries representing the
  athlete's expected HRV range from prior personal history.
- **Low Threshold**: Per-day cutoff below baseline used to distinguish `Low` from
  `Unbalanced`.
- **Age-Norm Assessment**: Derived comparison outcome used to determine whether `Poor`
  classification applies.

### Assumptions & Dependencies

- Overnight HRV in wellness records is sufficiently aligned with Garmin's overnight HRV
  concept for practical mimicry.
- Exact proprietary Garmin internal coefficients are not publicly specified; this feature
  targets behaviorally equivalent classification logic from documented Garmin semantics.
- Age-based norm thresholds are available from a maintainable reference table suitable for
  deterministic `Poor` evaluation.
- Home Assistant charting is expected to be built from numeric sensor histories (status
  value and boundary sensors) rather than a proprietary range-band entity type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When sufficient input data exists, 100% of refreshes expose both a numeric
  `HRV Status` value and a valid Garmin-style `HRV Status (Level)` value.
- **SC-002**: In controlled test datasets representing each label condition, status
  classification resolves to the expected one of `Balanced`, `Unbalanced`, `Low`, `Poor`,
  or `No status` in 100% of cases.
- **SC-003**: On first run with sufficient historical HRV available upstream, derived
  status and baseline boundaries become available within one normal refresh cycle.
- **SC-004**: On refresh cycles with unchanged HRV source data, repeated full historical
  recalculation is avoided in 100% of observed cycles.
- **SC-005**: Users can build a Garmin-like trend chart from exposed entities by plotting
  at minimum: `HRV Status` value, baseline lower bound, and baseline upper bound.
