"""Sensor platform for Intervals.icu."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import IntervalsIcuCoordinator

SOURCE_SUMMARY = "summary"
SOURCE_ACTIVITY_DAILY = "activity_daily"
SOURCE_WELLNESS = "wellness"
SOURCE_WELLNESS_SPORT = "wellness_sport_metrics"
SOURCE_WELLNESS_HRV_STATUS = "wellness_hrv_status"

GENERIC_SPORT_ICON = "mdi:trophy-outline"
SPORT_TYPE_ICONS: dict[str, str] = {
    "ride": "mdi:bike",
    "run": "mdi:run",
    "swim": "mdi:swim",
    "weighttraining": "mdi:weight-lifter",
    "hike": "mdi:hiking",
    "walk": "mdi:walk",
    "alpineski": "mdi:ski",
    "backcountryski": "mdi:ski",
    "badminton": "mdi:badminton",
    "canoeing": "mdi:kayaking",
    "crossfit": "mdi:weight-lifter",
    "ebikeride": "mdi:bike-fast",
    "emountainbikeride": "mdi:bike-pedal-mountain",
    "elliptical": "mdi:run-fast",
    "golf": "mdi:golf",
    "gravelride": "mdi:bike",
    "trackride": "mdi:bike",
    "handcycle": "mdi:bike",
    "highintensityintervaltraining": "mdi:weight-lifter",
    "hockey": "mdi:hockey-puck",
    "iceskate": "mdi:skate",
    "inlineskate": "mdi:rollerblade",
    "kayaking": "mdi:kayaking",
    "kitesurf": "mdi:kitesurfing",
    "mountainbikeride": "mdi:bike-pedal-mountain",
    "nordicski": "mdi:ski-cross-country",
    "openwaterswim": "mdi:swim",
    "padel": "mdi:tennis",
    "pilates": "mdi:meditation",
    "pickleball": "mdi:racquetball",
    "racquetball": "mdi:racquetball",
    "rugby": "mdi:rugby",
    "rockclimbing": "mdi:carabiner",
    "rollerski": "mdi:ski-cross-country",
    "rowing": "mdi:rowing",
    "sail": "mdi:sail-boat",
    "skateboard": "mdi:skateboard",
    "snowboard": "mdi:snowboard",
    "snowshoe": "mdi:snowshoeing",
    "soccer": "mdi:soccer",
    "squash": "mdi:racquetball",
    "stairstepper": "mdi:stairs",
    "standuppaddling": "mdi:kayaking",
    "surfing": "mdi:surfing",
    "tabletennis": "mdi:table-tennis",
    "tennis": "mdi:tennis",
    "trailrun": "mdi:run",
    "transition": "mdi:run-fast",
    "velomobile": "mdi:bike-fast",
    "virtualride": "mdi:bike",
    "virtualrow": "mdi:rowing",
    "virtualrun": "mdi:run",
    "virtualski": "mdi:ski",
    "watersport": "mdi:ski-water",
    "wheelchair": "mdi:human-wheelchair",
    "windsurf": "mdi:surfing",
    "workout": "mdi:dumbbell",
    "yoga": "mdi:yoga",
    "other": GENERIC_SPORT_ICON,
}

INTEGER_DISPLAY_PRECISION_KEYS: set[str] = {
    "summary_fitness",
    "summary_fatigue",
    "summary_form",
    "summary_training_load",
    "summary_eftp",
    "summary_session_rpe",
    "summary_activity_count",
    "summary_total_time",
    "summary_moving_time",
    "summary_elapsed_time",
    "summary_distance",
    "summary_total_elevation_gain",
    "summary_calories",
    "summary_time_in_zones_total",
    "activity_daily_calories",
    "wellness_sleep_secs",
    "wellness_sleep_score",
    "wellness_sleep_quality",
    "wellness_avg_sleeping_hr",
    "wellness_resting_hr",
    "wellness_hrv",
    "wellness_hrv_status",
    "wellness_hrv_baseline_lower",
    "wellness_hrv_baseline_upper",
    "wellness_hrv_low_threshold",
    "wellness_hrv_sdnn",
    "wellness_ctl",
    "wellness_atl",
    "wellness_ctl_load",
    "wellness_atl_load",
    "wellness_fatigue",
    "wellness_stress",
    "wellness_readiness",
    "wellness_soreness",
    "wellness_mood",
    "wellness_motivation",
    "wellness_injury",
    "wellness_steps",
    "wellness_respiration",
    "wellness_spo2",
    "wellness_systolic",
    "wellness_diastolic",
    "wellness_hydration",
    "wellness_hydration_volume",
    "wellness_baevsky_si",
    "wellness_kcal_consumed",
    "wellness_carbohydrates",
    "wellness_protein",
    "wellness_fat_total",
}

ONE_DECIMAL_DISPLAY_PRECISION_KEYS: set[str] = {
    "summary_ramp_rate",
    "summary_weight",
    "wellness_ramp_rate",
    "wellness_weight",
    "wellness_body_fat",
    "wellness_abdomen",
    "wellness_vo2max",
    "wellness_blood_glucose",
    "wellness_lactate",
}

TWO_DECIMAL_DISPLAY_PRECISION_KEYS: set[str] = {
    "summary_eftp_per_kg",
}


@dataclass(frozen=True, kw_only=True)
class IntervalsIcuSensorDescription(SensorEntityDescription):
    """Describe Intervals.icu sensor entity."""

    source: str
    value_key: str
    value_transform: Callable[[Any], Any] | None = None


SUMMARY_SENSOR_DESCRIPTIONS: tuple[IntervalsIcuSensorDescription, ...] = (
    IntervalsIcuSensorDescription(
        key="summary_fitness",
        name="Fitness",
        icon="mdi:heart-pulse",
        source=SOURCE_SUMMARY,
        value_key="fitness",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_fatigue",
        name="Fatigue",
        icon="mdi:run-fast",
        source=SOURCE_SUMMARY,
        value_key="fatigue",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_form",
        name="Form",
        icon="mdi:scale-balance",
        source=SOURCE_SUMMARY,
        value_key="form",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_training_load",
        name="Training Load",
        icon="mdi:chart-timeline-variant",
        source=SOURCE_SUMMARY,
        value_key="training_load",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_ramp_rate",
        name="Ramp Rate",
        icon="mdi:chart-line",
        source=SOURCE_SUMMARY,
        value_key="rampRate",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_eftp",
        name="eFTP",
        icon="mdi:lightning-bolt",
        source=SOURCE_SUMMARY,
        value_key="eftp",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_eftp_per_kg",
        name="eFTP per kg",
        icon="mdi:lightning-bolt-outline",
        source=SOURCE_SUMMARY,
        value_key="eftpPerKg",
        native_unit_of_measurement="W/kg",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_session_rpe",
        name="Session RPE",
        icon="mdi:heart-flash",
        source=SOURCE_SUMMARY,
        value_key="srpe",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_activity_count",
        name="Activity Count",
        icon="mdi:counter",
        source=SOURCE_SUMMARY,
        value_key="count",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_total_time",
        name="Total Time",
        icon="mdi:clock-outline",
        source=SOURCE_SUMMARY,
        value_key="time",
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_moving_time",
        name="Moving Time",
        icon="mdi:clock-fast",
        source=SOURCE_SUMMARY,
        value_key="moving_time",
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_elapsed_time",
        name="Elapsed Time",
        icon="mdi:clock-time-eight-outline",
        source=SOURCE_SUMMARY,
        value_key="elapsed_time",
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_distance",
        name="Distance",
        icon="mdi:map-marker-distance",
        source=SOURCE_SUMMARY,
        value_key="distance",
        native_unit_of_measurement="m",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_total_elevation_gain",
        name="Elevation Gain",
        icon="mdi:terrain",
        source=SOURCE_SUMMARY,
        value_key="total_elevation_gain",
        native_unit_of_measurement="m",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_calories",
        name="Calories",
        icon="mdi:fire",
        source=SOURCE_SUMMARY,
        value_key="calories",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_weight",
        name="Weight",
        icon="mdi:weight-kilogram",
        device_class=SensorDeviceClass.WEIGHT,
        source=SOURCE_SUMMARY,
        value_key="weight",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="summary_time_in_zones_total",
        name="Time In Zones Total",
        icon="mdi:chart-donut",
        source=SOURCE_SUMMARY,
        value_key="timeInZonesTot",
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

DAILY_ACTIVITY_SENSOR_DESCRIPTIONS: tuple[IntervalsIcuSensorDescription, ...] = (
    IntervalsIcuSensorDescription(
        key="activity_daily_calories",
        name="Activity Calories Burned (Daily)",
        icon="mdi:fire",
        source=SOURCE_ACTIVITY_DAILY,
        value_key="calories",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

WELLNESS_SENSOR_DESCRIPTIONS: tuple[IntervalsIcuSensorDescription, ...] = (
    IntervalsIcuSensorDescription(
        key="wellness_sleep_secs",
        name="Sleep Duration",
        icon="mdi:sleep",
        source=SOURCE_WELLNESS,
        value_key="sleepSecs",
        native_unit_of_measurement="s",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_sleep_duration_humanized",
        name="Sleep Duration (Humanized)",
        icon="mdi:sleep",
        source=SOURCE_WELLNESS,
        value_key="sleepSecs",
        value_transform=lambda value: _format_seconds_as_hours_minutes(value),
    ),
    IntervalsIcuSensorDescription(
        key="wellness_sleep_score",
        name="Sleep Score",
        icon="mdi:star-circle-outline",
        source=SOURCE_WELLNESS,
        value_key="sleepScore",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_sleep_quality",
        name="Sleep Quality",
        icon="mdi:star-outline",
        source=SOURCE_WELLNESS,
        value_key="sleepQuality",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_sleep_quality_level",
        name="Sleep Quality (Level)",
        icon="mdi:star-outline",
        source=SOURCE_WELLNESS,
        value_key="sleepQuality",
        value_transform=lambda value: _map_scale(
            value, ("Great", "Good", "Average", "Poor")
        ),
    ),
    IntervalsIcuSensorDescription(
        key="wellness_avg_sleeping_hr",
        name="Average Sleeping Heart Rate",
        icon="mdi:heart-pulse",
        source=SOURCE_WELLNESS,
        value_key="avgSleepingHR",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_resting_hr",
        name="Resting Heart Rate",
        icon="mdi:heart-pulse",
        source=SOURCE_WELLNESS,
        value_key="restingHR",
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_hrv",
        name="Overnight HRV",
        icon="mdi:head-heart-outline",
        source=SOURCE_WELLNESS,
        value_key="hrv",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_hrv_status",
        name="HRV Status (7-Day Avg)",
        icon="mdi:head-heart-outline",
        source=SOURCE_WELLNESS_HRV_STATUS,
        value_key="value",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_hrv_status_level",
        name="HRV Status (Level)",
        icon="mdi:head-heart-outline",
        source=SOURCE_WELLNESS_HRV_STATUS,
        value_key="level",
        value_transform=lambda value: _map_hrv_status_level(value),
    ),
    IntervalsIcuSensorDescription(
        key="wellness_hrv_baseline_lower",
        name="HRV Baseline Lower",
        icon="mdi:chart-bell-curve",
        source=SOURCE_WELLNESS_HRV_STATUS,
        value_key="baseline_low",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_hrv_baseline_upper",
        name="HRV Baseline Upper",
        icon="mdi:chart-bell-curve",
        source=SOURCE_WELLNESS_HRV_STATUS,
        value_key="baseline_high",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_hrv_low_threshold",
        name="HRV Low Threshold (7-Day Avg)",
        icon="mdi:chart-bell-curve-cumulative",
        source=SOURCE_WELLNESS_HRV_STATUS,
        value_key="low_cutoff",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_hrv_sdnn",
        name="HRV SDNN",
        icon="mdi:head-heart-outline",
        source=SOURCE_WELLNESS,
        value_key="hrvSDNN",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_ctl",
        name="Wellness CTL",
        icon="mdi:chart-line",
        source=SOURCE_WELLNESS,
        value_key="ctl",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_atl",
        name="Wellness ATL",
        icon="mdi:chart-line-variant",
        source=SOURCE_WELLNESS,
        value_key="atl",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_ramp_rate",
        name="Wellness Ramp Rate",
        icon="mdi:chart-line",
        source=SOURCE_WELLNESS,
        value_key="rampRate",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_ctl_load",
        name="Wellness CTL Load",
        icon="mdi:chart-areaspline",
        source=SOURCE_WELLNESS,
        value_key="ctlLoad",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_atl_load",
        name="Wellness ATL Load",
        icon="mdi:chart-areaspline",
        source=SOURCE_WELLNESS,
        value_key="atlLoad",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_fatigue",
        name="Wellness Fatigue",
        icon="mdi:run-fast",
        source=SOURCE_WELLNESS,
        value_key="fatigue",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_fatigue_level",
        name="Wellness Fatigue (Level)",
        icon="mdi:run-fast",
        source=SOURCE_WELLNESS,
        value_key="fatigue",
        value_transform=lambda value: _map_scale(
            value, ("Low", "Average", "High", "Extreme")
        ),
    ),
    IntervalsIcuSensorDescription(
        key="wellness_stress",
        name="Stress",
        icon="mdi:emoticon-confused-outline",
        source=SOURCE_WELLNESS,
        value_key="stress",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_stress_level",
        name="Stress (Level)",
        icon="mdi:emoticon-confused-outline",
        source=SOURCE_WELLNESS,
        value_key="stress",
        value_transform=lambda value: _map_scale(
            value, ("Low", "Average", "High", "Extreme")
        ),
    ),
    IntervalsIcuSensorDescription(
        key="wellness_readiness",
        name="Readiness",
        icon="mdi:battery-heart",
        source=SOURCE_WELLNESS,
        value_key="readiness",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_soreness",
        name="Soreness",
        icon="mdi:arm-flex",
        source=SOURCE_WELLNESS,
        value_key="soreness",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_soreness_level",
        name="Soreness (Level)",
        icon="mdi:arm-flex",
        source=SOURCE_WELLNESS,
        value_key="soreness",
        value_transform=lambda value: _map_scale(
            value, ("Low", "Average", "High", "Extreme")
        ),
    ),
    IntervalsIcuSensorDescription(
        key="wellness_mood",
        name="Mood",
        icon="mdi:emoticon-outline",
        source=SOURCE_WELLNESS,
        value_key="mood",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_mood_level",
        name="Mood (Level)",
        icon="mdi:emoticon-outline",
        source=SOURCE_WELLNESS,
        value_key="mood",
        value_transform=lambda value: _map_scale(
            value, ("Great", "Good", "OK", "Grumpy")
        ),
    ),
    IntervalsIcuSensorDescription(
        key="wellness_motivation",
        name="Motivation",
        icon="mdi:rocket-launch-outline",
        source=SOURCE_WELLNESS,
        value_key="motivation",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_motivation_level",
        name="Motivation (Level)",
        icon="mdi:rocket-launch-outline",
        source=SOURCE_WELLNESS,
        value_key="motivation",
        value_transform=lambda value: _map_scale(
            value, ("Extreme", "High", "Average", "Low")
        ),
    ),
    IntervalsIcuSensorDescription(
        key="wellness_injury",
        name="Injury",
        icon="mdi:medical-bag",
        source=SOURCE_WELLNESS,
        value_key="injury",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_injury_level",
        name="Injury (Level)",
        icon="mdi:medical-bag",
        source=SOURCE_WELLNESS,
        value_key="injury",
        value_transform=lambda value: _map_scale(
            value, ("None", "Niggle", "Poor", "Injured")
        ),
    ),
    IntervalsIcuSensorDescription(
        key="wellness_steps",
        name="Steps",
        icon="mdi:walk",
        source=SOURCE_WELLNESS,
        value_key="steps",
        native_unit_of_measurement="steps",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_respiration",
        name="Respiration",
        icon="mdi:lungs",
        source=SOURCE_WELLNESS,
        value_key="respiration",
        native_unit_of_measurement="breaths/min",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_spo2",
        name="SpO2",
        icon="mdi:water-percent",
        source=SOURCE_WELLNESS,
        value_key="spO2",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_systolic",
        name="Systolic Pressure",
        icon="mdi:heart-cog",
        source=SOURCE_WELLNESS,
        value_key="systolic",
        native_unit_of_measurement="mmHg",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_diastolic",
        name="Diastolic Pressure",
        icon="mdi:heart-cog",
        source=SOURCE_WELLNESS,
        value_key="diastolic",
        native_unit_of_measurement="mmHg",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_hydration",
        name="Hydration",
        icon="mdi:cup-water",
        source=SOURCE_WELLNESS,
        value_key="hydration",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_hydration_level",
        name="Hydration (Level)",
        icon="mdi:cup-water",
        source=SOURCE_WELLNESS,
        value_key="hydration",
        value_transform=lambda value: _map_scale(
            value, ("Good", "OK", "Poor", "Bad")
        ),
    ),
    IntervalsIcuSensorDescription(
        key="wellness_hydration_volume",
        name="Hydration Volume",
        icon="mdi:cup-water",
        source=SOURCE_WELLNESS,
        value_key="hydrationVolume",
        native_unit_of_measurement="ml",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_baevsky_si",
        name="Baevsky SI",
        icon="mdi:chart-bell-curve-cumulative",
        source=SOURCE_WELLNESS,
        value_key="baevskySI",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_blood_glucose",
        name="Blood Glucose",
        icon="mdi:needle",
        source=SOURCE_WELLNESS,
        value_key="bloodGlucose",
        native_unit_of_measurement="mmol/L",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_lactate",
        name="Lactate",
        icon="mdi:chart-scatter-plot",
        source=SOURCE_WELLNESS,
        value_key="lactate",
        native_unit_of_measurement="mmol/L",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_body_fat",
        name="Body Fat",
        icon="mdi:human",
        source=SOURCE_WELLNESS,
        value_key="bodyFat",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_abdomen",
        name="Abdomen",
        icon="mdi:ruler",
        source=SOURCE_WELLNESS,
        value_key="abdomen",
        native_unit_of_measurement="cm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_vo2max",
        name="VO2 Max",
        icon="mdi:lungs",
        source=SOURCE_WELLNESS,
        value_key="vo2max",
        native_unit_of_measurement="ml/kg/min",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_kcal_consumed",
        name="Calories Consumed",
        icon="mdi:food-apple",
        source=SOURCE_WELLNESS,
        value_key="kcalConsumed",
        native_unit_of_measurement="kcal",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_carbohydrates",
        name="Carbohydrates",
        icon="mdi:food",
        source=SOURCE_WELLNESS,
        value_key="carbohydrates",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_protein",
        name="Protein",
        icon="mdi:food-steak",
        source=SOURCE_WELLNESS,
        value_key="protein",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_fat_total",
        name="Fat Total",
        icon="mdi:food-drumstick",
        source=SOURCE_WELLNESS,
        value_key="fatTotal",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_weight",
        name="Wellness Weight",
        icon="mdi:weight-kilogram",
        device_class=SensorDeviceClass.WEIGHT,
        source=SOURCE_WELLNESS,
        value_key="weight",
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_menstrual_phase",
        name="Menstrual Phase",
        icon="mdi:calendar-heart",
        source=SOURCE_WELLNESS,
        value_key="menstrualPhase",
    ),
    IntervalsIcuSensorDescription(
        key="wellness_menstrual_phase_predicted",
        name="Menstrual Phase Predicted",
        icon="mdi:calendar-heart",
        source=SOURCE_WELLNESS,
        value_key="menstrualPhasePredicted",
    ),
    IntervalsIcuSensorDescription(
        key="wellness_temp_weight",
        name="Temporary Weight Flag",
        icon="mdi:scale-bathroom",
        source=SOURCE_WELLNESS,
        value_key="tempWeight",
        entity_registry_enabled_default=False,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_temp_resting_hr",
        name="Temporary Resting Heart Rate Flag",
        icon="mdi:heart-cog",
        source=SOURCE_WELLNESS,
        value_key="tempRestingHR",
        entity_registry_enabled_default=False,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_locked",
        name="Wellness Locked",
        icon="mdi:lock-outline",
        source=SOURCE_WELLNESS,
        value_key="locked",
        entity_registry_enabled_default=False,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_comments",
        name="Wellness Comments",
        icon="mdi:comment-text-outline",
        source=SOURCE_WELLNESS,
        value_key="comments",
        entity_registry_enabled_default=False,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_record_date",
        name="Wellness Record Date",
        icon="mdi:calendar",
        source=SOURCE_WELLNESS,
        value_key="id",
        entity_registry_enabled_default=False,
    ),
    IntervalsIcuSensorDescription(
        key="wellness_updated",
        name="Wellness Updated",
        icon="mdi:update",
        source=SOURCE_WELLNESS,
        value_key="updated",
        entity_registry_enabled_default=False,
    ),
)

BASE_SENSOR_DESCRIPTIONS: tuple[IntervalsIcuSensorDescription, ...] = (
    *SUMMARY_SENSOR_DESCRIPTIONS,
    *DAILY_ACTIVITY_SENSOR_DESCRIPTIONS,
    *WELLNESS_SENSOR_DESCRIPTIONS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Intervals.icu sensors from config entry."""
    coordinator: IntervalsIcuCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    descriptions = [
        *BASE_SENSOR_DESCRIPTIONS,
        *_build_wellness_sport_sensor_descriptions(coordinator),
    ]

    async_add_entities(
        IntervalsIcuSensor(coordinator, description) for description in descriptions
    )


