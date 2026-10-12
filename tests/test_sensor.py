"""Tests for the summary and per-fraction sensors."""

import pytest
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers import entity_registry as er

from custom_components.hra_renovasjon.const import DOMAIN, ICONS_URL_PATH
from custom_components.hra_renovasjon.sensor import HraFractionSensor

from .conftest import SCHEDULE_URL, day, disposal

NEXT_DATE = "sensor.hra_renovasjon_next_date"
DAYS_TO_GO = "sensor.hra_renovasjon_days_to_go"
RESTAVFALL = "sensor.hra_renovasjon_restavfall"


async def _refresh(hass, entry, aioclient_mock, **response):
    """Serve a new API response and run one coordinator update."""
    aioclient_mock.clear_requests()
    aioclient_mock.get(SCHEDULE_URL, **response)
    await hass.data[DOMAIN][entry.entry_id]["coordinator"].async_refresh()
    await hass.async_block_till_done()


async def test_summary_sensors(hass, setup_integration):
    state = hass.states.get(NEXT_DATE)
    assert state.state == day(2)
    assert state.attributes["days_to_pickup"] == 2
    assert state.attributes["fractions"] == "Matavfall, Restavfall"

    assert hass.states.get(DAYS_TO_GO).state == "2"


async def test_fraction_sensor_picks_earliest_date(hass, setup_integration):
    """The API list is unsorted: Restavfall +9 comes before Restavfall +2."""
    state = hass.states.get(RESTAVFALL)
    assert state.state == day(2)
    assert state.attributes["next_date"] == day(2)
    assert state.attributes["next_dates"] == [day(2), day(9)]
    assert state.attributes["days_to_pickup"] == 2
    assert state.attributes["route_name"] == "Rute 7"
    assert state.attributes["frequency"] == "Hver 2. uke"
    assert state.attributes["fraction_guid"] == "guid-restavfall"
    assert state.attributes["entity_picture"] == f"{ICONS_URL_PATH}/waste-new.png"
    assert state.attributes["icon"] == "mdi:trash-can"


async def test_fraction_sensor_unique_ids_are_entry_scoped(hass, setup_integration):
    entry = setup_integration
    ent_reg = er.async_get(hass)
    assert ent_reg.async_get(RESTAVFALL).unique_id == f"{entry.entry_id}_restavfall"
    assert ent_reg.async_get(NEXT_DATE).unique_id == f"{entry.entry_id}_next_date"
    assert ent_reg.async_get(DAYS_TO_GO).unique_id == f"{entry.entry_id}_days_to_go"


async def test_past_dates_are_ignored(hass, setup_integration, aioclient_mock):
    await _refresh(
        hass, setup_integration, aioclient_mock,
        json=[disposal("Restavfall", -3), disposal("Restavfall", 5), disposal("Papir", 0)],
    )

    assert hass.states.get(RESTAVFALL).state == day(5)
    assert hass.states.get(NEXT_DATE).state == day(0)
    assert hass.states.get(DAYS_TO_GO).state == "0"


async def test_new_fraction_appears_without_reload(hass, setup_integration, aioclient_mock, schedule):
    """Regression (0.1.15): the fraction set used to be frozen at setup."""
    assert hass.states.get("sensor.hra_renovasjon_plast") is None

    await _refresh(
        hass, setup_integration, aioclient_mock,
        json=[*schedule, disposal("Plast", 6)],
    )

    state = hass.states.get("sensor.hra_renovasjon_plast")
    assert state.state == day(6)
    assert state.attributes["entity_picture"] == f"{ICONS_URL_PATH}/plastic-new.png"


async def test_repeated_updates_do_not_duplicate(hass, setup_integration, aioclient_mock, schedule):
    for _ in range(3):
        await _refresh(hass, setup_integration, aioclient_mock, json=schedule)

    entities = er.async_entries_for_config_entry(
        er.async_get(hass), setup_integration.entry_id
    )
    # next date + days to go + calendar + Restavfall, Matavfall, Papir
    assert len(entities) == 6


async def test_vanished_fraction_keeps_its_entity(hass, setup_integration, aioclient_mock):
    await _refresh(
        hass, setup_integration, aioclient_mock, json=[disposal("Papir", 3)]
    )

    assert hass.states.get(RESTAVFALL).state == STATE_UNKNOWN
    assert hass.states.get("sensor.hra_renovasjon_papir").state == day(3)


async def test_empty_schedule(hass, setup_integration, aioclient_mock):
    """The API answers 200 [] for a dead agreement GUID: unknown, not unavailable."""
    await _refresh(hass, setup_integration, aioclient_mock, json=[])

    assert hass.states.get(NEXT_DATE).state == STATE_UNKNOWN
    assert hass.states.get(DAYS_TO_GO).state == STATE_UNKNOWN
    assert hass.states.get(RESTAVFALL).state == STATE_UNKNOWN


async def test_entries_without_a_name_are_skipped(hass, setup_integration, aioclient_mock, schedule):
    await _refresh(
        hass, setup_integration, aioclient_mock,
        json=[*schedule, {"date": day(1)}, {"name": "", "date": day(1)}],
    )

    entities = er.async_entries_for_config_entry(
        er.async_get(hass), setup_integration.entry_id
    )
    assert len(entities) == 6


async def test_api_failure_makes_sensors_unavailable(hass, setup_integration, aioclient_mock):
    await _refresh(hass, setup_integration, aioclient_mock, status=500)

    assert hass.states.get(NEXT_DATE).state == STATE_UNAVAILABLE
    assert hass.states.get(RESTAVFALL).state == STATE_UNAVAILABLE


@pytest.mark.parametrize(
    ("fraction", "picture", "icon"),
    [
        ("Glass og metall", "GlassOgMetall.png", "mdi:glass-fragile"),
        ("Glass", "glass-new.png", "mdi:glass-fragile"),
        ("Metall", "metal-new.png", "mdi:glass-fragile"),
        ("Restavfall", "waste-new.png", "mdi:trash-can"),
        ("Matavfall", "organic-new.png", "mdi:food-apple"),
        ("Papir og kartong", "PapirOgKartong.png", "mdi:archive"),
        ("Plastemballasje", "plastic-new.png", "mdi:bottle-soda"),
        ("Farlig avfall", None, "mdi:trash-can-outline"),
    ],
)
def test_pictures_and_icons(fraction, picture, icon):
    sensor = object.__new__(HraFractionSensor)
    sensor._fraction_name = fraction

    expected = f"{ICONS_URL_PATH}/{picture}" if picture else None
    assert sensor.entity_picture == expected
    assert sensor.icon == icon
