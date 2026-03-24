"""Constants for the Intervals.icu integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "intervals_icu"
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_ATHLETE_ID = "athlete_id"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"

DEFAULT_ATHLETE_ID = "0"
DEFAULT_SCAN_INTERVAL_MINUTES = 30
MIN_SCAN_INTERVAL_MINUTES = 5

DATA_COORDINATOR = "coordinator"
