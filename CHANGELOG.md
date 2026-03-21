# Changelog  
Alle vesentlige endringer i **HRA Renovasjon** dokumenteres her.

Formatet følger prinsippene fra [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
og versjonering følger [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
