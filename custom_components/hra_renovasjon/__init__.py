from __future__ import annotations

import logging
import os
from datetime import timedelta

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HraApiClient
from .const import (
    DOMAIN,
    CONF_AGREEMENT_GUID,
    ICONS_URL_PATH,
    PLATFORMS,
    DEFAULT_SCAN_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)

# Set once the icons have been mounted; aiohttp rejects a duplicate route, so
# the second config entry must not register the same path again.
DATA_ICONS_REGISTERED = f"{DOMAIN}_icons_registered"

# Up to 0.1.13 the two aggregate sensors used a global unique ID, so a second
# configured address collided with the first and its sensors were dropped.
# They are entry-scoped from 0.1.14; map the old IDs to the new suffixes.
LEGACY_UNIQUE_IDS = {
    "hra_renovasjon_next_date": "next_date",
    "hra_renovasjon_days_to_go": "days_to_go",
}


async def _async_register_icons(hass: HomeAssistant) -> None:
    """Serve the bundled fraction icons straight from the component folder.

    Up to 0.1.14 these were copied into the user's config/www on every setup,
    which wrote into the user's own directory and overwrote whatever was
    already there. Mounting them read-only leaves config/www untouched.
    """
    if hass.data.get(DATA_ICONS_REGISTERED):
        return

    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    await hass.http.async_register_static_paths(
        [StaticPathConfig(ICONS_URL_PATH, icons_dir, True)]
    )

    hass.data[DATA_ICONS_REGISTERED] = True
    _LOGGER.debug("HRA: icons served from %s", ICONS_URL_PATH)


@callback
def _async_migrate_unique_ids(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Re-key pre-0.1.14 aggregate sensors so entity IDs and history survive."""
    registry = er.async_get(hass)

    for legacy_unique_id, suffix in LEGACY_UNIQUE_IDS.items():
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, legacy_unique_id)
        if entity_id is None:
            continue

        registry_entry = registry.async_get(entity_id)
        if registry_entry is None or registry_entry.config_entry_id != entry.entry_id:
            # Owned by another config entry, which migrates it on its own setup.
            continue

        new_unique_id = f"{entry.entry_id}_{suffix}"
        if registry.async_get_entity_id("sensor", DOMAIN, new_unique_id) is not None:
            _LOGGER.debug("HRA: %s already migrated, skipping", legacy_unique_id)
            continue

        _LOGGER.debug(
            "HRA: migrating unique_id %s -> %s", legacy_unique_id, new_unique_id
        )
        registry.async_update_entity(entity_id, new_unique_id=new_unique_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HRA Renovasjon from a config entry."""

    await _async_register_icons(hass)

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

    _async_migrate_unique_ids(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
