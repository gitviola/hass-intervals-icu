"""Sensor platform for Intervals.icu."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

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
SOURCE_WELLNESS = "wellness"
SOURCE_WELLNESS_SPORT = "wellness_sport_metrics"


@dataclass(frozen=True, kw_only=True)
class IntervalsIcuSensorDescription(SensorEntityDescription):
    """Describe Intervals.icu sensor entity."""

    source: str
    value_key: str


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
        name="HRV",
        icon="mdi:head-heart-outline",
        source=SOURCE_WELLNESS,
        value_key="hrv",
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
        key="wellness_stress",
        name="Stress",
        icon="mdi:emoticon-confused-outline",
        source=SOURCE_WELLNESS,
        value_key="stress",
        state_class=SensorStateClass.MEASUREMENT,
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
        key="wellness_mood",
        name="Mood",
        icon="mdi:emoticon-outline",
        source=SOURCE_WELLNESS,
        value_key="mood",
        state_class=SensorStateClass.MEASUREMENT,
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
        key="wellness_injury",
        name="Injury",
        icon="mdi:medical-bag",
        source=SOURCE_WELLNESS,
        value_key="injury",
        state_class=SensorStateClass.MEASUREMENT,
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

    @property
    def native_value(self) -> Any:
        """Return the current sensor value."""
        source = _data_for_source(self.coordinator.data, self.entity_description.source)
        value = source.get(self.entity_description.value_key)
        return _normalize_sensor_value(value)


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
                icon=_sport_metric_icon(metric_slug),
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


def _sport_metric_icon(metric_slug: str) -> str:
    """Return icon for known sport metrics."""
    if metric_slug in {"eftp", "p_max"}:
        return "mdi:lightning-bolt"
    if metric_slug == "w_prime":
        return "mdi:battery-high"
    return "mdi:chart-line"


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
