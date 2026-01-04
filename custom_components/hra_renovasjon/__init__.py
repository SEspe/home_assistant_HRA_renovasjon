from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HraApiClient
from .const import (
    DOMAIN,
    CONF_AGREEMENT_GUID,
    PLATFORMS,
    DEFAULT_SCAN_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HRA Renovasjon from a config entry."""
    session = async_get_clientsession(hass)
    client = HraApiClient(session)

    agreement_guid = entry.data[CONF_AGREEMENT_GUID]

    async def async_update_data():
        try:
            return await client.get_upcoming_disposals(agreement_guid)
        except Exception as err:
            raise UpdateFailed(f"Error fetching data from HRA: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="HRA Renovasjon",
        update_method=async_update_data,
        update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
