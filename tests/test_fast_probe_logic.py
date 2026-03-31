"""Unit tests for fast upstream freshness probe helpers."""

from __future__ import annotations

from datetime import datetime
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

    class ClientSession:
        """Stub aiohttp session type for annotations."""

    class ClientTimeout:
        def __init__(self, total: int | float) -> None:
            self.total = total

    class ClientError(Exception):
        """Stub aiohttp client error."""

    class ContentTypeError(Exception):
        """Stub aiohttp content-type error."""

    aiohttp_mod.BasicAuth = BasicAuth
    aiohttp_mod.ClientSession = ClientSession
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


class FastProbeLogicTests(unittest.TestCase):
    """Validate lightweight upstream freshness probe helpers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_coordinator_module()

    def test_activity_probe_state_filters_day_and_keeps_latest_duplicate(self) -> None:
        rows = [
            {
                "id": "i2",
                "start_date_local": "2026-03-31T09:00:00",
                "created": "2026-03-31T09:10:00Z",
                "icu_sync_date": "2026-03-31T09:10:00Z",
            },
            {
                "id": "i1",
                "start_date_local": "2026-03-31T07:00:00",
                "created": "2026-03-31T07:20:00Z",
                "analyzed": "2026-03-31T07:21:00Z",
            },
            {
                "id": "i1",
                "start_date_local": "2026-03-31T07:00:00",
                "created": "2026-03-31T07:30:00Z",
                "analyzed": "2026-03-31T07:31:00Z",
            },
            {
                "id": "old",
                "start_date_local": "2026-03-30T22:45:00",
                "created": "2026-03-31T00:02:00Z",
            },
        ]

        state = self.mod._activity_probe_state(rows, "2026-03-31")

        self.assertEqual(
            state,
            (
                (
                    "i2",
                    "2026-03-31T09:00:00",
                    "2026-03-31T09:10:00Z",
                    "2026-03-31T09:10:00Z",
                    "",
                ),
                (
                    "i1",
                    "2026-03-31T07:00:00",
                    "2026-03-31T07:30:00Z",
                    "",
                    "2026-03-31T07:31:00Z",
                ),
            ),
        )

    def test_wellness_probe_state_uses_latest_updated_today(self) -> None:
        rows = [
            {"id": "2026-03-31", "updated": "2026-03-31T06:00:00Z"},
            {"id": "2026-03-31", "updated": "2026-03-31T07:00:00Z"},
            {"id": "2026-03-30", "updated": "2026-03-30T08:00:00Z"},
        ]

        state = self.mod._wellness_probe_state(rows, "2026-03-31")

        self.assertEqual(state, ("2026-03-31", "2026-03-31T07:00:00Z"))

    def test_remote_probe_state_changes_when_activity_analysis_changes(self) -> None:
        before = self.mod._build_remote_probe_state(
            activity_rows=[
                {
                    "id": "i1",
                    "start_date_local": "2026-03-31T07:00:00",
                    "created": "2026-03-31T07:30:00Z",
                }
            ],
            calculation_date="2026-03-31",
            wellness_rows=[],
        )
        after = self.mod._build_remote_probe_state(
            activity_rows=[
                {
                    "id": "i1",
                    "start_date_local": "2026-03-31T07:00:00",
                    "created": "2026-03-31T07:30:00Z",
                    "analyzed": "2026-03-31T07:33:00Z",
                }
            ],
            calculation_date="2026-03-31",
            wellness_rows=[],
        )

        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
