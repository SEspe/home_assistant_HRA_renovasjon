# TODO

Enhancements suggested after comparing with [monsivar/HRA_Hentedager](https://github.com/monsivar/HRA_Hentedager).

- [x] **Address picker:** when HRA returns several matches for an address, let the user pick the right property in the config flow instead of taking the first result (`api.py` `search_address` currently uses `data[0]`).
- [ ] **Binary sensor:** add a `binary_sensor` that is `on` when at least one fraction is collected today, with per-fraction attributes.
- [ ] **Lovelace card:** a card that groups fractions sharing the same pickup date and registers itself automatically.
- [ ] **Two devices:** split the fraction/date sensors and the day/calendar entities into two logical devices, as the other repo does.
- [ ] **Translation:** add `translations/nn.json`.
- [ ] **Scan interval:** verify the interval set in the config flow is actually applied to the coordinator (`__init__.py` currently uses `DEFAULT_SCAN_INTERVAL_MINUTES`).
