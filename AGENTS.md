# AGENTS.md

## Purpose
Build and maintain a Home Assistant custom integration (`intervals_icu`) that maps Intervals.icu API data to Home Assistant sensors.

## Guardrails
- Keep changes inside this repository.
- Never commit secrets, API keys, or tokens.
- Preserve Home Assistant integration domain: `intervals_icu`.
- Prefer additive, minimal-risk changes.

## Technical defaults
- Use config entries + config flow for setup.
- Use `DataUpdateCoordinator` for shared polling.
- Use typed, async Python code.
- Keep sensor logic in `sensor.py` and API calls in `api.py`.

## Validation
Before finalizing significant changes:
1. Run `python3 -m compileall custom_components/intervals_icu`.
2. Ensure manifest and translations stay in sync with config/options flow fields.
3. Confirm no credentials appear in tracked files.

## Releases
Release rules (mandatory):

1. Follow Semantic Versioning (`MAJOR.MINOR.PATCH`):
   - `MAJOR`: breaking changes (removed/renamed entities, incompatible config/data behavior).
   - `MINOR`: backward-compatible features (new sensors/options/behavior).
   - `PATCH`: backward-compatible fixes/docs/CI/internal changes.
2. Every release MUST include a changelog entry in `CHANGELOG.md`.
3. Every release MUST be a full GitHub Release with release notes (not only a git tag), matching HACS publish expectations.
4. Tag format MUST be `vX.Y.Z` and MUST match manifest version `X.Y.Z`.
5. Never retag or move an existing release tag.

Release checklist:

1. Add/update `CHANGELOG.md` under `## [Unreleased]` while developing.
2. At release time, move unreleased notes into `## [X.Y.Z] - YYYY-MM-DD`.
3. Update `custom_components/intervals_icu/manifest.json` `version` to `X.Y.Z` (no `v` prefix).
4. Run validation checks (`python3 -m compileall custom_components/intervals_icu` and CI workflows if available).
5. Commit release artifacts (including changelog + manifest).
6. Create annotated tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
7. Push branch and tag: `git push origin main && git push origin vX.Y.Z`.
8. Publish GitHub Release `vX.Y.Z` with concise user-facing notes aligned with `CHANGELOG.md`.

Backfill policy:
- If a tag exists without release notes or changelog coverage, backfill both before the next release.

## Pull Requests
- PRs merged into `main` MUST always use **Squash and merge**.
- Goal: each merged PR results in exactly one commit in `main`.

## Active Technologies
- Python 3.13+ (Home Assistant custom integration runtime) + Home Assistant core helpers/config entries/services, aiohttp clien (001-wellness-write-services)
- N/A (remote API + in-memory coordinator cache) (001-wellness-write-services)
- Python 3.13+ (Home Assistant custom integration runtime) + Home Assistant coordinator/entity helpers, aiohttp client, Intervals.icu REST API (002-daily-activity-calories)
- Python 3.13+ (Home Assistant custom integration runtime) + Home Assistant coordinator/entity helpers, aiohttp client, Intervals.icu REST API, Python `statistics` module (003-garmin-hrv-status)
- N/A (remote API + in-memory coordinator cache; recorder-backed entity history in Home Assistant) (003-garmin-hrv-status)

## Recent Changes
- 001-wellness-write-services: Added Python 3.13+ (Home Assistant custom integration runtime) + Home Assistant core helpers/config entries/services, aiohttp clien
