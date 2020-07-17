# Definitions

#get debug
sensor = data.get("debug", None)
if sensor != None:
	sensor_state = hass.states.get(sensor).state
	if sensor_state == "on":
		DEBUG = True
	else:
		DEBUG = False
else:
	DEBUG = False

def ld(msg, *args):
	if DEBUG == True:
		logger.info(msg % args)

ld("Start climate_automation Entwicklung")
	
# Set this to False to deactivate the service calls - only for extrem debugging
live = True

# Defaults
DEFAULT_ECO = 16
DEFAULT_COMFORT = 22
DEFAULT_PRESENSE = True
DEFAULT_SWITCH_ON_OFF = True
DEFAULT_WINDOW_OPEN = False
DEFAULT_PARTY_MODE = False
DEFAULT_USE_ECO_GLOBAL = False
DEFAULT_IN_TIME = False


# climate entitiy attributes
# get attributes

# Attributes 
CLIMATE_HVAC_MODES = "hvac_modes"
CLIMATE_MIN_TEMP = "min_temp"
CLIMATE_MAX_TEMP = "max_temp"
CLIMATE_PRESET_MODES = "preset_modes"
CLIMATE_CURRENT_TEMPERATURE = "current_temperature"
CLIMATE_TEMPERATURE = "temperature"
CLIMATE_PRESET_MODE = "preset_mode"
CLIMATE_NODE_ID = "node_id"
CLIMATE_VALUE_INDEX = "value_index"
CLIMATE_VALUE_INSTANCE = "value_instance"
CLIMATE_VALUE_ID = "value_id"
CLIMATE_FRIENDLY_NAME = "friendly_name"

PARAM_ENTITY_IDS = "entity_ids"
PARAM_ENTITY_ID = "entity_id"
PARAM_PARTY_MODE = "party_mode"
PARAM_USE_GLOBAL_ECO = "use_eco_global"
PARAM_SWITCHES_ON_OFF = "switches_on_off"
PARAM_WINDOW_SENSORS = "windows"
PARAM_PRESENCE_SENSORS = "sensors_presence"
PARAM_GLOBAL_ECO = "eco_global_temperature"
PARAM_ECO_TEMPERATURE = "eco_temperature"
PARAM_COMFORT_TEMPERATURE = "comfort_temperature"
PARAM_SCHEDULE_WEEKDAYS = "schedule_weekdays"
PARAM_SCHEDULE_SATURDAYS = "schedule_saturdays"
PARAM_SCHEDULE_SUNDAYS = "schedule_sundays"


# climate service commands
DOMAIN = "climate"
# thermostat presets
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

SENSOR_ON = "on"
SENSOR_OFF = "off"

# Set decider to default
ENTITY_IDS = []
WINDOW_OPEN = DEFAULT_WINDOW_OPEN
PRESENSE = DEFAULT_PRESENSE
SWITCH_ON_OFF = DEFAULT_SWITCH_ON_OFF
IN_TIME = DEFAULT_IN_TIME
PARTY_MODE = DEFAULT_PARTY_MODE
USE_GLOBAL_ECO = DEFAULT_USE_ECO_GLOBAL
TEMPERATURE_COMFORT = DEFAULT_COMFORT
TEMPERATURE_ECO = DEFAULT_ECO
USE_GLOBAL_ECO = DEFAULT_USE_ECO_GLOBAL

# define all sensors initial

def get_data_from_param(var, attr):
	ld("### get_data_from_param: var: %s attr: %s", var, attr)
	try:
		result = data.get(attr, None)
		ld("- data got for %s: %s", attr, result)
		return result
	except:
		return var
		
	
def get_data_from_entity(var, attr):
	ld("### get-data_from_entity: var: %s attr: %s", var, attr)
	try:
		sensor = data.get(attr, None)
		ld("- data got for %s: %s", attr, sensor)
		try:
			result = hass.states.get(sensor).state
			ld("-- data got for %s: %s", sensor, result)
			return result
		except:
			return var
	except:
		return var
	

# load entitys

try:
	ENTITY_IDS = data.get(PARAM_ENTITY_IDS, [])
	ld("+ loaded entitys: %s", ENTITY_IDS)
except:
	ld("ERROR loading entitys")

# only if there are entitys - go on
	