class IntervalsIcuSensor(CoordinatorEntity[IntervalsIcuCoordinator], SensorEntity):
    """Intervals.icu sensor entity backed by a shared coordinator."""

    entity_description: IntervalsIcuSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IntervalsIcuCoordinator,
        description: IntervalsIcuSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description

        athlete_data = _data_for_source(coordinator.data, "athlete")
        athlete_id = str(athlete_data.get("id") or coordinator.athlete_id)
        athlete_name = str(athlete_data.get("name") or "Intervals.icu Athlete")

        self._attr_unique_id = f"{athlete_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, athlete_id)},
            manufacturer="Intervals.icu",
            model="API",
            name=athlete_name,
        )
        self._attr_suggested_display_precision = _suggested_display_precision(description)

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        source = _data_for_source(self.coordinator.data, self.entity_description.source)
        value = source.get(self.entity_description.value_key)
        if self.entity_description.value_transform is not None:
            value = self.entity_description.value_transform(value)
        return _normalize_sensor_value(value)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes for source-specific diagnostics."""
        if self.entity_description.source == SOURCE_ACTIVITY_DAILY:
            source = _data_for_source(self.coordinator.data, SOURCE_ACTIVITY_DAILY)
            attrs = _daily_activity_attributes(source)
            return attrs or None

        if self.entity_description.source == SOURCE_WELLNESS_HRV_STATUS:
            source = _data_for_source(self.coordinator.data, SOURCE_WELLNESS_HRV_STATUS)
            attrs = _hrv_status_attributes(source)
            if self.entity_description.key != "wellness_hrv_status":
                attrs.pop("history_28d", None)
            return attrs or None

        return None


def _build_wellness_sport_sensor_descriptions(
    coordinator: IntervalsIcuCoordinator,
) -> tuple[IntervalsIcuSensorDescription, ...]:
    """Build dynamic sensors for wellness sportInfo metrics."""
    metrics = _data_for_source(coordinator.data, SOURCE_WELLNESS_SPORT)
    descriptions: list[IntervalsIcuSensorDescription] = []

    for key, value in sorted(metrics.items()):
        if "__" in key:
            sport_slug, metric_slug = key.split("__", maxsplit=1)
        else:
            sport_slug, metric_slug = "sport", key

        sport_name = sport_slug.replace("_", " ").title()
        metric_name = _format_sport_metric_name(metric_slug)

        descriptions.append(
            IntervalsIcuSensorDescription(
                key=f"wellness_sport_{key}",
                name=f"{sport_name} {metric_name}",
                icon=_sport_type_icon(sport_slug),
                source=SOURCE_WELLNESS_SPORT,
                value_key=key,
                native_unit_of_measurement=_sport_metric_unit(metric_slug),
                state_class=SensorStateClass.MEASUREMENT
                if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)
                else None,
            )
        )

    return tuple(descriptions)


def _format_sport_metric_name(metric_slug: str) -> str:
    """Format flattened sport metric keys to readable names."""
    names = {
        "eftp": "eFTP",
        "w_prime": "W Prime",
        "p_max": "P Max",
    }
    return names.get(metric_slug, metric_slug.replace("_", " ").title())


def _sport_metric_unit(metric_slug: str) -> str | None:
    """Return unit for known sport metrics."""
    if metric_slug in {"eftp", "p_max"}:
        return UnitOfPower.WATT
    if metric_slug == "w_prime":
        return "J"
    return None


def _sport_type_icon(sport_slug: str) -> str:
    """Return icon for the Intervals.icu sport type, with generic fallback."""
    return SPORT_TYPE_ICONS.get(sport_slug, GENERIC_SPORT_ICON)


def _suggested_display_precision(
    description: IntervalsIcuSensorDescription,
) -> int | None:
    """Return display precision hint for numeric sensors."""
    key = description.key

    if description.state_class is None:
        return None

    if key.startswith("wellness_sport_"):
        sport_key = key.removeprefix("wellness_sport_")
        metric_slug = sport_key.split("__")[-1]
        return _sport_metric_display_precision(metric_slug)

    if key in INTEGER_DISPLAY_PRECISION_KEYS:
        return 0

    if key in ONE_DECIMAL_DISPLAY_PRECISION_KEYS:
        return 1

    if key in TWO_DECIMAL_DISPLAY_PRECISION_KEYS:
        return 2

    return None


def _sport_metric_display_precision(metric_slug: str) -> int:
    """Return display precision for known sportInfo metrics."""
    if metric_slug in {"eftp", "p_max", "w_prime"}:
        return 0
    return 1


def _data_for_source(data: dict[str, Any], source: str) -> dict[str, Any]:
    """Safely return source payload dictionary."""
    value = data.get(source)
    return value if isinstance(value, dict) else {}


def _normalize_sensor_value(value: Any) -> Any:
    """Normalize API values to HA SensorEntity supported scalar types."""
    if value is None:
        return None

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (str, int, float, date, datetime, Decimal)):
        return value

    return None


def _format_seconds_as_hours_minutes(value: Any) -> str | None:
    """Format duration seconds as a compact '<hours>h <minutes>m' string."""
    if value is None or isinstance(value, bool):
        return None

    try:
        total_seconds = int(value)
    except (TypeError, ValueError):
        return None

    if total_seconds < 0:
        return None

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}h {minutes}m"


def _daily_activity_attributes(source: dict[str, Any]) -> dict[str, Any]:
    """Return curated attributes for day-level activity calories."""
    attrs: dict[str, Any] = {}
    for key in (
        "calculation_date",
        "source_status",
        "activity_count_total",
        "activity_count_with_calories",
        "activity_count_missing_calories",
        "error",
    ):
        value = source.get(key)
        if value is not None:
            attrs[key] = value
    return attrs


def _hrv_status_attributes(source: dict[str, Any]) -> dict[str, Any]:
    """Return curated attributes for HRV status and baseline entities."""
    attrs: dict[str, Any] = {}
    for key in (
        "level",
        "calculation_date",
        "source_status",
        "sample_count_7d",
        "sample_count_baseline",
        "sample_count_21d",
        "age_norm_lower_bound",
        "status_window_days",
        "baseline_window_days",
        "baseline_lag_days",
        "baseline_lower_percentile",
        "baseline_upper_percentile",
        "poor_persistence_days",
        "baseline_suppressed",
        "cache_hit",
        "birthdate_source",
        "sex",
        "recompute_mode",
        "points_total",
        "history_28d",
        "error",
    ):
        value = source.get(key)
        if value is not None:
            attrs[key] = value
    return attrs


def _map_hrv_status_level(value: Any) -> str | None:
    """Map internal HRV status codes to Garmin-style labels."""
    if value is None:
        return None
    if not isinstance(value, str):
        return None

    cleaned = value.strip().lower()
    labels = {
        "balanced": "Balanced",
        "unbalanced": "Unbalanced",
        "low": "Low",
        "poor": "Poor",
        "no_status": "No status",
        "no status": "No status",
    }
    return labels.get(cleaned)


def _map_scale(value: Any, labels: tuple[str, ...]) -> str | None:
    """Map numeric scale values used by Intervals.icu to human-friendly labels."""
    if value is None or isinstance(value, bool):
        return None

    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None

    # Intervals fields may be 1-based (1..N). Some integrations emit 0-based values.
    if 1 <= numeric <= len(labels):
        return labels[numeric - 1]
    if 0 <= numeric < len(labels):
        return labels[numeric]
    return None
