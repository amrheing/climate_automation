##########################################################################################
#
# Author: Gerald Amrhein, python_scripts@amrhein.info
# created: 21.06.2020
# license: feel free to use and edit
#
# i had the need to automate my special heatings in the house :-)
# no where i found anything which fullfilled alle my needs
# from former house i had the fritzbox eurotronics dect thermostat 
# and the management in the fritzbox was very likely
# special the time schedules was nice 
#
# my needs:
# - 2 time schedules per room
# - global or room eco temperature
# - room specific comfort temperature
# - party mode
# - switch climate off when window open
# - go to eco when we are away
# - holiday / global mode off
# - all the parameters have to be configurable with sliders or switches or input numbers. No fixed data in service_data!
#
# i use the "Eurotronics SPIRIT Z-WAVE PLUS" thermostats. 
# they get an external temperature sensor "Eurotronics TEMPERATUR-FEUCHTE-SENSOR"
#
# these thermostats are free from any cloud management, abonnements or something else stupid things
#
# the first ideas to write tis script is from "UpdateClimate" in the hacs store! thanks to @Santobert
#
# Next goals:
# - implementation of holiday, maybe from a calendar
# - different temperature decrease when windows get opened
#
#
# Service Data in Automations are:
#
### an input_boolean entity to switch on / Off
### optional: edit in the first lines of the code and use a static entry in service data
### optional: if you do not want to debug, do not place this option in service_data
### default: false
#	debug: input_boolean.climate_debug_mode
#
### A list of thermostats in one room, the will be managed with the same parameters. 
### minimum One entity is mandatory
# entity_ids:
#		- climate.living_room_left
#		- climate.living_room_right
#
### A list of switches which state a ON or OFF for the thermostat
### default: True , means that heating control is ON
# switches_on_off:
#		- input_boolean.heating_global_on_off
#		- input_boolean.heating_living_room_on_off
#
### A list of window sensors
### default: False - means that all windows are closed
# windows:
#		- binary_sensor.living_room_window_left
#		- binary_sensor.living_room_window_right
#
### A list of sensors wich states home with on or off.
### the decission who is at home have to rules separate
### default: True - Home Mode is working
# sensors_presence:
# 	- input_boolean.home_mode
#
### only one switch to state party mode
### default: False - 
# party_mode: input_boolean.party_mode
#
### Each time have to be a input_datetime selector with "time"
# schedule1_start: input_datetime.living_room_heating_schedule1_start
# schedule1_end:   input_datetime.living_room_heating_schedule1_end
# schedule2_start: input_datetime.living_room_heating_schedule2_start
# schedule2_end:   input_datetime.living_room_heating_schedule2_end
#
### An input_number entity
# eco_global_temperature: input_number.eco_temperature
#
### An input_boolean entity
# use_eco_global: input_boolean.living_room_use_global_eco
#
### An input_number entity
# eco_temperature: input_number.livin_room_eco
#
### An input_number entity
# comfort_temperature: input_number.living_room_comfort
#
#########################################

# Definitions
# set default debug mode
#DEBUG = data.get("debug", False)
DEBUG = hass.states.get(data.get("debug")).state
if DEBUG == 'on':
	DEBUG = True
else:
	DEBUG = False

if DEBUG:
	logger.info("Python Script 'Climate Automation' debugging: %s", DEBUG)

# climate entitiy attributes
# get attributes
ATTR_HVAC_MODES = "hvac_modes" 
ATTR_MIT_TEMP = "min_temp"
ATTR_MAX_TEMP = "max_temp"
ATTR_PRESET_MODES = "preset_modes"
ATTR_CURRENT_TEMPERATURE = "current_temperature"
ATTR_NODE_ID = "node_id"
ATTR_VALUE_INDEX = "value_index"
ATTR_VALUE_INSTANCE = "value_instance"
ATTR_VALUE_ID = "value_id"
ATTR_FRIENDLY_NAME = "friendly_name"

