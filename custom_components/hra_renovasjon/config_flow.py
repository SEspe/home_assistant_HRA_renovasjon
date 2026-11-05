from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import DOMAIN, CONF_ADDRESS, CONF_AGREEMENT_GUID
from .api import HraApiClient

_LOGGER = logging.getLogger(__name__)

CONF_PROPERTY = "property"


class HraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for HRA Renovasjon."""

    VERSION = 1

    def __init__(self) -> None:
        self._query: str = ""
        self._matches: list[dict] = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]

            try:
                session = async_get_clientsession(self.hass)
                client = HraApiClient(session)
                matches = await client.search_addresses(address)

                if len(matches) > 1:
                    # Several properties match: let the user pick one.
                    self._query = address
                    self._matches = matches
                    return await self.async_step_select()

                match = matches[0]
                return await self._async_create_for_match(
                    title=address,
                    address=address,
                    agreement_guid=match["agreementGuid"],
                )

            except AbortFlow:
                # _abort_if_unique_id_configured() signals an abort by raising;
                # it must not be swallowed by the generic handler below.
                raise

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

    async def async_step_select(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Let the user pick one property when the search returned several."""
        if user_input is not None:
            guid = user_input[CONF_PROPERTY]
            match = next(m for m in self._matches if m["agreementGuid"] == guid)
            return await self._async_create_for_match(
                title=match["name"],
                address=match["name"],
                agreement_guid=guid,
            )

        options = [
            SelectOptionDict(value=m["agreementGuid"], label=m["name"])
            for m in self._matches
        ]
        data_schema = vol.Schema(
            {
                vol.Required(CONF_PROPERTY): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="select",
            data_schema=data_schema,
            description_placeholders={"query": self._query},
        )

    async def _async_create_for_match(
        self, title: str, address: str, agreement_guid: str
    ) -> FlowResult:
        await self.async_set_unique_id(agreement_guid)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=title,
            data={
                CONF_ADDRESS: address,
                CONF_AGREEMENT_GUID: agreement_guid,
            },
        )
