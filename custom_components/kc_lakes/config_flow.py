"""Config flow for King County Lakes Buoy integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class KCLakesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for King County Lake Buoy Data."""

    VERSION = 1  # Config flow version

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # Input is valid, create the config entry
            _LOGGER.info("Creating config entry for King County Lake Buoy Integration")
            return self.async_create_entry(
                title="King County Lake Buoy",  # Title shown in the UI integrations list
                data={},  # No data needed to store for this simple case
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),  # No fields required
            description_placeholders={
                "api_url": "https://green2.kingcounty.gov/lake-buoy/GenerateMapData.aspx"
            },
        )