# set & get attributes
ATTR_STATE = "state"
ATTR_PRESET_MODE = "preset_mode"
ATTR_TEMPERATURE = "temperature"

# climate service commands
DOMAIN = "climate"
ENTITY_ID = "entity_id"
SERVICE_TURN_OFF = "turn_off"
SERVICE_TURN_ON = "turn_on"
SERVICE_SET_HVAC_MODE = "set_hvac_mode"
SERVICE_SET_PRESET_MODE = "set_preset_mode"
SERVICE_SET_TEMPERATURE = "set_temperature"

# values from the thermostat (eurotronics spirit zwave)
HVAC_MODE_OFF = "off"
HVAC_MODE_HEAT = "heat"
PRESET_MODE_ECO = "Heat Eco"
PRESET_MODE_BOOST = "boost"
PRESET_MODE_MANUFACTURE = "Manufacturer Specific"
PRESET_MODE_NONE = "none"

# helpers
NO_TIME = datetime.time.fromisoformat("00:00:00")
SENSOR_ON = "on"
SENSOR_OFF = "off"
IN_TIME = False
WINDOW_OPEN = False
SWITCH_ON_OFF = True
PRESENSE = True

if DEBUG:
	logger.info("### Start getting data ###")
try:
	# get automation data
	# the enitity to control
	ENTITY_IDS = data.get("entity_ids", None)
	# the list from OFF Sensors
	SWITCHES_ON_OFF = data.get("switches_on_off", [])
	# the list of window sensors
	SENSORS_WINDOWS = data.get("windows", [])
	# the presense sensor
	SENSORS_PRESENCE = data.get("sensors_presence", [])
	# Party Mode?
	SENSOR_PARTY_MODE = hass.states.get(data.get("party_mode")).state
	# Time schedule 1
	SCHEDULE1_START = hass.states.get(data.get("schedule1_start")).state
	SCHEDULE1_END = hass.states.get(data.get("schedule1_end")).state
	# Time schedule 2
	SCHEDULE2_START = hass.states.get(data.get("schedule2_start")).state
	SCHEDULE2_END = hass.states.get(data.get("schedule2_end")).state
	# the Global ECO Temperature
	TEMPERATURE_ECO_GLOBAL = hass.states.get(data.get("eco_global_temperature")).state
	# should the global eco used or the local
	TEMPERATURE_USE_GLOBAL = hass.states.get(data.get("use_eco_global")).state
	# the room eco temperature
	TEMPERATURE_ECO = hass.states.get(data.get("eco_temperature")).state
	# the rooms comfort temperatur
	TEMPERATURE_COMFORT = hass.states.get(data.get("comfort_temperature")).state
except:
	logger.info("Ther is an error retrieving the service_data")

# set states if service_data is not configured
if SENSORS_PRESENCE is None:
	SENSORS_PRESENCE = True

if SENSOR_PARTY_MODE is None:
	SENSOR_PARTY_MODE = False

if TEMPERATURE_ECO_GLOBAL is None:
	TEMPERATURE_ECO_GLOBAL = False
	
##########################################################################################
#  Functions which are independent the climate ENTITY_ID                                 #
##########################################################################################

##########################################################################################
# - my functions work with global variables which where previously set                   #
#   i know that is not the best way to create functions :-)                              #
# - variable data is given as parameter                                                  #
##########################################################################################


# function to check the state in time schedules
def is_time_between(begin_time, end_time) -> bool:
	if begin_time == end_time:
		if DEBUG:
			logger.info("Schedule Times are equal")
		return False
	# get starttime 
	xhour = int(begin_time.split(":")[0])
	xmin = int(begin_time.split(":")[1])
	begin = datetime.time(hour=xhour, minute=xmin)

	yhour = int(end_time.split(":")[0])
	ymin = int(end_time.split(":")[1])	
	end = datetime.time(hour=yhour, minute=ymin)

	now = dt_util.now().time()
	if DEBUG:
		logger.info("check %s < %s < %s", begin, now, end)
	try:
		if begin_time < end_time:
			return now >= begin and now <= end
		else:  # crosses midnight
			return now >= begin or now <= end
	except ValueError:
		logger.info("time format wrong")
		return False

