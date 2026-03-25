"""Constants for the Intervals.icu integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "intervals_icu"
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_ATHLETE_ID = "athlete_id"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"
CONF_BIRTHDATE = "birthdate"

DEFAULT_ATHLETE_ID = "0"
DEFAULT_SCAN_INTERVAL_MINUTES = 30
MIN_SCAN_INTERVAL_MINUTES = 5

HRV_STATUS_WINDOW_DAYS = 7
HRV_STATUS_MIN_SAMPLES = 6
HRV_BASELINE_WINDOW_DAYS = 56
HRV_BASELINE_MIN_SAMPLES = 18
HRV_BASELINE_LAG_DAYS = 4
HRV_BASELINE_LOWER_PERCENTILE = 40.0
HRV_BASELINE_UPPER_PERCENTILE = 95.0
HRV_LOW_CUTOFF_MIN_DELTA_MS = 2.0
HRV_LOW_CUTOFF_RANGE_FACTOR = 0.25
HRV_STATUS_BOOTSTRAP_DAYS = 120
HRV_POOR_PERSISTENCE_DAYS = 7

DATA_COORDINATOR = "coordinator"

SERVICE_SET_WELLNESS = "set_wellness"

ATTR_DATE = "date"

WRITABLE_WELLNESS_FIELD_MAP: dict[str, str] = {
    "weight": "weight",
    "resting_hr": "restingHR",
    "hrv": "hrv",
    "hrv_sdnn": "hrvSDNN",
    "menstrual_phase": "menstrualPhase",
    "kcal_consumed": "kcalConsumed",
    "sleep_secs": "sleepSecs",
    "sleep_score": "sleepScore",
    "sleep_quality": "sleepQuality",
    "avg_sleeping_hr": "avgSleepingHR",
    "soreness": "soreness",
    "fatigue": "fatigue",
    "stress": "stress",
    "mood": "mood",
    "motivation": "motivation",
    "injury": "injury",
    "sp_o2": "spO2",
    "systolic": "systolic",
    "diastolic": "diastolic",
    "hydration": "hydration",
    "hydration_volume": "hydrationVolume",
    "readiness": "readiness",
    "baevsky_si": "baevskySI",
    "blood_glucose": "bloodGlucose",
    "lactate": "lactate",
    "body_fat": "bodyFat",
    "abdomen": "abdomen",
    "vo2max": "vo2max",
    "comments": "comments",
    "steps": "steps",
    "respiration": "respiration",
    "carbohydrates": "carbohydrates",
    "protein": "protein",
    "fat_total": "fatTotal",
    "temp_weight": "tempWeight",
    "temp_resting_hr": "tempRestingHR",
}
