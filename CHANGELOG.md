# Changelog  
Alle vesentlige endringer i **HRA Renovasjon** dokumenteres her.

Formatet følger prinsippene fra [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
og versjonering følger [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.15] – 2026-08-27
### Changed
- Ikonene serveres nå direkte fra komponentmappen via en statisk sti (`/hra_renovasjon/icons`) i stedet for å kopieres inn i `config/www` ved hver oppstart. Integrasjonen skriver ikke lenger i brukerens egen `www`-mappe, og overskriver ikke filer som allerede ligger der
- Fraksjonssensorene bygges nå på nytt ved hver oppdatering fra HRA. Legger HRA til en fraksjon midt i sesongen, dukker sensoren opp av seg selv i stedet for å kreve en omstart av integrasjonen

### Added
- `docs/API.md`: dokumentasjon av HRA-API-et — begge endepunktene, alle responsfelter, kjente fraksjoner med `fractionId`/`fractionGuid`, og API-ets feilhåndtering (det svarer `200 []` på ugyldige forespørsler i stedet for en feilkode)

### Requirements
- Krever nå Home Assistant **2024.7** eller nyere (`async_register_static_paths`). Minimumsversjonen er deklarert i `hacs.json`, slik at HACS ikke tilbyr oppdateringen til eldre installasjoner
- `http` er lagt til som avhengighet i `manifest.json`

### Migrering
- Oppgraderingen er automatisk. `entity_picture` peker nå på `/hra_renovasjon/icons/...`; ingen konfigurasjon må endres
- Mappen `config/www/hra_renovasjon` brukes ikke lenger og kan slettes manuelt

---

## [0.1.14] – 2026-08-27
### Fixed
- Duplikat adresse ga feilmeldingen «cannot_connect» i stedet for `already_configured`. `_abort_if_unique_id_configured()` signaliserer avbrudd ved å kaste `AbortFlow`, som ble slukt av den generelle `except Exception`-blokken i config flow
- Samlesensorene (`next date` og `days to go`) brukte globale unike ID-er. Ved en andre konfigurert adresse kolliderte de, og Home Assistant droppet sensorene til adresse nummer to («Platform hra_renovasjon does not generate unique IDs»). ID-ene er nå knyttet til config entry
- Alle entiteter fra samme config entry havner nå på én device. Kalenderen registrerte seg under `(DOMAIN, entry_id)` mens sensorene brukte en fast `(DOMAIN, "hra_renovasjon_device")`, noe som ga to separate devices per adresse — og én delt device på tvers av adresser

### Changed
- Felles `hra_device_info(entry_id)` i `const.py` erstatter device_info-funksjonen i `sensor.py` og den inline-definerte i `calendar.py`

### Migrering
- Eksisterende `sensor.hra_renovasjon_next_date` og `sensor.hra_renovasjon_days_to_go` får nye unike ID-er automatisk ved oppstart. Entitets-ID-er, historikk og automasjoner beholdes, og ingen manuelle steg er nødvendig
- Sensorene flyttes til en ny device. Den gamle, nå tomme «HRA Renovasjon»-devicen kan slettes manuelt hvis den blir liggende igjen

---

## [0.1.13] – 2026-07-02
### Fixed
- Fjernet ugyldig `release_tag`-nøkkel fra `hacs.json`, siste treff fra `hacs/action`-valideringen; CI er nå grønn

---

## [0.1.12] – 2026-07-02
### Fixed
- Sortert nøklene i `manifest.json` alfabetisk (etter `domain`/`name`), som `hassfest` krever
- Fjernet ugyldig `image`-nøkkel fra `hacs.json`, avdekket av `hacs/action`

---

## [0.1.11] – 2026-07-02
### Fixed
- Fjernet `platforms`-nøkkelen fra `manifest.json` og `domains`-nøkkelen fra `hacs.json` — begge er ugyldige nøkler avdekket av den nye CI-valideringen (`hassfest` og `hacs/action`)

---

## [0.1.10] – 2026-07-02
### Fixed
- Fjernet `data.py`, en ubrukt og korrupt fil fra en tidligere arkitektur (feil imports, ødelagt indentering)
- `RenovasjonNesteDatoSensor` og `RenovasjonDagerTilNesteSensor` arver nå `CoordinatorEntity`, slik at de faktisk oppdateres når coordinator henter nye data (de sto tidligere fast etter oppstart)
- Kalenderentiteten bruker nå `CoordinatorEntity` i stedet for egen polling-løkke
- Adressesøk URL-encodes nå korrekt (`aiohttp` `params=`), slik at adresser med mellomrom, komma eller æøå håndteres riktig
- Oversettelsesfilene (`en.json`, `nb.json`) samsvarte ikke lenger med config flow (viste felter/valg fra en tidligere integrasjon); ryddet opp slik at de matcher det faktiske adressefeltet og feilmeldingen `cannot_connect`
- Rettet feil loggernavn i README (`hra_renovation` → `hra_renovasjon`) og fjernet utdatert beskrivelse av et "velg fraksjoner"-steg som ikke lenger finnes

### Changed
- Byttet fra tredjeparts `async_timeout`-pakken til innebygd `asyncio.timeout()`

---

## [0.1.6] – 2026-03-21
### Added
- Nye ikonfiler for alle fraksjoner (PNG) i `/www/hra_renovasjon/`
- `entity_picture`‑støtte for fraksjonssensorer
- Ikonmapping for:
  - Restavfall  
  - Matavfall  
  - Plastemballasje  
  - Papir, papp og kartong  
  - Glass- og metallemballasje  

### Changed
- Alle sensorer har nå `device_info` og grupperes under én device i Home Assistant
- Ryddet og modernisert `sensor.py` med felles `device_info()`‑funksjon
- Forbedret dato‑håndtering og robust parsing
- Mer konsistent navngivning og struktur i sensor‑klasser

### Fixed
- Sensorer som tidligere havnet i *Ungrouped* ligger nå korrekt under *HRA Renovasjon*
- Mindre feil i ikonvalg og fallback‑logikk

---

## [0.1.5] – 2026-03-xx
### Added
- Første versjon med kalenderstøtte
- Grunnleggende fraksjonssensorer
- Config flow

---

## [0.1.0] – Initial Release
### Added
- Første fungerende versjon av integrasjonen
- Henting av renovasjonsdata fra HRA API
- Opprettelse av fraksjonssensorer
