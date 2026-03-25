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

SERVICE_SET_WELLNESS = "set_wellness"

ATTR_DATE = "date"
ATTR_WEIGHT = "weight"
ATTR_KCAL_CONSUMED = "kcal_consumed"
ATTR_CARBOHYDRATES = "carbohydrates"
ATTR_PROTEIN = "protein"
ATTR_FAT_TOTAL = "fat_total"
ATTR_HYDRATION_VOLUME = "hydration_volume"

WRITABLE_WELLNESS_FIELD_MAP: dict[str, str] = {
    ATTR_WEIGHT: "weight",
    ATTR_KCAL_CONSUMED: "kcalConsumed",
    ATTR_CARBOHYDRATES: "carbohydrates",
    ATTR_PROTEIN: "protein",
    ATTR_FAT_TOTAL: "fatTotal",
    ATTR_HYDRATION_VOLUME: "hydrationVolume",
}
