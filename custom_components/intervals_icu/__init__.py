"""The Intervals.icu integration."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .api import (
    IntervalsIcuApiClient,
    IntervalsIcuApiError,
    IntervalsIcuAuthError,
    IntervalsIcuConnectionError,
)
from .const import (
    ATTR_CARBOHYDRATES,
    ATTR_DATE,
    ATTR_FAT_TOTAL,
    ATTR_HYDRATION_VOLUME,
    ATTR_KCAL_CONSUMED,
    ATTR_PROTEIN,
    ATTR_WEIGHT,
    DATA_COORDINATOR,
    DOMAIN,
    PLATFORMS,
    SERVICE_SET_WELLNESS,
    WRITABLE_WELLNESS_FIELD_MAP,
)
from .coordinator import IntervalsIcuCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_REGISTRATION_KEY = "_services_registered"
SET_WELLNESS_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DATE): cv.string,
        vol.Optional(ATTR_WEIGHT): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional(ATTR_KCAL_CONSUMED): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional(ATTR_CARBOHYDRATES): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional(ATTR_PROTEIN): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional(ATTR_FAT_TOTAL): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional(ATTR_HYDRATION_VOLUME): vol.All(
            vol.Coerce(float), vol.Range(min=0)
        ),
    },
    extra=vol.PREVENT_EXTRA,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Intervals.icu from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    api = IntervalsIcuApiClient(session, entry.data[CONF_API_KEY])
    coordinator = IntervalsIcuCoordinator(hass, entry, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {DATA_COORDINATOR: coordinator}
    if not hass.data[DOMAIN].get(SERVICE_REGISTRATION_KEY):
        async def _handle_set_wellness(call: ServiceCall) -> None:
            await _async_handle_set_wellness(hass, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_WELLNESS,
            _handle_set_wellness,
            schema=SET_WELLNESS_SERVICE_SCHEMA,
        )
        hass.data[DOMAIN][SERVICE_REGISTRATION_KEY] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Intervals.icu config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not _active_coordinators(hass):
            hass.services.async_remove(DOMAIN, SERVICE_SET_WELLNESS)
            hass.data[DOMAIN].pop(SERVICE_REGISTRATION_KEY, None)
    return unload_ok


async def _async_handle_set_wellness(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle wellness write service for the active Intervals.icu entry."""
    coordinator = _single_active_coordinator(hass)
    record_date = _resolve_wellness_date(call.data.get(ATTR_DATE))
    payload = _build_wellness_payload(call.data)

    if not payload:
        raise ServiceValidationError(
            "At least one writable wellness field is required: "
            + ", ".join(sorted(WRITABLE_WELLNESS_FIELD_MAP))
        )

    _LOGGER.debug(
        "Writing wellness fields for athlete %s on %s: %s",
        coordinator.athlete_id,
        record_date,
        ", ".join(sorted(payload)),
    )

    try:
        await coordinator.api.update_wellness_record(
            coordinator.athlete_id, record_date, payload
        )
    except IntervalsIcuAuthError as err:
        raise HomeAssistantError("Intervals.icu authentication failed") from err
    except IntervalsIcuConnectionError as err:
        raise HomeAssistantError("Network error contacting Intervals.icu") from err
    except IntervalsIcuApiError as err:
        raise HomeAssistantError(f"Intervals.icu API error: {err}") from err

    await coordinator.async_request_refresh()
    _LOGGER.debug(
        "Wellness write succeeded for athlete %s on %s",
        coordinator.athlete_id,
        record_date,
    )


def _single_active_coordinator(hass: HomeAssistant) -> IntervalsIcuCoordinator:
    """Return active coordinator, requiring exactly one configured entry."""
    coordinators = _active_coordinators(hass)
    if not coordinators:
        raise HomeAssistantError("No active Intervals.icu entries are available")
    if len(coordinators) > 1:
        raise ServiceValidationError(
            "Multiple Intervals.icu entries configured. "
            "Wellness write service currently supports a single entry."
        )
    return coordinators[0]


def _active_coordinators(hass: HomeAssistant) -> list[IntervalsIcuCoordinator]:
    """Return all coordinators stored for configured entries."""
    domain_data = hass.data.get(DOMAIN, {})
    coordinators: list[IntervalsIcuCoordinator] = []
    for value in domain_data.values():
        if isinstance(value, dict) and DATA_COORDINATOR in value:
            coordinator = value[DATA_COORDINATOR]
            if isinstance(coordinator, IntervalsIcuCoordinator):
                coordinators.append(coordinator)
    return coordinators


def _resolve_wellness_date(raw_date: Any) -> str:
    """Resolve target date from service payload."""
    if raw_date is None or raw_date == "":
        return dt_util.now().date().isoformat()

    if isinstance(raw_date, date):
        return raw_date.isoformat()

    if isinstance(raw_date, str):
        cleaned = raw_date.strip()
        if not cleaned:
            return dt_util.now().date().isoformat()
        try:
            return date.fromisoformat(cleaned).isoformat()
        except ValueError as err:
            raise ServiceValidationError(
                "Invalid date format. Use ISO format YYYY-MM-DD."
            ) from err

    raise ServiceValidationError("Invalid date type. Use ISO date string YYYY-MM-DD.")


def _build_wellness_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Map service payload to Intervals.icu wellness API payload keys."""
    payload: dict[str, Any] = {}
    for local_key, remote_key in WRITABLE_WELLNESS_FIELD_MAP.items():
        if local_key not in data:
            continue
        value = data.get(local_key)
        if value is None:
            continue
        payload[remote_key] = value
    return payload
