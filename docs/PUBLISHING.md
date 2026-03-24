# Publishing Checklist

## 1. GitHub repository metadata

Set these in GitHub repository settings:

- Description: one-line summary of this integration
- Topics:
  - `home-assistant`
  - `home-assistant-integration`
  - `hacs`
  - `hacs-integration`
  - `intervals-icu`

## 2. Required files (already included)

- `custom_components/intervals_icu/manifest.json`
  - includes: `domain`, `documentation`, `issue_tracker`, `codeowners`, `name`, `version`
- `hacs.json` in repository root
- `README.md`
- brand assets in `custom_components/intervals_icu/brand/`
  - includes at least `icon.png`

## 3. CI checks

GitHub Actions included:

- `.github/workflows/hacs.yml` (HACS validation)
- `.github/workflows/hassfest.yml` (Home Assistant Hassfest validation)
- `.github/workflows/ci.yml` (basic Python compile check)

All should pass on `main` before release.

## 4. Release strategy

For HACS, publishing GitHub Releases is recommended.

Recommended release process:

1. Bump `manifest.json` version.
2. Commit and merge to `main`.
3. Create Git tag and GitHub Release (for example `v0.1.0`).

## 5. HACS distribution

### As custom repository (immediate)

Users add this repository in HACS as type `Integration`.

My Home Assistant link pattern:

`https://my.home-assistant.io/redirect/hacs_repository/?owner=<owner>&repository=<repo>&category=integration`

### As HACS default store (optional)

Follow HACS docs for default inclusion:

- https://www.hacs.xyz/docs/publish/include/

## References

- HACS publish general: https://www.hacs.xyz/docs/publish/start/
- HACS integration requirements: https://www.hacs.xyz/docs/publish/integration/
- HACS action docs: https://www.hacs.xyz/docs/publish/action/
