import logging
from datetime import datetime, date
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up calendar entity from config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data["coordinator"]
    client = entry_data["client"]

    async_add_entities([
        HraRenovasjonCalendar(
            name="HRA Renovasjon Kalender",
            config_entry=config_entry,
            coordinator=coordinator,
            client=client,
        )
    ])


class HraRenovasjonCalendar(CalendarEntity):
    """Calendar entity for HRA Renovasjon."""

    def __init__(self, name, config_entry, coordinator, client):
        self._name = name
        self._config_entry = config_entry
        self._coordinator = coordinator
        self._client = client
        self._events: list[CalendarEvent] = []

    @property
    def should_poll(self) -> bool:
        return True

    async def async_added_to_hass(self):
        await self.async_update()

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"{self._config_entry.entry_id}_calendar"

    @property
    def device_info(self):
        """Register device so HA can show logo.png."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "HRA Renovasjon",
            "manufacturer": "HRA",
            "model": "Renovasjonskalender",
        }

    @property
    def event(self):
        if not self._events:
            return None
        return self._events[0]

    async def async_get_events(self, hass, start_date, end_date):
        """Return events between two dates."""
        start = start_date.date() if isinstance(start_date, datetime) else start_date
        end = end_date.date() if isinstance(end_date, datetime) else end_date

        return [
            event for event in self._events
            if isinstance(event.start, date) and start <= event.start <= end
        ]

    async def async_update(self):
        """Fetch events from coordinator data."""
        data = self._coordinator.data
        _LOGGER.debug("Coordinator data: %s", data)

        events: list[CalendarEvent] = []

        for entry in data:
            fraction_name = entry["name"]
            pickup_date = entry["date"]

            d = datetime.strptime(pickup_date, "%Y-%m-%d").date()

            events.append(CalendarEvent(
                summary=fraction_name,
                start=d,
                end=d
            ))

        events.sort(key=lambda e: e.start)
        self._events = events
