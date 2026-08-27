# HRA Renovasjon

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)


Home Assistant integration of the norwegian HRA Renovasjon app (HRA App). Special for Ringerike, Lunner,Hole og Jevnaker

Denne integrasjonen er laget for HRA Renovasjon (Hadeland og Ringerike Avfallsselskap AS).
Støtter kommunene Ringerike, Hole, Jevnaker, osv.

Based and Credit to : https://github.com/eyesoft/home_assistant_min_renovasjon/.  Only changed the api / decode part to suit HRA API
## Installation
Under HACS -> Integrations, add custom repository "https://github.com/SEspe/home_assistant_HRA_renovasjon/ with Category "Integration". 

Search for repository "HRA_Renovasjon" and download it. Restart Home Assistant.

Go to Settings > Integrations and Add Integration "HRA Renovasjon". Type in address to search, e.g. "Min gate 12, 0153" (street address comma zipcode).

## Entities

Everything for one address is grouped under a single device. Several addresses
are supported — add the integration once per address, and each gets its own
device and its own set of entities.

The schedule is refreshed from HRA once an hour.

### Fraction sensors

One sensor per waste fraction HRA reports for your address, created
automatically. If HRA adds a fraction mid-season, its sensor shows up at the
next refresh without a restart.

Fractions in the HRA area:

- Restavfall
- Matavfall
- Papir, papp og kartong
- Plastemballasje
- Glass- og metallemballasje

**State:** the next collection date, as `YYYY-MM-DD`. Only today and later are
counted; a fraction with nothing scheduled reports `unknown`.

**Attributes:**

| Attribute | Description |
|---|---|
| `next_date` | Next collection date — same as the state |
| `next_dates` | The next collection dates, up to five |
| `days_to_pickup` | Whole days from today until `next_date` (never negative) |
| `route_name` | HRA's route for the collection, e.g. `408 Mat og restavfall` |
| `frequency` | Collection interval in weeks — 4 or 8 in the HRA area |
| `fraction_id`, `fraction_guid` | HRA's own identifiers for the fraction |

Each sensor also carries an `entity_picture` with the fraction's image, and an
`mdi` icon as fallback.

### Summary sensors

Two sensors summarise all fractions at once:

| Entity | State | Attributes |
|---|---|---|
| `sensor.hra_renovasjon_next_date` | Earliest upcoming collection date across every fraction | `days_to_pickup`, and `fractions` — the fractions collected on that date, comma separated |
| `sensor.hra_renovasjon_days_to_go` | Whole days until that collection | — |

### Calendar

`calendar.hra_renovasjon_kalender` gets one all-day event per collection,
titled with the fraction name. It works with the standard Calendar card and
with calendar triggers in automations.

### A note on entity IDs

The IDs above are what most installations have. Home Assistant derives entity
IDs from the device and entity name, and that derivation has changed across HA
versions — a **fresh** install will usually get the device name as a prefix on
the fraction sensors:

| Installed | Fraction sensor |
|---|---|
| Before v0.1.6 | `sensor.restavfall` |
| v0.1.6 and later | `sensor.hra_renovasjon_restavfall` |

Existing entity IDs are never changed by an upgrade, so an older installation
keeps the IDs it already has. Check **Developer Tools → States** and filter on
`hra` to see what yours are called, and use those in the cards below.


## Cards

### Entities card

![Ex1](docs/ex1.png)
<details>
    <summary>Show yaml</summary>

```yaml
type: entities
title: HRA Renovasjon, neste hentedato
entities:
  - entity: sensor.restavfall
    name: Restavfall
  - entity: sensor.matavfall
    name: Matavfall
  - entity: sensor.papir_papp_og_kartong
    name: Papir,papp kartong
  - entity: sensor.plastemballasje
    name: Plast
  - entity: sensor.glass_og_metallemballasje
    name: Glass og metall
```
</details>

### Mushroom template card

![CEx2](docs/ex2.png)


<details>
    <summary>Show yaml</summary>

```yaml EN
type: custom:mushroom-template-card
entity: sensor.hra_renovasjon_next_date
primary: >
  {% set d = states('sensor.hra_renovasjon_next_date') %} Neste tømming: {% if d
  not in ['unknown', 'unavailable', ''] %}
    {{ (as_datetime(d) | as_local).strftime('%A %d %B') | title }}
  {% else %}
    Ukjent
  {% endif %}
secondary: >
  Dager til neste tømming: {{ state_attr('sensor.hra_renovasjon_next_date',
  'days_to_pickup') }}

  Fraksjoner: {{ state_attr('sensor.hra_renovasjon_next_date', 'fractions') }}
icon: mdi:trash-can
multiline_secondary: true
tap_action:
  action: more-info
features_position: bottom
grid_options:
  columns: 12
  rows: auto
color: >
  {% set d = state_attr('sensor.hra_renovasjon_next_date', 'days_to_pickup') |
  int(99) %} {% if d <= 1 %}
    red
  {% elif d <= 3 %}
    orange
  {% elif d <= 7 %}
    yellow
  {% else %}
    green
  {% endif %}
```

```yaml NO
type: custom:mushroom-template-card
entity: sensor.hra_renovasjon_next_date
primary: >
  {% set d = states('sensor.hra_renovasjon_next_date') %} Neste tømming: {% if d
  not in ['unknown', 'unavailable', ''] %}

    {% set dt = as_datetime(d) | as_local %}

    {% set ukedag = {
      'Monday':'Mandag','Tuesday':'Tirsdag','Wednesday':'Onsdag',
      'Thursday':'Torsdag','Friday':'Fredag','Saturday':'Lørdag','Sunday':'Søndag'
    }[dt.strftime('%A')] %}

    {% set måned = {
      'January':'januar','February':'februar','March':'mars','April':'april',
      'May':'mai','June':'juni','July':'juli','August':'august',
      'September':'september','October':'oktober','November':'november','December':'desember'
    }[dt.strftime('%B')] %}

    {{ ukedag }} {{ dt.strftime('%d') }} {{ måned }}

  {% else %}
    Ukjent
  {% endif %}
secondary: >
  Dager til neste tømming: {{ state_attr('sensor.hra_renovasjon_next_date',
  'days_to_pickup') }}

  Fraksjoner: {{ state_attr('sensor.hra_renovasjon_next_date', 'fractions') }}
icon: mdi:trash-can
multiline_secondary: true
tap_action:
  action: more-info
features_position: bottom
grid_options:
  columns: 12
  rows: auto
color: >
  {% set d = state_attr('sensor.hra_renovasjon_next_date', 'days_to_pickup') |
  int(99) %} {% if d <= 1 %}
    red
  {% elif d <= 3 %}
    orange
  {% elif d <= 7 %}
    yellow
  {% else %}
    green
  {% endif %}


```
</details>

## Debugging
in configuration.yaml

```yaml
logger:
  default: info
  logs:
    custom_components.hra_renovasjon: debug
```

## API

The HRA API this integration talks to is documented in
[docs/API.md](docs/API.md): both endpoints, their response fields, the known
waste fractions, and the API's error behaviour (it answers `200 []` for bad
input rather than an error status).
