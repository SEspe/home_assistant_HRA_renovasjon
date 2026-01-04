from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_ADDRESS, CONF_AGREEMENT_GUID
from .api import HraApiClient

_LOGGER = logging.getLogger(__name__)


class HraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for HRA Renovation."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]

            try:
                session = async_get_clientsession(self.hass)
                client = HraApiClient(session)
                agreement_guid = await client.search_address(address)

                await self.async_set_unique_id(agreement_guid)
                self._abort_if_unique_id_configured()

                data = {
                    CONF_ADDRESS: address,
                    CONF_AGREEMENT_GUID: agreement_guid,
                }

                return self.async_create_entry(
                    title=address,
                    data=data,
                )

            except Exception as err:
                _LOGGER.exception("Error validating address with HRA: %s", err)
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS, default=user_input.get(CONF_ADDRESS) if user_input else ""): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
