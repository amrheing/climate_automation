<a href="https://github.com/amrheing/climate_automation/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/amrheing/climate_automation"></a>
<a href="https://github.com/amrheing/climate_automation/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/amrheing/climate_automation"></a>
<a href="https://github.com/amrheing/climate_automation/blob/master/LICENSE"><img alt="GitHub license" src="https://img.shields.io/github/license/amrheing/climate_automation"></a>

# climate_automation.py 

This python_script is for use in HomeAssistant

## Features
- multiple Thermostats per room
- multiple Window sensors
- multiple On / Off Switches
- presense mode
- party mode
- define a globale eco and decide to use that
- all service data is given as helper objects in HA
  - input_number
  - input_boolean
  - input_datetime
- validation of service data
- much debug code
- switch debug on / off

The overall goal of the script is no data in the script. 
All service data has to be set bei number, time or boolean helpers in HA.

The script is tested with the "Eurotronics Spirit zwave" Thermostats.

1) If one On/Off switch is off or the one window is open: `hvac_mode`will be `off`
2) If not in a time schedule or precense is away: `preset_mode` will be `Heat Eco`
3) If in time_schdule or party mode is on: `preset_mode` will be `heat`

When setting the `hvac_mode`also the temperature is set

The script checks always the actual settings to decrease network actions

With debug mode you get a lot of information about the checks 

## Next goals

implement an outside temperature sensor to manage the global on / off state
flexible decission what to do when windows are open
holiday mode based on calender
thermostast presets and integration of the danfoss zwave thermostat

## Installation

put this file in your "python_scripts" folder in HomeAssistant /config, reload the scripts and create the automation rule

## Konfiguration

| Name                    | Required  | Description                                                      |
| ----------------------- | --------- | ---------------------------------------------------------------- |
| entity_ids              | True      | list of entity ids to control                                    |
| debug                   | False     | Single Switch on / off the debug mode                            |
| switches_on_off         | False     | list switches for on  / off                                      |
| sensors_presence        | False     | list of sensors to test the precense                             |
| eco_global_temperature  | False     | eco Temperature in the house                                     |
| use_eco_global          | False     | use the global or local eco temperature - default: OFF           |
| eco_temperature         | False     | the rooms eco temperature - default: 16                          |
| comfort_temperature     | False     | the rooms comfort temperature - default: 22                      |
| party_mode              | False     | switch on party mode, disables time scheduling - default: OFF    |
| windows                 | False     | Window open sensors - Default: Closed                            |
| schedule1_start         | False     | Start time of heating schedule 1                                 |
| schedule1_end           | False     | End time of heating schedule 1                                   |
| schedule2_start         | False     | Start time of heating schedule 2                                 |
| schedule2_end           | False     | End time of heating schedule 2                                   |


## HomeAssistant Automation

```yaml
- id: 0123456789
  alias: Climate Livingroom
  trigger:
    - hours: "*"
      minutes: "1"
      platform: time_pattern
    - entity_id: input_boolean.climate_on
      platform: state
    - entity_id: nput_boolean.climate_office_on_off
      platform: state
  condition: []
  action:
    - data:
        comfort_temperature: input_number.thermostat_office_comfort_temperature
        debug: input_boolean.climate_debug_mode
        party_mode: input_boolean.party_modus
        eco_temperature: input_number.thermostat_office_eco_temperature
        eco_global_temperature: input_number.eco_temperature
        entity_ids:
          - climate.thermostat_office_left
          - climate.thermostat_office_right
        schedule1_end: input_datetime.climate_office_schedule1_end
        schedule1_start: input_datetime.climate_office_schedule1_start
        schedule2_end: input_datetime.climate_office_schedule2_end
        schedule2_start: input_datetime.climate_office_schedule2_start
        sensors_presence:
          - input_boolean.home_mode
        switches_on_off:
          - input_boolean.climate_on
          - input_boolean.climate_office_on_off
        use_eco_global: input_boolean.climate_office_use_global_eco
        windows:
        - binary_sensor.window_office_left
        - binary_sensor.window_office_right
      service: python_script.climate_automation
```