if len(ENTITY_IDS) > 0:
	SWITCHES_ON_OFF = get_data_from_param([], PARAM_SWITCHES_ON_OFF)
	SENSORS_WINDOWS = get_data_from_param([], PARAM_WINDOW_SENSORS)
	SENSORS_PRESENCE = get_data_from_param([], PARAM_PRESENCE_SENSORS)
	
	SENSOR_PARTY_MODE = get_data_from_entity(DEFAULT_PARTY_MODE, PARAM_PARTY_MODE)
	TEMPERATURE_ECO_GLOBAL = get_data_from_entity(None, PARAM_GLOBAL_ECO)
	TEMPERATURE_USE_GLOBAL_ECO = get_data_from_entity(DEFAULT_USE_ECO_GLOBAL, PARAM_USE_GLOBAL_ECO)
	TEMPERATURE_ECO = get_data_from_entity(DEFAULT_ECO, PARAM_ECO_TEMPERATURE)
	TEMPERATURE_COMFORT = get_data_from_entity(DEFAULT_COMFORT, PARAM_COMFORT_TEMPERATURE)
	SCHEDULE_WEEKDAYS = get_data_from_entity("", PARAM_SCHEDULE_WEEKDAYS)
	SCHHEDULE_SATURDAYS = get_data_from_entity("", PARAM_SCHEDULE_SATURDAYS)
	SCHEDULE_SUNDAYS = get_data_from_entity("", PARAM_SCHEDULE_SUNDAYS)
		
# helpers
NO_TIME = datetime.time.fromisoformat("00:00:00")
now = dt_util.now().time()
# Monday: 0 -- Sunday: 7
thisDay = dt_util.now().weekday()
ld("+ thisDay: %s", thisDay)

	
##########################################################################################
#  Functions which are independent the climate ENTITY_ID                                 #
##########################################################################################

##########################################################################################
# - my functions work with global variables which where previously set                   #
#   i know that is not the best way to create functions :-)                              #
# - variable data is given as parameter                                                  #
##########################################################################################

# Time Schedules
		
def get_time_schedule(day): 
	ld("+ get_time_schedule of day %s", day)
	switcher = {
			1: SCHEDULE_WEEKDAYS,
			2: SCHEDULE_WEEKDAYS,
			3: SCHEDULE_WEEKDAYS,
			4: SCHEDULE_WEEKDAYS,
			5: SCHEDULE_WEEKDAYS,
			6: SCHHEDULE_SATURDAYS,
			7: SCHEDULE_SUNDAYS
		} 
	return switcher.get(day, None)
		
time_schedule = get_time_schedule(thisDay)

ld("+ Time Schedule is %s", time_schedule)


# function to check the state in time schedules
def is_time_between(now, begin_time, end_time) -> bool:
	ld("### is_time_between: Now: %s - Begin: %s - End: %s", now, begin_time, end_time)
	#if begin_time == end_time:
	#	ld("Schedule Times are equal")
	#	return False
	# get starttime 
	try:
		xhour = int(begin_time.split(":")[0])
	except:
		xhour = 0
	try:
		xmin = int(begin_time.split(":")[1])
	except:
		xmin = 0
	begin = datetime.time(hour=xhour, minute=xmin)
	ld("- beginn time: %s", begin)

	try:
		yhour = int(end_time.split(":")[0])
	except:
		yhour = 0
	try:
		ymin = int(end_time.split(":")[1])	
	except:
		ymin = 0
	end = datetime.time(hour=yhour, minute=ymin)
	ld("- end time: %s", end)

	ld("+ check %s < %s < %s", begin, now, end)
	try:
		if now >= begin and now <= end:
			ld("- is in time slot!")
			return True
		else:  
			ld("- not in time slot")
			return False
	except:
		ld("- time format wrong")
		return False

# function to check presense
def is_at_home() -> bool:
	for presense in SENSORS_PRESENCE:
		presense_state = hass.states.get(presense).state
		ld("+ %s has state: %s", presense, presense_state)

		if presense_state != SENSOR_ON:
		# if any presense is not ON, then PRESENSE go to False
			ld("+ %s is gone to OFF", presense)
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
					 
##########################################################################################			 
# set thermostat off only if not current to reduce commands
def call_climate_off():
	ld("+ Current state: %s - Current HVAC Mode: %s", current_preset, current_state)
	if current_state != HVAC_MODE_OFF:
		try:
			SERVICE_DATA = service_data(ENTITY_ID)
			ld("- Set climate to OFF - %s", SERVICE_DATA)
			if live == True:
				hass.services.call(DOMAIN, SERVICE_TURN_OFF, SERVICE_DATA, False)
		except:
			ld("- Set climate off fails")
	else:
		ld("- No need to change the hvac mode")
	