# function to check presense
def is_at_home() -> bool:
	for presense in SENSORS_PRESENCE:
		presense_state = hass.states.get(presense).state
		if DEBUG:
			logger.info("%s has state: %s", presense, presense_state)

		if presense_state != SENSOR_ON:
		# if any presense is not ON, then PRESENSE go to False
			logger.info("%s is gone to OFF", presense)
			return False
		else:
			return True
			
##########################################################################################
#  Functions to control the climate entity                                               #
##########################################################################################

# this create a basic service_data Array with entity_id only
SERVICE_DATA = []
def service_data(entity):
	sd = []
	sd = {"entity_id": entity}
	return sd
					 
# set thermostat off only if not current to reduce commands
def call_climate_off():
	if current_state != HVAC_MODE_OFF:
		SERVICE_DATA = service_data(ENTITY_ID)
		hass.services.call(DOMAIN, SERVICE_TURN_OFF, SERVICE_DATA, False)

# set climate to comfort and set comfort temperature
# this function use the temperature as parameter to avoid global data for that purpose
def call_climate_comfort(comfort_temperature):
	# turn climate on only if not current to reduce commands
	if current_state != HVAC_MODE_HEAT:
		SERVICE_DATA = service_data(ENTITY_ID)
		hass.services.call(DOMAIN, SERVICE_TURN_ON, SERVICE_DATA, False)
	# set preset only if not current to reduce commands
	if current_preset != PRESET_MODE_NONE:
		SERVICE_DATA = service_data(ENTITY_ID)
		SERVICE_DATA[ATTR_PRESET_MODE] = PRESET_MODE_NONE
		hass.services.call(DOMAIN, SERVICE_SET_PRESET_MODE, SERVICE_DATA, False)
	# set temperature
	SERVICE_DATA = service_data(ENTITY_ID)
	SERVICE_DATA[ATTR_TEMPERATURE] = float(comfort_temperature)
	hass.services.call(DOMAIN, SERVICE_SET_TEMPERATURE, SERVICE_DATA, False)

# set climate to eco and st eco temperature
# this function use the temperature as parameter to avoid global data for that purpose
def call_climate_eco(eco_temperature):
	# turn climate on only if not current to reduce commands
	#if current_state != HVAC_MODE_HEAT:
	#	hass.services.call(DOMAIN, SERVICE_TURN_ON, SERVICE_DATA, False)
	# set preset only if not current to reduce commands
	if current_preset != PRESET_MODE_ECO:
		logger.info("Set preset_mode to eco")
		SERVICE_DATA = service_data(ENTITY_ID)
		SERVICE_DATA[ATTR_PRESET_MODE] = PRESET_MODE_ECO
		hass.services.call(DOMAIN, SERVICE_SET_PRESET_MODE, SERVICE_DATA, False)
	# set temperature
	logger.info("Set temperature")
	SERVICE_DATA = service_data(ENTITY_ID)
	SERVICE_DATA[ATTR_TEMPERATURE] = float(eco_temperature)
	hass.services.call(DOMAIN, SERVICE_SET_TEMPERATURE, SERVICE_DATA, False)

##########################################################################################
#  get all the states to control                                                         #
##########################################################################################

# presense
if DEBUG:
	logger.info("### Check presense ###")
	
PRESENSE = is_at_home()

# time schedule
# the default is False. There will be only a change is a time schedule is matching
# with False the time scheduling is OFF and there is always ECO 
if DEBUG:
	logger.info("### Check time schedules ###")

if is_time_between(SCHEDULE1_START, SCHEDULE1_END):
	if DEBUG:
		logger.info("schedule 1 is now active")
	IN_TIME = True
