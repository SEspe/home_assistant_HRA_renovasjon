# HRA API

These notes have moved to **[docs/API.md](docs/API.md)**, which documents both
endpoints, their full response fields, the known fractions and the API's
error behaviour.

Quick reference:

- Base address: `https://api.hra.no`
- Address search: `GET /search/address?query=Storgata%201,%203510` — returns `agreementGuid`
- Upcoming collections: `GET /Renovation/UpcomingGarbageDisposals/{agreementGuid}`

Raw captured responses: [docs/GetExamples.txt](docs/GetExamples.txt)
