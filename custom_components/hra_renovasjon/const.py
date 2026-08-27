DOMAIN = "hra_renovasjon"

CONF_ADDRESS = "address"
CONF_AGREEMENT_GUID = "agreement_guid"

PLATFORMS = ["sensor", "calendar"]

# Bundled fraction icons are mounted here at setup, straight from the
# component folder (see _async_register_icons), instead of being copied
# into the user's config/www.
ICONS_URL_PATH = "/hra_renovasjon/icons"


DEFAULT_SCAN_INTERVAL_MINUTES = 60

ATTR_NEXT_DATE = "next_date"
ATTR_NEXT_DATES = "next_dates"
ATTR_ROUTE_NAME = "route_name"
ATTR_FREQUENCY = "frequency"
ATTR_FRACTION_ID = "fraction_id"
ATTR_FRACTION_GUID = "fraction_guid"
ATTR_DAYSNEXT = "days_to_pickup"


def hra_device_info(entry_id: str) -> dict:
    """Device info shared by every entity belonging to one config entry.

    Keyed on the entry id so that each configured address gets its own
    device instead of everything collapsing into one shared device.
    """
    return {
        "identifiers": {(DOMAIN, entry_id)},
        "name": "HRA Renovasjon",
        "manufacturer": "HRA",
        "model": "Renovasjon API",
    }
