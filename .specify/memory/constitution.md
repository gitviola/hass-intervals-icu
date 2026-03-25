<!--
Sync Impact Report
- Version change: template (unversioned) -> 1.0.0
- Modified principles:
  - Template Principle 1 -> I. Home Assistant UX and Entity Stability
  - Template Principle 2 -> II. Coordinator-First Data Collection
  - Template Principle 3 -> III. Metric Semantics, Freshness, and Rollover
  - Template Principle 4 -> IV. Security, Privacy, and Diagnostics
  - Template Principle 5 -> V. Semantic Releases and HACS Compliance
- Added sections:
  - Technical and Quality Standards
  - Development Workflow and Quality Gates
- Removed sections:
  - Placeholder-only template sections
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md
  - ✅ .specify/templates/spec-template.md
  - ✅ .specify/templates/tasks-template.md
  - ⚠ pending: .specify/templates/commands/*.md (directory not present in this repo)
- Follow-up TODOs: none
-->

# hass-intervals-icu Constitution

## Core Principles

### I. Home Assistant UX and Entity Stability
This integration MUST provide a reliable Home Assistant-native user experience:
- Setup MUST use config entries and options flow, with no YAML-only setup path.
- Entity `unique_id` values MUST be stable across upgrades.
- The integration MUST avoid duplicate logical entries for the same athlete.
- User-facing metric names MUST stay backward compatible unless a breaking release
  and migration note are provided.

### II. Coordinator-First Data Collection
All remote reads MUST be coordinated and asynchronous:
- API polling MUST be centralized through `DataUpdateCoordinator`.
- Entities MUST NOT perform direct network I/O in state properties.
- Polling interval configuration MUST enforce safe lower bounds.
- Auth/network/API failures MUST degrade gracefully and expose actionable errors.

### III. Metric Semantics, Freshness, and Rollover
Metric correctness is non-negotiable:
- Every exposed metric MUST map to a documented API source field.
- Date-scoped metrics (sleep, steps, nutrition) MUST define freshness behavior.
- Rollover of null values MUST only apply to explicitly persistent metrics, with
  exceptions documented and tested.
- Display formatting (humanized text, precision hints) MUST NOT mutate raw values.

### IV. Security, Privacy, and Diagnostics
Sensitive data protection and operability are mandatory:
- API credentials MUST NEVER be committed, logged, or emitted in diagnostics.
- Diagnostic output MUST redact secrets and personal identifiers where applicable.
- Error handling MUST avoid leaking confidential payload data.
- Troubleshooting paths SHOULD include clear log categories and remediation steps.

### V. Semantic Releases and HACS Compliance
Release discipline MUST align with Home Assistant and HACS expectations:
- Versioning MUST follow Semantic Versioning (`MAJOR.MINOR.PATCH`).
- Every release MUST include:
  - manifest version update,
  - `CHANGELOG.md` entry,
  - GitHub Release notes.
- Release tags MUST be `vX.Y.Z` and match manifest version `X.Y.Z`.
- HACS and hassfest validations MUST pass before publishing.

## Technical and Quality Standards

- Runtime code SHOULD be typed, async-safe Python and align with HA integration
  architecture patterns.
- Integration metadata (`manifest.json`, `hacs.json`, translations) MUST remain
  valid and in sync with config/options flow behavior.
- Changes affecting data semantics, polling, or user-visible sensors MUST include
  verification steps (at minimum compile checks and targeted runtime validation).
- New behavior that changes output meaning SHOULD include docs updates in README
  and/or docs inventory files.

## Development Workflow and Quality Gates

- Feature development SHOULD follow: `specify -> clarify -> plan -> tasks ->
  analyze -> implement`.
- Constitution checks in planning are a hard gate: unresolved MUST conflicts
  require spec/plan/task updates before implementation.
- Pull requests SHOULD include:
  - scope summary,
  - validation evidence,
  - release/changelog impact statement.
- Pull requests merged into `main` MUST use **Squash and merge** so each PR
  contributes exactly one commit on `main`.
- Hotfixes MAY bypass full planning flow only for urgent production breakages, but
  MUST still satisfy release, validation, and documentation obligations.

## Governance

This constitution supersedes conflicting local conventions for this repository.

- Amendment process:
  - Propose changes via pull request with rationale and impact summary.
  - Classify version bump by semantic impact:
    - MAJOR: incompatible principle removal or redefinition.
    - MINOR: new principle/section or materially expanded obligations.
    - PATCH: clarifications without semantic policy change.
  - Record amendment date and version update in this file.
- Compliance review expectations:
  - Every plan and release SHOULD include a constitution compliance check.
  - Non-compliance MUST be explicitly documented with remediation or approved
    exception rationale.

**Version**: 1.0.0 | **Ratified**: 2026-03-24 | **Last Amended**: 2026-03-24
