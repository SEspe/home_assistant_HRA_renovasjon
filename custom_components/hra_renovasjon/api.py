import aiohttp
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.hra.no"


class HraApiClient:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def search_addresses(self, query: str) -> list[dict]:
        """Return all address matches as dicts with agreementGuid and name.

        Items without an agreementGuid are skipped, and matches sharing an
        agreementGuid are returned once. Raises ValueError if nothing matches.
        """
        url = f"{BASE_URL}/search/address"

        _LOGGER.debug("HRA: Searching address: %s (query=%s)", url, query)

        async with asyncio.timeout(10):
            async with self._session.get(url, params={"query": query}) as resp:
                resp.raise_for_status()
                data = await resp.json()

        matches: list[dict] = []
        seen: set[str] = set()
        for item in data or []:
            guid = item.get("agreementGuid")
            if not guid or guid in seen:
                continue
            seen.add(guid)
            matches.append(
                {
                    "agreementGuid": guid,
                    "name": item.get("name") or item.get("propertyName") or guid,
                }
            )

        if not matches:
            raise ValueError("HRA: No address results returned")

        _LOGGER.debug("HRA: Found %d address match(es)", len(matches))
        return matches

    async def get_upcoming_disposals(self, agreement_guid: str) -> list:
        """Return list of upcoming garbage disposals."""
        url = f"{BASE_URL}/Renovation/UpcomingGarbageDisposals/{agreement_guid}"

        _LOGGER.debug("HRA: Fetching schedule: %s", url)

        async with asyncio.timeout(10):
            async with self._session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()

                _LOGGER.debug("HRA: Received %d schedule entries", len(data))

                return data