else:
	if DEBUG:
		logger.info("schedule 1 is out of now")

if is_time_between(SCHEDULE2_START, SCHEDULE2_END):
	if DEBUG:
		logger.info("schedule 2 is now active")
	IN_TIME = True
else:
	if DEBUG:
		logger.info("schedule 2 is out of now")
		
# Switches ON or OFF
# check if switch states are OFF
# default: True  climate automation is ON
if DEBUG:
	logger.info("### check OFF sensor states ###")
# if any SENSOR_OFF is OFF, the switch get False
for switch in SWITCHES_ON_OFF:
	switch_state = hass.states.get(switch).state
	if DEBUG:		
		logger.info("%s has state: %s", switch, switch_state)
	if switch_state == SENSOR_OFF:
		logger.info("Climate automation will be OFF")
		SWITCH_ON_OFF = False

# windows
# check if windows are open
if DEBUG:
	logger.info("### check window states ###")
for window in SENSORS_WINDOWS: 
	window_state = hass.states.get(window).state
	if DEBUG:
		logger.info("%s has state: %s", window, window_state)
	# We invert this statement to catch 'None' as well
	if hass.states.is_state(window, SENSOR_ON):
	# if any Windows is open, then WINDOW_OPEN get True
		if DEBUG:
			logger.info("%s is open", window)
		WINDOW_OPEN = True
	
# which eco temperature should be used
if DEBUG:
	logger.info("### check use of global eco ###")
if TEMPERATURE_USE_GLOBAL == SENSOR_ON:
	if DEBUG:
		logger.info("Global Eco should be used")
	ECO_SETPOINT = TEMPERATURE_ECO_GLOBAL
else:
	if DEBUG:
		logger.info("local eco will be used")
	ECO_SETPOINT = TEMPERATURE_ECO

##########################################################################################
#  Functions special for the climate ENTITY_ID                                           #
##########################################################################################

# check first if an entity is given
try:
	count = len(ENTITY_IDS)
	if count >= 1:
		for ENTITY_ID in ENTITY_IDS:
			# get the current thermostat values
			try:
				actual_states = hass.states.get(ENTITY_ID)
				current_state = actual_states.state
				current_preset = actual_states.attributes.get(ATTR_PRESET_MODE)
				current_setpoint = actual_states.attributes.get(ATTR_TEMPERATURE)
				current_temperature = actual_states.attributes.get(ATTR_CURRENT_TEMPERATURE)
			except:
				logger.info("Entity: %s could not be retrieved", ENTITY_ID)
			
			logger.info("ENTITY: %s - SWITCH_ON_OFF: %s - PRESENSE: %s - WINDOWS OPEN: %s - IN TIME: %s - Party: %s", ENTITY_ID, SWITCH_ON_OFF, PRESENSE, WINDOW_OPEN, IN_TIME, SENSOR_PARTY_MODE)
			logger.info("Eco Setpoint: %s - Global Eco: %s - use Global: %s - Eco: %s - Comfort: %s", ECO_SETPOINT, TEMPERATURE_ECO_GLOBAL, TEMPERATURE_USE_GLOBAL, TEMPERATURE_ECO, TEMPERATURE_COMFORT)

			# Logic
			if SWITCH_ON_OFF == True and WINDOW_OPEN == False:
				logger.info("No OFF State and all windows closed -> Thermostat will be on")
				if IN_TIME == False or PRESENSE == False:
					logger.info("Now is out of Time Schdule or presense is off -> Eco mode")			
					call_climate_eco(ECO_SETPOINT)
				elif IN_TIME or SENSOR_PARTY_MODE == SENSOR_ON:
					logger.info("Now is in Time Schedule or Party -> Comfort Mode")
					call_climate_comfort(TEMPERATURE_COMFORT)
			else:
				logger.info("There is a OFF state or a window open -> Thermostat will be off")
				call_climate_off()
except:
	logger.info("There is an error with the enitity")