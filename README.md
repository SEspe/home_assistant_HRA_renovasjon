# HRA Renovasjon

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)


Home Assistant integration of the norwegian HRA Renovasjon app (HRA App). Special for Ringerike, Lunner,Hole og Jevnaker 

Based and Credit to : https://github.com/eyesoft/home_assistant_min_renovasjon/.  Only changed the api / decode part to suit HRA API
## Installation
Under HACS -> Integrations, add custom repository "https://github.com/SEspe/home_assistant_HRA_renovasjon/ with Category "Integration". 

Search for repository "HRA_Renovasjon" and download it. Restart Home Assistant.

Go to Settings > Integrations and Add Integration "HRA Renovasjon". Type in address to search, e.g. "Min gate 12, 0153" (street address comma zipcode).

Click Configure and choose fractions to create sensors.

Restart Home Assistant.

## Debugging
in configuration.yaml

```yaml
logger:
  default: info
  logs:
    custom_components.hra_renovation: debug
```