# TODO

Enhancements suggested after comparing with [monsivar/HRA_Hentedager](https://github.com/monsivar/HRA_Hentedager).

- [x] **Address picker:** when HRA returns several matches for an address, let the user pick the right property in the config flow instead of taking the first result (`api.py` `search_address` currently uses `data[0]`).
- [ ] **Binary sensor:** add a `binary_sensor` that is `on` when at least one fraction is collected today, with per-fraction attributes.
  - **Pros:** simple on/off trigger for automations (e.g. notify the evening before, or on bin day); uses data the integration already fetches, so no extra API calls.
  - **Cons:** minimal value, since the next-date and days-to-go sensors already show "collected today" (days to go = 0); a user can build it with a template binary sensor. Needs its own midnight refresh, because the data only updates hourly. Adds a platform, strings in en and nb, tests, and README documentation, and the entity IDs become permanent once used.
  - **Current decision:** parked. Keep in TODO; revisit only if users ask for it.
- [ ] **Lovelace card:** a card that groups fractions sharing the same pickup date and registers itself automatically.
  - **Pros:** groups fractions by pickup date in one line; works without copying YAML from the README; uses the integration's own icons.
  - **Cons:** a JavaScript frontend component that must ship and be rebuilt with each release; breaks on Lovelace or frontend API changes that the Python tests don't catch; auto-registration relies on frontend internals and may still need a manual resource step; overlaps with the existing README cards.
  - **Current decision:** not now. Too much maintenance and fragile for the value. Revisit only if the README cards stop being enough.
- [ ] **Two devices:** split the fraction/date sensors and the day/calendar entities into two logical devices, as the other repo does.
- [ ] **Translation:** add `translations/nn.json`.
- [ ] **Scan interval:** verify the interval set in the config flow is actually applied to the coordinator (`__init__.py` currently uses `DEFAULT_SCAN_INTERVAL_MINUTES`).
