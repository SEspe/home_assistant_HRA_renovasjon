# HRA API

Reference for the public HRA (Hallingdal og Ringerike Avfallsselskap) endpoints
this integration depends on.

The API is undocumented and unversioned — HRA can change it without notice.
Everything below was verified against the live service on **2026-08-27**; the
"Verified" notes mark what was observed rather than promised.

| | |
|---|---|
| Base URL | `https://api.hra.no` |
| Authentication | None. No API key, token, or cookie is required |
| Transport | HTTPS, `GET` only |
| Response type | `application/json; charset=utf-8` |
| Caching | Server sends `Cache-Control: no-store, no-cache` |
| Coverage | Ringerike, Hole, Jevnaker and neighbouring municipalities |

---

## 1. Address search

Resolves a free-text address to the `agreementGuid` that identifies a waste
collection agreement. This is the only way to obtain the GUID needed by the
schedule endpoint.

```
GET /search/address?query={address}
```

| Parameter | Required | Description |
|---|---|---|
| `query` | yes | Free-text address. The intended form is `street address, postal code` — e.g. `Veienkollen 24, 3517` |

The value must be URL-encoded; addresses contain spaces, commas and Norwegian
characters (`æ`, `ø`, `å`). The integration lets `aiohttp` handle this by
passing `params={"query": query}` rather than building the URL by hand.

### Example

```bash
curl -G --data-urlencode "query=Veienkollen 24, 3517" \
  https://api.hra.no/search/address
```

```json
[
  {
    "propertyGuid": "8ff1ac0e-aa92-465d-bb04-9883dcb20a05",
    "gnrBnrFnrSnr": "3305.49.270.9.0",
    "agreementGuid": "c4ce7f3d-bef2-41c1-9e42-becc8282cfe1",
    "wasteHeroPropertyId": null,
    "propertyName": "Veienkollen 24",
    "municipalityNumber": 3305,
    "municipality": "RINGERIKE",
    "streetNumber": 35100,
    "streetName": "Veienkollen",
    "houseNumber": 24,
    "houseLetter": null,
    "postalPlace": "HØNEFOSS",
    "postalNumber": 3517,
    "name": "Veienkollen 24, 3517 HØNEFOSS"
  }
]
```

### Response fields

| Field | Type | Notes |
|---|---|---|
| `agreementGuid` | string (uuid) | **The only field this integration uses.** Identifies the collection agreement; pass it to the schedule endpoint |
| `propertyGuid` | string (uuid) | Identifies the property itself |
| `wasteHeroPropertyId` | string \| null | Reference to HRA's WasteHero system. `null` for every address observed |
| `gnrBnrFnrSnr` | string | Norwegian cadastral key: `municipality.gnr.bnr.fnr.snr` |
| `propertyName` | string | Street address without postal code |
| `name` | string | Full display address, `street, postcode PLACE` |
| `municipality` / `municipalityNumber` | string / int | e.g. `RINGERIKE` / `3305` |
| `streetName` / `streetNumber` | string / int | Street and HRA's internal street id |
| `houseNumber` / `houseLetter` | int / string \| null | `houseLetter` is `null` unless the address has one (e.g. `12B`) |
| `postalPlace` / `postalNumber` | string / int | e.g. `HØNEFOSS` / `3517` |

### Behaviour to be aware of

- **A vague query returns many matches.** `query=Veienkollen` (street name only)
  returned 23 results. The integration takes `data[0]`, so an under-specified
  address silently resolves to whichever property the API happens to rank
  first — this is why the config flow asks for `street address, postal code`.
- **The postal code is optional in practice.** `Veienkollen 24` alone resolved
  to the same property as `Veienkollen 24, 3517`, but including it is what
  makes the match unambiguous.