##########################################################################################
# set climate to comfort and set comfort temperature
# this function use the temperature as parameter to avoid global data for that purpose
def call_climate_comfort(comfort_temperature):
	# turn climate on only if not current to reduce commands
	ld("+ Current state: %s - Current HVAC Mode: %s", current_preset, current_state)
	try:
		if current_state != HVAC_MODE_HEAT:
			SERVICE_DATA = service_data(ENTITY_ID)
			ld("- Set HVAC mode to %s on %s", SERVICE_TURN_ON, SERVICE_DATA)
			if live == True:
				hass.services.call(DOMAIN, SERVICE_TURN_ON, SERVICE_DATA, False)
			time.sleep(3)
		else:
			ld("- No need to change the hvac mode")
	except:
		ld("- set hvac mode fails")
		
	# set preset only if not current to reduce commands
	try:
		if current_preset != PRESET_MODE_NONE:
			SERVICE_DATA = service_data(ENTITY_ID)
			SERVICE_DATA[CLIMATE_PRESET_MODE] = PRESET_MODE_NONE
			ld("+ Set Preset mode to %s", PRESET_MODE_NONE)
			if live == True:
				hass.services.call(DOMAIN, SERVICE_SET_PRESET_MODE, SERVICE_DATA, False)
			time.sleep(3)
		else:
			ld("+ No need to change the preset mode")
	except:
		ld("- set preset mode fails")
		
	# set temperature
	try:
		if current_setpoint != comfort_temperature:
			SERVICE_DATA = service_data(ENTITY_ID)
			SERVICE_DATA[CLIMATE_TEMPERATURE] = float(comfort_temperature)
			ld("+ Set temperature to comfort: %s", SERVICE_DATA)
			if live == True:
				hass.services.call(DOMAIN, SERVICE_SET_TEMPERATURE, SERVICE_DATA, False)
		else:
			ld("+ No need to change the temperature setpoint")
	except:
		ld("- Set temperature setpoint fails")

##########################################################################################
# set climate to eco and st eco temperature
# this function use the temperature as parameter to avoid global data for that purpose
def call_climate_eco(eco_temperature):
	ld("+ Current state: %s - Current HVAC Mode: %s", current_preset, current_state)
	# turn climate on only if not current to reduce commands
	#if current_state != HVAC_MODE_HEAT:
	#	hass.services.call(DOMAIN, SERVICE_TURN_ON, SERVICE_DATA, False)
	# set preset only if not current to reduce commands
	try:
		if current_preset != PRESET_MODE_ECO:
			SERVICE_DATA = service_data(ENTITY_ID)
			SERVICE_DATA[ATTR_PRESET_MODE] = PRESET_MODE_ECO
			ld("+ Set preset_mode to eco - %s", SERVICE_DATA)
			if live == True:
				hass.services.call(DOMAIN, SERVICE_SET_PRESET_MODE, SERVICE_DATA, False)
		else:
			ld("+ No need to change the Preset Mode")
	except:
		ld("- Set the Preset mode fails")
	# set temperature
	try:
		if current_setpoint != eco_temperature:
			SERVICE_DATA = service_data(ENTITY_ID)
			SERVICE_DATA[ATTR_TEMPERATURE] = float(eco_temperature)
			ld("+ Set temperature to eco - %s", SERVICE_DATA)
			if live == True:
				hass.services.call(DOMAIN, SERVICE_SET_TEMPERATURE, SERVICE_DATA, False)
		else:
			ld("+ No need to change the temperature setpoint")
	except:
		ld("- Set temperature setpoint fails")
			

##########################################################################################
#  get all the states to control                                                         #
##########################################################################################

# presense
ld("### Check presense ###")
	
PRESENSE = is_at_home()

# Switches ON or OFF
# check if switch states are OFF
# default: True  climate automation is ON
ld("### check OFF sensor states ###")
# if any SENSOR_OFF is OFF, the switch get False
try:
	for switch in SWITCHES_ON_OFF:
		switch_state = hass.states.get(switch).state
		if switch_state == SENSOR_OFF:
			ld("+ Climate automation will be OFF")
			SWITCH_ON_OFF = False
