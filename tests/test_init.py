"""Tests for setup, unload, the icon route and the unique-ID migration."""

from aiohttp import web
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.hra_renovasjon import DATA_ICONS_REGISTERED
from custom_components.hra_renovasjon.api import BASE_URL
from custom_components.hra_renovasjon.const import DOMAIN, ICONS_URL_PATH

from .conftest import SCHEDULE_URL, disposal, make_entry

OTHER_GUID = "99999999-8888-7777-6666-555555555555"
OTHER_SCHEDULE_URL = f"{BASE_URL}/Renovation/UpcomingGarbageDisposals/{OTHER_GUID}"


async def test_setup_and_unload(hass, setup_integration):
    entry = setup_integration
    assert entry.state is ConfigEntryState.LOADED
    assert entry.entry_id in hass.data[DOMAIN]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_api_failure_at_startup_retries(hass, config_entry, aioclient_mock):
    aioclient_mock.get(SCHEDULE_URL, status=503)

    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def _setup_two_addresses(hass, aioclient_mock, schedule):
    first = make_entry(hass)
    second = make_entry(hass, address="Kirkegata 2, Jevnaker", guid=OTHER_GUID)
    aioclient_mock.get(SCHEDULE_URL, json=schedule)
    aioclient_mock.get(OTHER_SCHEDULE_URL, json=[disposal("Glass og metall", 4)])

    # Setting up the first entry loads the integration, which sets up every
    # entry of the domain -- the second is set up on the same code path.
    assert await hass.config_entries.async_setup(first.entry_id)
    await hass.async_block_till_done()
    return first, second


async def test_two_addresses_keep_their_own_entities_and_devices(
    hass, aioclient_mock, schedule
):
    """Regression (0.1.14): summary sensors collided and devices were split."""
    first, second = await _setup_two_addresses(hass, aioclient_mock, schedule)
    assert first.state is ConfigEntryState.LOADED
    assert second.state is ConfigEntryState.LOADED

    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)

    for entry, fractions in ((first, 3), (second, 1)):
        entities = er.async_entries_for_config_entry(ent_reg, entry.entry_id)
        # next date + days to go + calendar + one sensor per fraction
        assert len(entities) == 3 + fractions

        devices = dr.async_entries_for_config_entry(dev_reg, entry.entry_id)
        assert len(devices) == 1
        assert devices[0].identifiers == {(DOMAIN, entry.entry_id)}
        assert {e.device_id for e in entities} == {devices[0].id}


async def test_icons_mounted_once_and_served(
    hass, hass_client_no_auth, aioclient_mock, schedule
):
    """Two entries must mount the icon folder once, not once per entry.

    Found 2026-10-12: entries are set up concurrently, and the guard flag was
    only set after the await, so both entries passed it and the folder was
    mounted twice. aiohttp accepts the duplicate silently.
    """
    await _setup_two_addresses(hass, aioclient_mock, schedule)
    assert hass.data[DATA_ICONS_REGISTERED] is True

    mounts = [
        r for r in hass.http.app.router.resources()
        if isinstance(r, web.StaticResource) and r.canonical == ICONS_URL_PATH
    ]
    assert len(mounts) == 1

    client = await hass_client_no_auth()
    resp = await client.get(f"{ICONS_URL_PATH}/waste-new.png")
    assert resp.status == 200
    assert resp.content_type == "image/png"


async def test_legacy_unique_ids_are_migrated(hass, config_entry, aioclient_mock, schedule):
    ent_reg = er.async_get(hass)
    legacy = ent_reg.async_get_or_create(
        "sensor", DOMAIN, "hra_renovasjon_next_date",
        config_entry=config_entry, suggested_object_id="hra_renovasjon_next_date",
    )
    aioclient_mock.get(SCHEDULE_URL, json=schedule)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    new_unique_id = f"{config_entry.entry_id}_next_date"
    migrated = ent_reg.async_get(legacy.entity_id)
    assert migrated.unique_id == new_unique_id
    # Entity ID kept, and no duplicate created under the new unique ID.
    assert ent_reg.async_get_entity_id("sensor", DOMAIN, new_unique_id) == legacy.entity_id
    assert hass.states.get(legacy.entity_id) is not None


async def test_migration_leaves_another_entrys_entity_alone(
    hass, config_entry, aioclient_mock, schedule
):
    other = make_entry(hass, address="Kirkegata 2, Jevnaker", guid=OTHER_GUID)
    ent_reg = er.async_get(hass)
    foreign = ent_reg.async_get_or_create(
        "sensor", DOMAIN, "hra_renovasjon_days_to_go", config_entry=other
    )
    aioclient_mock.get(SCHEDULE_URL, json=schedule)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert ent_reg.async_get(foreign.entity_id).unique_id == "hra_renovasjon_days_to_go"


async def test_migration_skips_when_target_exists(
    hass, config_entry, aioclient_mock, schedule
):
    ent_reg = er.async_get(hass)
    legacy = ent_reg.async_get_or_create(
        "sensor", DOMAIN, "hra_renovasjon_next_date", config_entry=config_entry
    )
    current = ent_reg.async_get_or_create(
        "sensor", DOMAIN, f"{config_entry.entry_id}_next_date", config_entry=config_entry
    )
    aioclient_mock.get(SCHEDULE_URL, json=schedule)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert ent_reg.async_get(legacy.entity_id).unique_id == "hra_renovasjon_next_date"
    assert ent_reg.async_get(current.entity_id).unique_id == f"{config_entry.entry_id}_next_date"


async def test_migration_is_idempotent(hass, config_entry, aioclient_mock, schedule):
    ent_reg = er.async_get(hass)
    legacy = ent_reg.async_get_or_create(
        "sensor", DOMAIN, "hra_renovasjon_days_to_go", config_entry=config_entry
    )
    aioclient_mock.get(SCHEDULE_URL, json=schedule)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert ent_reg.async_get(legacy.entity_id).unique_id == f"{config_entry.entry_id}_days_to_go"