- **No match is not an error.** See [Error handling](#error-handling).
- A doubled slash (`https://api.hra.no//search/address`) also works. The older
  notes in this repo use that form; the single slash is correct.

---

## 2. Upcoming collections

Returns the upcoming collection dates for one agreement.

```
GET /Renovation/UpcomingGarbageDisposals/{agreementGuid}
```

| Parameter | Required | Description |
|---|---|---|
| `agreementGuid` | yes | Path segment. The `agreementGuid` from the address search |

### Example

```bash
curl https://api.hra.no/Renovation/UpcomingGarbageDisposals/c4ce7f3d-bef2-41c1-9e42-becc8282cfe1
```

```json
[
  {
    "name": "Restavfall",
    "date": "2026-12-14",
    "fractionId": 9999,
    "fractionGuid": "b4bbf08d-30f0-4024-9f53-e42229ec48a6",
    "route": 14408,
    "routeName": "408 Mat og restavfall",
    "frequency": 4,
    "startDay": 3
  }
]
```

### Response fields

| Field | Type | Notes |
|---|---|---|
| `name` | string | Fraction name in Norwegian. Used as the sensor name and as the key for icon selection |
| `date` | string | Collection date, **`YYYY-MM-DD`**, no time component and no timezone |
| `fractionId` | int | Numeric fraction id, stable per fraction |
| `fractionGuid` | string (uuid) | GUID for the fraction |
| `route` | int | Internal route id. The *same fraction can appear on different routes* across the season |
| `routeName` | string | Human-readable route, e.g. `408 Mat og restavfall` |
| `frequency` | int | Collection interval in weeks. Values `4` and `8` observed |
| `startDay` | int | Weekday index for the route. Only `3` observed |

### Behaviour to be aware of

- **The list is not sorted.** Entries arrive in arbitrary date order and must be
  sorted client-side. Both `sensor.py` and `calendar.py` sort by parsed date.
- **All fractions come back in one flat list**, one object per fraction *per
  date*. A typical address returns ~26 entries covering roughly four months
  ahead.
- **Only future dates are returned** in practice, but the integration still
  filters on `date >= today` rather than trusting that.
- **An unknown or malformed GUID returns `200 []`**, not a 404. See below.

---

## 3. Known fractions

Observed for a Ringerike address. Other municipalities may expose fractions not
listed here — the integration builds its sensors from whatever `name` values
the API actually returns, so a new fraction produces a new sensor without a
code change.

| `name` | `fractionId` | `fractionGuid` |
|---|---|---|
| `Restavfall` | 9999 | `b4bbf08d-30f0-4024-9f53-e42229ec48a6` |
| `Matavfall` | 2110 | `ccdd09f5-3510-43bb-9bb4-2b192230d354` |
| `Papir, papp og kartong` | 2400 | `8998844f-406e-458c-b8da-8e8249f5c321` |
| `Plastemballasje` | 3200 | `03fc89dd-accb-4b4f-a6b0-667438975720` |
| `Glass- og metallemballasje` | 2612 | `2627574c-db98-4d6b-94fd-dfb47a64007d` |

Icons and pictures are chosen from substrings of the lower-cased `name`
(`rest`, `mat`, `papir`/`kartong`, `glass`+`metall`, `plast`), so renamed or
newly added fractions degrade to a default icon instead of failing. See
`_pick_icon()` and `entity_picture` in `custom_components/hra_renovasjon/sensor.py`.

---

## Error handling

**Both endpoints answer `200 OK` for everything.** There is no 4xx/5xx path to
key error handling on — invalid input produces an empty JSON array:

| Request | Response |
|---|---|
| `GET /search/address?query=Zzzzqqq 999` (no match) | `200` `[]` |
| `GET /search/address?query=` (empty) | `200` `[]` |
| `GET /search/address` (parameter missing) | `200` `[]` |
| `GET /Renovation/UpcomingGarbageDisposals/00000000-0000-0000-0000-000000000000` | `200` `[]` |
| `GET /Renovation/UpcomingGarbageDisposals/not-a-guid` | `200` `[]` |

Consequences for a client:

- **An empty result must be treated as failure during address lookup.**
  `HraApiClient.search_address()` raises `ValueError` on an empty list, which
  the config flow surfaces as `cannot_connect`.
- **An empty schedule is indistinguishable from a bad GUID.** If an agreement
  is closed or its GUID stops resolving, the integration receives `[]` and
  every sensor goes to `unknown` rather than `unavailable`. Genuine outages
  (timeouts, DNS failures, 5xx from an intermediary) *do* raise and surface as
  `UpdateFailed`.
- `raise_for_status()` is still called on both requests, to catch failures
  introduced by proxies or a future change in HRA's error handling.

---

## How the integration uses the API

| When | Call | Purpose |
|---|---|---|
| Config flow, on address submit | `/search/address` | Resolve the address to `agreementGuid`, stored in the config entry and used as its `unique_id` |
| Setup, then hourly | `/Renovation/UpcomingGarbageDisposals/{guid}` | Refresh the schedule through a `DataUpdateCoordinator` |

Both calls are wrapped in a 10-second `asyncio.timeout()` and share Home
Assistant's `aiohttp` client session. The polling interval is
`DEFAULT_SCAN_INTERVAL_MINUTES` in `const.py` (60 minutes) — the schedule spans
months, so polling more often only adds load.

The client is `custom_components/hra_renovasjon/api.py`; raw captured responses
are in [`GetExamples.txt`](GetExamples.txt).

---

## Courtesy

This is a small municipal service with no published rate limits or terms of
use. Keep polling infrequent, send a single request per refresh, and do not
enumerate addresses or agreement GUIDs.