except:
	ld("ON/OFF Switch check fails")

# windows
# check if windows are open
ld("### check window states ###")
try:
	for window in SENSORS_WINDOWS: 
			window_state = hass.states.get(window).state
			ld("- %s has state: %s", window, window_state)
			# We invert this statement to catch 'None' as well
			if hass.states.is_state(window, SENSOR_ON):
			# if any Windows is open, then WINDOW_OPEN get True
				ld("- %s is open", window)
				WINDOW_OPEN = True
except:
	ld("Window Check fails")
	

	
# which eco temperature should be used
ld("### check use of global eco ###")
if TEMPERATURE_USE_GLOBAL_ECO == SENSOR_ON:
	ld("- Global Eco should be used")
	ECO_SETPOINT = TEMPERATURE_ECO_GLOBAL
else:
	ld("- local eco will be used")
	ECO_SETPOINT = TEMPERATURE_ECO

##########################################################################################
#  Functions special for the climate ENTITY_ID                                           #
##########################################################################################

# check first if an entity is given
try:	
	for ENTITY_ID in ENTITY_IDS:
		ld("+ work with enitiy: %s", ENTITY_ID)
		# get the current thermostat values
		try:
			actual_states = hass.states.get(ENTITY_ID)
			ld("- Climate RAW: %s", actual_states)
		except:
			ld("- Entity: %s could not be retrieved", ENTITY_ID)
			
		try:
			current_state = actual_states.state
			ld("- Current State of %s: %s", ENTITY_ID, current_state)
		except:
			ld("- get state of %s fails", ENTITY_ID)
			
		try:
			current_preset = actual_states.attributes.get(CLIMATE_PRESET_MODE)
			ld("- Current Preset of %s: %s", ENTITY_ID, current_preset)
		except:
			ld("- get preset of %s fails", ENTITY_ID)
		
		try:
			current_setpoint = actual_states.attributes.get(CLIMATE_TEMPERATURE)
			ld("- Current Set Point of %s: %s", ENTITY_ID, current_setpoint)
		except:
			ld("- get setpoint of %s fails", ENTITY_ID)
			
		try:	
			current_temperature = actual_states.attributes.get(CLIMATE_CURRENT_TEMPERATURE)
			ld("- Current temperture of %s: %s", ENTITY_ID, current_temperature)
		except:
			ld("- get current temperature of %s fails", ENTITY_ID)

		logger.info("\"%s\": --> Actual States %s - Preset: %s - Setpoint: %s - Temperature: %s", ENTITY_ID, current_state, current_preset, current_setpoint, current_temperature)		
		
		# in Time?
		if time_schedule != None:
			slots = time_schedule.split(",")
			for slot in slots:
				start = slot.split("-")[0]
				end = slot.split("-")[1]
				ld("+ Slot: %s - Start: %s - End: %s", slot, start, end)
				if is_time_between(now, start, end) == True:
					IN_TIME = True
				
		logger.info("\"%s\": --> Start Logic: ON/OFF: %s - WINDOW: %s - TIME: %s - PRESENCE: %s - PARTY: - %s", ENTITY_ID, SWITCH_ON_OFF, WINDOW_OPEN, IN_TIME, PRESENSE, SENSOR_PARTY_MODE)

			
		# Logic
		if SWITCH_ON_OFF == True and WINDOW_OPEN == False:
			logger.info("\"%s\": No OFF State and all windows closed -> Thermostat will be on", ENTITY_ID)
			if IN_TIME == False or PRESENSE == False:
				logger.info("\"%s\": Now is out of Time Schdule or presense is off -> Eco mode", ENTITY_ID)			
				call_climate_eco(ECO_SETPOINT)
			elif IN_TIME or PARTY_MODE == SENSOR_ON:
				logger.info("\"%s\": Now is in Time Schedule or Party -> Comfort Mode - %s Celsius", ENTITY_ID, TEMPERATURE_COMFORT)
				call_climate_comfort(TEMPERATURE_COMFORT)
		else:
			logger.info("\"%s\": There is a OFF state or a window open -> Thermostat will be off", ENTITY_ID)
			call_climate_off()
			
		if len(ENTITY_IDS) > 1:
			time.sleep(2)
except:
	logger.info("\"%s\": There is an error with the enitity", ENTITY_ID)
