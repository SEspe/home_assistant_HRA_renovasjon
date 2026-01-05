
from __future__ import annotations

import logging
from datetime import datetime, date

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    ATTR_NEXT_DATE,
    ATTR_NEXT_DATES,
    ATTR_ROUTE_NAME,
    ATTR_FREQUENCY,
    ATTR_FRACTION_ID,
    ATTR_FRACTION_GUID,
    ATTR_DAYSNEXT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HRA sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    # Group schedule entries by 'name' (Restavfall, Matavfall, etc.)
    fraction_names = set(item["name"] for item in coordinator.data)

    entities = []
    for fraction_name in sorted(fraction_names):
        entities.append(HraFractionSensor(coordinator, entry.entry_id, fraction_name))

    async_add_entities(entities)


class HraFractionSensor(CoordinatorEntity, SensorEntity):
    """Sensor for one waste fraction (e.g. Restavfall)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str, fraction_name: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._fraction_name = fraction_name
        self._attr_unique_id = f"{entry_id}_{fraction_name.lower().replace(' ', '_')}"
        self._attr_name = fraction_name


    @property
    def native_value(self):
        """Return the next pickup date as the state (ISO date string)."""
        entries = self._filtered_entries()
        if not entries:
            return None
        next_entry = entries[0]
        return next_entry["date"]  # keep as string (e.g., "2026-01-15")

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        entries = self._filtered_entries()
        if not entries:
            return {}

        # Already sorted by parsed_date ascending
        first = entries[0]
        dates = [e["date"] for e in entries][:5]

        # Compute DaysNext (days between today and Next_Date)
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


        attrs = {
            ATTR_NEXT_DATE: first["date"],
            ATTR_NEXT_DATES: dates,
            ATTR_ROUTE_NAME: first.get("routeName"),
            ATTR_FREQUENCY: first.get("frequency"),
            ATTR_FRACTION_ID: first.get("fractionId"),
            ATTR_FRACTION_GUID: first.get("fractionGuid"),
            ATTR_DAYSNEXT: daysnext,
        }
        return attrs

    @property
    def icon(self):
        """Return an icon based on fraction name (fallback if no picture is used)."""
        return self._pick_icon(self._fraction_name)

    def _filtered_entries(self):
        """Return all schedule entries for this fraction, in the future, sorted by date."""
        data = self.coordinator.data or []
        today = dt_util.now().date()

        # Only entries for this fraction
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

        # Sort by the parsed date
        future_entries.sort(key=lambda x: x["parsed_date"])
        return future_entries

    # --- helpers -------------------------------------------------------------

    def _pick_icon(self, fraction_name: str) -> str:
        """Pick an MDI icon for the fraction (used as fallback when no picture)."""
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
