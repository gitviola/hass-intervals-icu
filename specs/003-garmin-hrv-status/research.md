# Research: Garmin-Like HRV Status and Baseline Ranges

## Decision 1: Use Garmin's externally documented HRV status rules as hard requirements

- Decision: Align core behavior to Garmin-documented semantics:
  seven-day average status value, baseline-range comparison, and status labels
  `Balanced`, `Unbalanced`, `Low`, `Poor`, `No status`.
- Rationale: This is the only authoritative public description of Garmin HRV
  status behavior and gives deterministic acceptance criteria.
- Alternatives considered:
  - Invent custom status names/logic: rejected because user goal is Garmin-like
    behavior.

## Decision 2: Implement a behavioral clone, not an exact proprietary clone

- Decision: Treat Garmin internals for baseline-range construction as unknown and
  specify an explicit open formula in this integration.
- Rationale: Garmin publishes status semantics, but not the exact baseline
  coefficient math.
- Alternatives considered:
  - Claim exact Garmin equivalence: rejected because it is not verifiable from
    public documentation.

## Decision 3: Define numeric `HRV Status` as rolling 7-day overnight HRV mean

- Decision: `hrv_status_value(day) = mean(overnight_hrv over trailing 7 days)`
  when at least 6 valid nightly values exist in the window.
- Rationale: Garmin explicitly frames status from a seven-day average while
  allowing minor source gaps keeps behavior practical with occasional missing
  wellness entries.
- Alternatives considered:
  - Require strict 7/7 nightly samples: rejected as too brittle for real-world
    missing nights.
  - Use median instead of mean: rejected due weaker parity with Garmin wording.

## Decision 4: Define baseline range from a rolling 21-day personal window

- Decision: Build per-day baseline from trailing 21-day overnight HRV values:
  - `baseline_mean = mean(window_21d)`
  - `baseline_sd = stdev(window_21d)`
  - `baseline_low = baseline_mean - 0.5 * baseline_sd`
  - `baseline_high = baseline_mean + 0.5 * baseline_sd`
  Require at least 18 valid samples in the 21-day window.
- Rationale: Three-week initialization matches Garmin's "three weeks" guidance,
  and ±0.5 SD (smallest worthwhile change style) is a common HRV-guided
  monitoring convention.
- Alternatives considered:
  - Percentile band (P25-P75): rejected for this version because SD-based
    cutoffs provide simpler, tunable continuity with a `Low` threshold.
  - Fixed baseline from first 3 weeks only: rejected because user explicitly
    wants a moving personalized baseline.

## Decision 5: Model `Low` as a stricter below-baseline condition

- Decision: `low_cutoff = baseline_mean - 1.0 * baseline_sd`; classify `Low`
  when seven-day status value is below this cutoff.
- Rationale: This creates a deterministic "well below baseline" zone below the
  balanced band and mirrors Garmin's separate `Unbalanced` vs `Low` semantics.
- Alternatives considered:
  - Use only one below-baseline class: rejected because Garmin differentiates
    `Unbalanced` and `Low`.

## Decision 6: Model `Poor` from age-aware norms using an explicit reference table

- Decision: Add an age/sex reference lower bound table and classify `Poor` when
  both seven-day status and 21-day baseline mean remain below that lower bound
  for a configurable persistence period (default 7 days).
- Rationale: Garmin describes `Poor` as values averaging well below normal for
  age; persistence avoids noisy one-day downgrades.
- Alternatives considered:
  - Disable `Poor`: rejected because Garmin includes this status.
  - Trigger `Poor` on a single low day: rejected due volatility.

## Decision 7: Apply strict status precedence to avoid ambiguity

- Decision: Resolve status in this order:
  1) `No status` (insufficient data),
  2) `Poor` (age-norm breach with persistence),
  3) `Low` (below low cutoff),
  4) `Balanced` (inside baseline band),
  5) `Unbalanced` (outside baseline but not low/poor).
- Rationale: Guarantees one label per day and keeps `Low`/`Poor` dominant over
  generic out-of-range cases.
- Alternatives considered:
  - Check balanced first: rejected because it can mask low/poor conditions.

## Decision 8: Use coordinator-side caching with source fingerprinting

- Decision: Derivation runs in coordinator using a normalized wellness HRV
  fingerprint (`date`, `hrv`, `updated`). If fingerprint is unchanged, reuse
  cached outputs; if changed, recompute only the affected tail window.
- Rationale: Minimizes CPU/API churn while preserving correctness.
- Alternatives considered:
  - Full recompute every poll: rejected as unnecessary overhead.

## Decision 9: Bootstrap automatically from historical wellness HRV

- Decision: On first run (or when cache unavailable), fetch bounded historical
  wellness data (default 120 days), derive day-by-day status/ranges, and expose
  latest day immediately.
- Rationale: Matches user expectation that feature should be immediately useful
  without waiting weeks after enablement.
- Alternatives considered:
  - Forward-only computation after install: rejected due delayed usefulness.

## Decision 10: Expose range boundaries as normal numeric sensors for HA charts

- Decision: Publish baseline lower/upper and low threshold as dedicated numeric
  sensors (state history friendly), plus a text `(Level)` sensor for status.
- Rationale: Home Assistant core charts work naturally with numeric entity
  series; this is the lowest-friction path for Garmin-like overlays.
- Alternatives considered:
  - Store only attributes on one entity: rejected due poorer chart usability.
  - Introduce custom chart/range entity type in integration: rejected as out of
    scope and unnecessary for MVP.

## Comparative Signals from Other Platforms

- Oura: compares short-term HRV trend against longer personal baseline windows
  (two-week trend vs three-month average for "HRV balance").
- WHOOP: computes HRV from a stable overnight segment (deep sleep) and frames
  interpretation around personal trend over time rather than single values.
- Common pattern: short-term rolling metric + personal baseline + age context.

## Sources Consulted

- Garmin device manual (HRV status semantics and labels):
  https://www8.garmin.com/manuals/webhelp/GUID-D3C2D1F9-D2C0-404D-9372-7B2D57459BF8/EN-US/GUID-9282196F-D969-404D-B678-F48A13D8D0CB.html
- Oura glossary (`HRV balance` windowing concept):
  https://support.ouraring.com/hc/en-us/articles/5949130374547-Glossary
- WHOOP HRV explainer (overnight/deep-sleep measurement and trend framing):
  https://www.whoop.com/us/en/thelocker/heart-rate-variability-hrv/
- Lifelines cohort RMSSD age/sex reference values:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7734556/
- HRV-guided training methodological review (rolling averages/SWC conventions):
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8507742/
- Home Assistant history graph card docs:
  https://www.home-assistant.io/dashboards/history-graph/
- Home Assistant statistics graph card docs:
  https://www.home-assistant.io/dashboards/statistics-graph/
- ApexCharts card capabilities for advanced range visualization:
  https://github.com/RomRider/apexcharts-card
