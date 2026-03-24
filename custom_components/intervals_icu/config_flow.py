"""Config flow for the Intervals.icu integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    IntervalsIcuApiClient,
    IntervalsIcuApiError,
    IntervalsIcuAuthError,
    IntervalsIcuConnectionError,
)
from .const import (
    CONF_ATHLETE_ID,
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_ATHLETE_ID,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MIN_SCAN_INTERVAL_MINUTES,
)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_ATHLETE_ID, default=DEFAULT_ATHLETE_ID): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_SCAN_INTERVAL_MINUTES, default=DEFAULT_SCAN_INTERVAL_MINUTES
        ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL_MINUTES)),
    }
)


class IntervalsIcuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Intervals.icu."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            athlete_id = str(user_input.get(CONF_ATHLETE_ID, DEFAULT_ATHLETE_ID)).strip()
            if not athlete_id:
                athlete_id = DEFAULT_ATHLETE_ID

            session = async_get_clientsession(self.hass)
            api = IntervalsIcuApiClient(session, api_key)

            try:
                athlete = await api.get_athlete(athlete_id)
            except IntervalsIcuAuthError:
                errors["base"] = "invalid_auth"
            except IntervalsIcuConnectionError:
                errors["base"] = "cannot_connect"
            except IntervalsIcuApiError:
                errors["base"] = "unknown"
            else:
                unique_id = str(athlete.get("id") or athlete_id)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                title = str(athlete.get("name") or f"Intervals.icu ({unique_id})")
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_API_KEY: api_key,
                        CONF_ATHLETE_ID: athlete_id,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        # HA changed options flow construction over time: older cores pass the
        # config entry in the constructor, newer cores inject `self.config_entry`
        # automatically. Support both to avoid 500 errors when opening Configure.
        try:
            return IntervalsIcuOptionsFlow(config_entry)
        except TypeError:
            return IntervalsIcuOptionsFlow()


class IntervalsIcuOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle options for Intervals.icu."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        suggested_options = {
            CONF_SCAN_INTERVAL_MINUTES: self.config_entry.options.get(
                CONF_SCAN_INTERVAL_MINUTES,
                self.config_entry.data.get(
                    CONF_SCAN_INTERVAL_MINUTES,
                    DEFAULT_SCAN_INTERVAL_MINUTES,
                ),
            )
        }

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, suggested_options
            ),
        )
