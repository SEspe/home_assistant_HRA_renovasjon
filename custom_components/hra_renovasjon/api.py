import aiohttp
import async_timeout
import logging

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.hra.no"


class HraApiClient:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def search_address(self, query: str) -> str:
        """Return agreementGuid for an address."""
        url = f"{BASE_URL}/search/address?query={query}"

        _LOGGER.debug("HRA: Searching address: %s", url)

        async with async_timeout.timeout(10):
            async with self._session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()

                if not data:
                    raise ValueError("HRA: No address results returned")

                agreement_guid = data[0]["agreementGuid"]
                _LOGGER.debug("HRA: Found agreementGuid: %s", agreement_guid)

                return agreement_guid

    async def get_upcoming_disposals(self, agreement_guid: str) -> list:
        """Return list of upcoming garbage disposals."""
        url = f"{BASE_URL}/Renovation/UpcomingGarbageDisposals/{agreement_guid}"

        _LOGGER.debug("HRA: Fetching schedule: %s", url)

        async with async_timeout.timeout(10):
            async with self._session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()

                _LOGGER.debug("HRA: Received %d schedule entries", len(data))

                return data
