"""Shared fixtures for the HRA Renovasjon test suite."""

from datetime import timedelta

import aiohttp.connector
import aiohttp.resolver
import pytest
import pytest_socket
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.hra_renovasjon.api import BASE_URL
from custom_components.hra_renovasjon.const import (
    CONF_ADDRESS,
    CONF_AGREEMENT_GUID,
    DOMAIN,
)

# The HA test plugin disables sockets per-test (plugins.pytest_runtest_setup ->
# pytest_socket.disable_socket). Creating Home Assistant's event loop needs a
# real socket at construction time -- notably the ProactorEventLoop self-pipe on
# Windows, which is AF_INET and so not covered by the plugin's allow_unix_socket
# exception. All HRA API calls go through aioclient_mock, so we neutralize the
# socket block by turning disable_socket into a no-op before any test runs.
pytest_socket.disable_socket = lambda *args, **kwargs: None

# Use aiohttp's threaded resolver instead of aiodns, which HA installs and
# aiohttp then picks by default. Every request goes through aioclient_mock, so
# nothing is ever resolved; the resolver only has to let the mocked
# ClientSession be built and closed cleanly. aiodns does neither here:
# - on Windows it refuses to run on the Proactor event loop at all;
# - on Linux, closing it leaves pycares' `_run_safe_shutdown_loop` thread
#   behind, which the HA plugin's cleanup check (HA 2025.1 harness) reports
#   as a lingering thread and errors the test.
aiohttp.connector.DefaultResolver = aiohttp.resolver.ThreadedResolver

pytest_plugins = ["pytest_homeassistant_custom_component"]

ADDRESS = "Storgata 1, Hønefoss"
AGREEMENT_GUID = "11111111-2222-3333-4444-555555555555"
SEARCH_URL = f"{BASE_URL}/search/address"
SCHEDULE_URL = f"{BASE_URL}/Renovation/UpcomingGarbageDisposals/{AGREEMENT_GUID}"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in every test."""
    yield


def day(days_ahead: int) -> str:
    """An ISO date relative to today in HA's time zone, as the sensors see it."""
    return (dt_util.now().date() + timedelta(days=days_ahead)).isoformat()


def disposal(name: str, days_ahead: int, **extra) -> dict:
    """One entry as the HRA schedule endpoint returns it."""
    return {
        "name": name,
        "date": day(days_ahead),
        "routeName": "Rute 7",
        "frequency": "Hver 2. uke",
        "fractionId": 1,
        "fractionGuid": f"guid-{name.lower()}",
        **extra,
    }


@pytest.fixture
def schedule(hass) -> list[dict]:
    """A schedule in the API's own (unsorted) order.

    Depends on hass so that "today" is taken in the test instance's time zone.
    """
    return [
        disposal("Restavfall", 9),
        disposal("Matavfall", 2),
        disposal("Restavfall", 2),
        disposal("Papir", 16),
    ]


def make_entry(hass, address: str = ADDRESS, guid: str = AGREEMENT_GUID) -> MockConfigEntry:
    """A configured address, added to hass but not set up."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=address,
        unique_id=guid,
        data={CONF_ADDRESS: address, CONF_AGREEMENT_GUID: guid},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def config_entry(hass) -> MockConfigEntry:
    return make_entry(hass)


@pytest.fixture
async def setup_integration(hass, config_entry, aioclient_mock, schedule):
    """Set up the integration against a mocked HRA API."""
    aioclient_mock.get(SCHEDULE_URL, json=schedule)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
