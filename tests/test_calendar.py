"""Tests for the pickup calendar."""

from datetime import timedelta

from homeassistant.const import STATE_OFF
from homeassistant.util import dt as dt_util

from .conftest import day

CALENDAR = "calendar.hra_renovasjon_kalender"


async def _get_events(hass, days: int) -> list[dict]:
    start = dt_util.start_of_local_day()
    response = await hass.services.async_call(
        "calendar",
        "get_events",
        {"start_date_time": start, "end_date_time": start + timedelta(days=days)},
        target={"entity_id": CALENDAR},
        blocking=True,
        return_response=True,
    )
    return response[CALENDAR]["events"]


async def test_state_shows_next_pickup(hass, setup_integration):
    state = hass.states.get(CALENDAR)
    assert state.state == STATE_OFF  # nothing today
    assert state.attributes["all_day"] is True
    assert state.attributes["start_time"].startswith(day(2))
    assert state.attributes["message"] in ("Matavfall", "Restavfall")


async def test_events_are_sorted_and_windowed(hass, setup_integration):
    events = await _get_events(hass, 10)

    # Papir (+16) is outside the window; the rest come back in date order.
    assert [(e["start"], e["summary"]) for e in events] == [
        (day(2), "Matavfall"),
        (day(2), "Restavfall"),
        (day(9), "Restavfall"),
    ]


async def test_events_are_one_day_all_day_events(hass, setup_integration):
    """CalendarEvent(start=d, end=d) is extended to end the following day by HA."""
    event = (await _get_events(hass, 3))[0]
    assert event["start"] == day(2)
    assert event["end"] == day(3)
