from __future__ import annotations

import logging
from datetime import datetime, date

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    ICONS_URL_PATH,
    hra_device_info,
    ATTR_NEXT_DATE,
    ATTR_NEXT_DATES,
    ATTR_ROUTE_NAME,
    ATTR_FREQUENCY,
    ATTR_FRACTION_ID,
    ATTR_FRACTION_GUID,
    ATTR_DAYSNEXT,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------------

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    _LOGGER.debug("HRA coordinator.data: %s", coordinator.data)

    # Samlesensorer
    async_add_entities([
        RenovasjonDagerTilNesteSensor(coordinator, entry.entry_id),
        RenovasjonNesteDatoSensor(coordinator, entry.entry_id),
    ])

    # Fraksjonssensorer. HRA kan legge til en fraksjon midt i en sesong, så
    # utvalget leses på nytt ved hver oppdatering i stedet for kun ved oppstart.
    known_fractions: set[str] = set()

    @callback
    def _async_add_new_fractions() -> None:
        data = coordinator.data
        if not isinstance(data, list):
            return

        names = {item["name"] for item in data if item.get("name")}
        new_names = names - known_fractions
        if not new_names:
            return

        known_fractions.update(new_names)
        _LOGGER.debug("HRA: adding fraction sensors: %s", sorted(new_names))

        async_add_entities(
            HraFractionSensor(coordinator, entry.entry_id, name)
            for name in sorted(new_names)
        )

    _async_add_new_fractions()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_fractions))


# ---------------------------------------------------------------------------
# SENSOR: Neste dato på tvers av alle fraksjoner
# ---------------------------------------------------------------------------

class RenovasjonNesteDatoSensor(CoordinatorEntity, SensorEntity):
    """Samlet sensor: neste dato + dager + fraksjoner."""

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = "HRA Renovasjon next date"
        self._attr_unique_id = f"{entry_id}_next_date"

    @property
    def device_info(self):
        return hra_device_info(self._entry_id)

    @property
    def native_value(self):
        data = self.coordinator.data
        if not isinstance(data, list) or not data:
            return None

        today = dt_util.now().date()
        dates = []

        for entry in data:
            dstr = entry.get("date")
            if not dstr:
                continue
            try:
                d = datetime.strptime(dstr, "%Y-%m-%d").date()
            except Exception:
                continue
            if d >= today:
                dates.append(d)

        if not dates:
            return None

        return min(dates).isoformat()

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not isinstance(data, list) or not data:
            return {}

        today = dt_util.now().date()
        next_date_str = self.native_value

        if not next_date_str:
            return {}

        next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()
        dager = (next_date - today).days

        fraksjoner = [
            entry.get("name")
            for entry in data
            if entry.get("date") == next_date_str
        ]

        return {
            "days_to_pickup": dager,
            "fractions": ", ".join(sorted(set(fraksjoner))),
        }


# ---------------------------------------------------------------------------
# SENSOR: Dager til neste tømming
# ---------------------------------------------------------------------------

class RenovasjonDagerTilNesteSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = "HRA Renovasjon days to go"
        self._attr_unique_id = f"{entry_id}_days_to_go"

    @property
    def device_info(self):
        return hra_device_info(self._entry_id)

    @property
    def native_value(self):
        data = self.coordinator.data
        if not isinstance(data, list) or not data:
            return None

        today = dt_util.now().date()
        next_date = None

        for entry in data:
            dstr = entry.get("date")
            if not dstr:
                continue

            try:
                d = datetime.strptime(dstr, "%Y-%m-%d").date()
            except Exception:
                continue

            if d >= today and (next_date is None or d < next_date):
                next_date = d

        if next_date is None:
            return None

        return (next_date - today).days


# ---------------------------------------------------------------------------
# SENSOR: Fraksjonssensorer
# ---------------------------------------------------------------------------

class HraFractionSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str, fraction_name: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._fraction_name = fraction_name
        self._attr_unique_id = f"{entry_id}_{fraction_name.lower().replace(' ', '_')}"
        self._attr_name = fraction_name

    @property
    def device_info(self):
        return hra_device_info(self._entry_id)

    @property
    def native_value(self):
        entries = self._filtered_entries()
        if not entries:
            return None
        return entries[0]["date"]

    @property
    def extra_state_attributes(self):
        entries = self._filtered_entries()
        if not entries:
            return {}

        first = entries[0]
        dates = [e["date"] for e in entries][:5]

        today: date = dt_util.now().date()
        next_date: date | None = first.get("parsed_date")

        if next_date is None:
            try:
                next_date = datetime.strptime(first["date"], "%Y-%m-%d").date()
            except Exception:
                next_date = None

        daysnext = (next_date - today).days if next_date else None
        if daysnext is not None and daysnext < 0:
            daysnext = 0

        return {
            ATTR_NEXT_DATE: first["date"],
            ATTR_NEXT_DATES: dates,
            ATTR_ROUTE_NAME: first.get("routeName"),
            ATTR_FREQUENCY: first.get("frequency"),
            ATTR_FRACTION_ID: first.get("fractionId"),
            ATTR_FRACTION_GUID: first.get("fractionGuid"),
            ATTR_DAYSNEXT: daysnext,
        }

    # ----------------------------------------------------------------------
    # Custom entity pictures
    # ----------------------------------------------------------------------
    @property
    def entity_picture(self):
        name = self._fraction_name.lower()

        if "glass" in name and "metall" in name:
            return f"{ICONS_URL_PATH}/GlassOgMetall.png"
        if "glass" in name:
            return f"{ICONS_URL_PATH}/glass-new.png"
        if "metall" in name or "metal" in name:
            return f"{ICONS_URL_PATH}/metal-new.png"
        if "rest" in name:
            return f"{ICONS_URL_PATH}/waste-new.png"
        if "mat" in name:
            return f"{ICONS_URL_PATH}/organic-new.png"
        if "papir" in name or "kartong" in name:
            return f"{ICONS_URL_PATH}/PapirOgKartong.png"
        if "plast" in name:
            return f"{ICONS_URL_PATH}/plastic-new.png"

        return None

    @property
    def icon(self):
        return self._pick_icon(self._fraction_name)

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------

    def _filtered_entries(self):
        data = self.coordinator.data or []
        today = dt_util.now().date()

        entries = [item for item in data if item["name"] == self._fraction_name]

        def parse_date(dstr: str) -> date | None:
            try:
                return datetime.strptime(dstr, "%Y-%m-%d").date()
            except ValueError:
                _LOGGER.warning("HRA: Invalid date format: %s", dstr)
                return None

        future_entries = []
        for e in entries:
            d = parse_date(e["date"])
            if d is not None and d >= today:
                e_copy = dict(e)
                e_copy["parsed_date"] = d
                future_entries.append(e_copy)

        future_entries.sort(key=lambda x: x["parsed_date"])
        return future_entries

    def _pick_icon(self, fraction_name: str) -> str:
        name = fraction_name.lower()
        if "rest" in name:
            return "mdi:trash-can"
        if "mat" in name:
            return "mdi:food-apple"
        if "papir" in name or "kartong" in name:
            return "mdi:archive"
        if "glass" in name or "metall" in name or "metal" in name:
            return "mdi:glass-fragile"
        if "plast" in name:
            return "mdi:bottle-soda"
        return "mdi:trash-can-outline"
