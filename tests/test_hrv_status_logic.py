"""Unit tests for Garmin-like HRV status derivation using dummy fixtures."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import enum
import importlib
import pathlib
import sys
import types
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "intervals_icu"


def _install_homeassistant_stubs() -> None:
    """Install minimal Home Assistant stubs required by coordinator imports."""
    if "homeassistant" not in sys.modules:
        sys.modules["homeassistant"] = types.ModuleType("homeassistant")

    const_mod = types.ModuleType("homeassistant.const")

    class Platform(str, enum.Enum):
        SENSOR = "sensor"

    const_mod.Platform = Platform
    sys.modules["homeassistant.const"] = const_mod

    config_entries_mod = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        """Minimal ConfigEntry stub for coordinator init."""

        def __init__(self, data: dict, options: dict | None = None) -> None:
            self.data = data
            self.options = options or {}

    config_entries_mod.ConfigEntry = ConfigEntry
    sys.modules["homeassistant.config_entries"] = config_entries_mod

    exceptions_mod = types.ModuleType("homeassistant.exceptions")

    class ConfigEntryAuthFailed(Exception):
        """Stub exception class."""

    exceptions_mod.ConfigEntryAuthFailed = ConfigEntryAuthFailed
    sys.modules["homeassistant.exceptions"] = exceptions_mod

    helpers_mod = types.ModuleType("homeassistant.helpers")
    helpers_mod.__path__ = []
    sys.modules["homeassistant.helpers"] = helpers_mod

    update_mod = types.ModuleType("homeassistant.helpers.update_coordinator")

    class DataUpdateCoordinator:
        """Stub coordinator base class."""

        def __init__(self, *args, **kwargs) -> None:
            self.data = {}

        def __class_getitem__(cls, item):
            return cls

    class UpdateFailed(Exception):
        """Stub update exception class."""

    update_mod.DataUpdateCoordinator = DataUpdateCoordinator
    update_mod.UpdateFailed = UpdateFailed
    sys.modules["homeassistant.helpers.update_coordinator"] = update_mod

    util_mod = types.ModuleType("homeassistant.util")
    util_mod.__path__ = []
    sys.modules["homeassistant.util"] = util_mod

    dt_mod = types.ModuleType("homeassistant.util.dt")
    dt_mod.now = datetime.now
    sys.modules["homeassistant.util.dt"] = dt_mod


def _install_aiohttp_stub() -> None:
    """Install minimal aiohttp stubs required by api module imports."""
    aiohttp_mod = types.ModuleType("aiohttp")

    class BasicAuth:
        def __init__(self, login: str, password: str) -> None:
            self.login = login
            self.password = password

    class ClientTimeout:
        def __init__(self, total: int | float) -> None:
            self.total = total

    class ClientError(Exception):
        """Stub aiohttp client error."""

    class ContentTypeError(Exception):
        """Stub aiohttp content-type error."""

    aiohttp_mod.BasicAuth = BasicAuth
    aiohttp_mod.ClientTimeout = ClientTimeout
    aiohttp_mod.ClientError = ClientError
    aiohttp_mod.ContentTypeError = ContentTypeError
    sys.modules["aiohttp"] = aiohttp_mod


def _install_package_stubs() -> None:
    """Install namespace package stubs to import coordinator without package __init__."""
    custom_components_mod = types.ModuleType("custom_components")
    custom_components_mod.__path__ = [str(REPO_ROOT / "custom_components")]
    sys.modules["custom_components"] = custom_components_mod

    intervals_pkg = types.ModuleType("custom_components.intervals_icu")
    intervals_pkg.__path__ = [str(PACKAGE_ROOT)]
    sys.modules["custom_components.intervals_icu"] = intervals_pkg


def _load_coordinator_module():
    """Load coordinator module with stubs in place."""
    _install_homeassistant_stubs()
    _install_aiohttp_stub()
    _install_package_stubs()

    for module_name in (
        "custom_components.intervals_icu.const",
        "custom_components.intervals_icu.api",
        "custom_components.intervals_icu.coordinator",
    ):
        sys.modules.pop(module_name, None)

    return importlib.import_module("custom_components.intervals_icu.coordinator")


def _build_hrv_rows(
    *,
    start_day: date,
    values: list[float | None],
    updated_suffix: str = "06:00:00Z",
) -> list[dict]:
    """Build wellness fixture rows with sequential local dates."""
    rows: list[dict] = []
    for idx, hrv in enumerate(values):
        day = start_day + timedelta(days=idx)
        rows.append(
            {
                "id": day.isoformat(),
                "hrv": hrv,
                "updated": f"{day.isoformat()}T{updated_suffix}",
            }
        )
    return rows


class _FakeApi:
    """Simple API stub used for coordinator init in pure-logic tests."""


class HrvStatusDerivationTests(unittest.TestCase):
    """Validate Garmin-like HRV status derivation paths with fixed fixtures."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_coordinator_module()
        const_mod = importlib.import_module("custom_components.intervals_icu.const")
        cls.CONF_ATHLETE_ID = const_mod.CONF_ATHLETE_ID
        cls.CONF_SCAN_INTERVAL_MINUTES = const_mod.CONF_SCAN_INTERVAL_MINUTES
        cls.CONF_BIRTHDATE = const_mod.CONF_BIRTHDATE

    def _coordinator(self, *, birthdate_override: str | None = None):
        options = {}
        if birthdate_override is not None:
            options[self.CONF_BIRTHDATE] = birthdate_override

        entry = sys.modules["homeassistant.config_entries"].ConfigEntry(
            data={
                self.CONF_ATHLETE_ID: "0",
                self.CONF_SCAN_INTERVAL_MINUTES: 30,
            },
            options=options,
        )
        return self.mod.IntervalsIcuCoordinator(hass=object(), entry=entry, api=_FakeApi())

    def test_normalize_samples_uses_latest_updated_and_drops_null(self) -> None:
        rows = [
            {"id": "2026-03-01", "hrv": 60, "updated": "2026-03-01T06:00:00Z"},
            {"id": "2026-03-01", "hrv": None, "updated": "2026-03-01T08:00:00Z"},
            {"id": "2026-03-02", "hrv": 55, "updated": "2026-03-02T06:00:00Z"},
        ]

        samples = self.mod._normalize_wellness_hrv_samples(rows)

        self.assertNotIn(date(2026, 3, 1), samples)
        self.assertEqual(samples[date(2026, 3, 2)], 55.0)

    def test_balanced_status_when_value_inside_baseline(self) -> None:
        values = [60] * 30
        rows = _build_hrv_rows(start_day=date(2026, 1, 1), values=values)

        coordinator = self._coordinator()
        payload = coordinator._derive_hrv_status_payload(
            athlete={"sex": "MALE", "icu_date_of_birth": "1990-01-01"},
            wellness_rows=rows,
            source_error=None,
        )

        self.assertEqual(payload["level"], "balanced")
        self.assertAlmostEqual(payload["value"], 60.0)
        self.assertFalse(payload["cache_hit"])

    def test_low_status_when_well_below_baseline(self) -> None:
        values = [65] * 23 + [25] * 7
        rows = _build_hrv_rows(start_day=date(2026, 1, 1), values=values)

        coordinator = self._coordinator()
        payload = coordinator._derive_hrv_status_payload(
            athlete={"sex": "MALE", "icu_date_of_birth": "1990-01-01"},
            wellness_rows=rows,
            source_error=None,
        )

        self.assertEqual(payload["level"], "low")
        self.assertIsNotNone(payload["low_cutoff"])

    def test_poor_status_after_persistence_window(self) -> None:
        # 30 very-low HRV days for a 30-year-old male should trigger poor after persistence.
        values = [12] * 30
        rows = _build_hrv_rows(start_day=date(2026, 1, 1), values=values)

        coordinator = self._coordinator()
        payload = coordinator._derive_hrv_status_payload(
            athlete={"sex": "MALE", "icu_date_of_birth": "1996-01-01"},
            wellness_rows=rows,
            source_error=None,
        )

        self.assertEqual(payload["level"], "poor")
        self.assertTrue(payload["baseline_suppressed"])

    def test_no_status_when_insufficient_history(self) -> None:
        rows = _build_hrv_rows(start_day=date(2026, 3, 1), values=[50, 52, 51, 49, 53])

        coordinator = self._coordinator()
        payload = coordinator._derive_hrv_status_payload(
            athlete={"sex": "FEMALE", "icu_date_of_birth": "1992-03-01"},
            wellness_rows=rows,
            source_error=None,
        )

        self.assertEqual(payload["level"], "no_status")
        self.assertEqual(payload["source_status"], "insufficient_data")

    def test_cache_hit_on_unchanged_source_and_incremental_on_change(self) -> None:
        values = [58] * 30
        rows = _build_hrv_rows(start_day=date(2026, 1, 1), values=values)

        coordinator = self._coordinator()

        first = coordinator._derive_hrv_status_payload(
            athlete={"sex": "MALE", "icu_date_of_birth": "1990-01-01"},
            wellness_rows=rows,
            source_error=None,
        )
        second = coordinator._derive_hrv_status_payload(
            athlete={"sex": "MALE", "icu_date_of_birth": "1990-01-01"},
            wellness_rows=rows,
            source_error=None,
        )

        self.assertFalse(first["cache_hit"])
        self.assertTrue(second["cache_hit"])

        mutated = list(rows)
        mutated[-1] = {
            **mutated[-1],
            "hrv": 40,
            "updated": f"{mutated[-1]['id']}T09:00:00Z",
        }

        third = coordinator._derive_hrv_status_payload(
            athlete={"sex": "MALE", "icu_date_of_birth": "1990-01-01"},
            wellness_rows=mutated,
            source_error=None,
        )

        self.assertFalse(third["cache_hit"])
        self.assertEqual(third["recompute_mode"], "incremental")

    def test_birthdate_option_override_is_used(self) -> None:
        rows = _build_hrv_rows(start_day=date(2026, 1, 1), values=[55] * 30)

        coordinator = self._coordinator(birthdate_override="1988-02-02")
        payload = coordinator._derive_hrv_status_payload(
            athlete={"sex": "MALE", "icu_date_of_birth": "1998-02-02"},
            wellness_rows=rows,
            source_error=None,
        )

        self.assertEqual(payload["birthdate_source"], "option")


if __name__ == "__main__":
    unittest.main()
