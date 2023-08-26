import ujson
import machine
import _thread

GLOBALS = {
	"Alarm": {
		"Enabled": 1,
		"Hour": 15,
		"Minute": 0,
		"DurationS": 300
	},
	"Time": {
		"Year": 2023,
		"Month": 1,
		"Day": 1,
		"Hour": 0,
		"Minutes": 0,
		"Seconds": 0
	},
	"Buzzer": {
		"Frequency": 1500,
		"DutyCycle%": 50,
		"BeepUnitMs": 100
	},
	"Pins": {
		"LcdIAddr": 0x27,
		"LcdIsda": 0,
		"LcdIscl": 1,
		"Btn0": 28,
		"Btn1": 27,
		"Btn2": 26,
		"BuzzerData": 9
	},
	"Ui": {
		"AlarmReps": 6,
		"LockMinutes": 5,
		"InputDelay": 200,
		"BacklightMs": 5000,
		"AlarmGraceMs": 2500
	},
	"Fixed": {
		"LcdICols": 16,
		"LcdIRows": 2,
		"LcdIFreq": 400000,
		"BtnPullDown": 1,
	}
}

# Needs to be recalculated every time the globals definition is changed
GLOBALS_PERMUTATIONS = {
	"GLOBALS": [0, 4, 5, 2, 1, 3],
	"Alarm": [3, 0, 1, 2],
	"Time": [0, 2, 4, 3, 5, 1],
	"Buzzer": [2, 0, 1],
	"Ui": [4, 0, 1, 2, 3]
}

RTC = machine.RTC()
GLOBALS_DIRTY = {
	"Dirty": False
}
GLOBAL_LOCKS = {
	"Thread": _thread.allocate_lock()
}

def read_globals():
	global GLOBALS
	try:
		with open("globals_stored.json", "r") as globals_file:
			GLOBALS = ujson.loads(globals_file.read())
		return True
	except:
		pass # Ignore

	finally:
		apply_time()
	
	return False

def store_globals():
	global GLOBALS
	print("Storing globals.")
	with open("globals_stored.json", "w") as globals_file:
		globals_file.write(ujson.dumps(GLOBALS))

""" Reorders GLOBALS for a better UX (hardcoded) """
def permutate_list(name, key_list):
	key_list_len = len(key_list)
	if not (name in GLOBALS_PERMUTATIONS) or key_list_len == 0: return key_list
	permutations = GLOBALS_PERMUTATIONS[name]

	result = [None] * key_list_len
	for source_index, target_index in enumerate(permutations):
		if source_index < key_list_len and target_index < key_list_len:
			result[target_index] = key_list[source_index]
	
	for i, item in enumerate(result):
		if item == None:
			result[i] = key_list[i]
	
	return result
	
def weekDay(year, month, day):
	offset = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
	afterFeb = 1
	if month > 2: afterFeb = 0
	aux = year - 1700 - afterFeb
	# dayOfWeek for 1700/1/1 = 5, Friday
	dayOfWeek  = 5
	# partial sum of days betweem current date and 1700/1/1
	dayOfWeek += (aux + afterFeb) * 365                  
	# leap year correction    
	dayOfWeek += aux / 4 - aux / 100 + (aux + 100) / 400     
	# sum monthly and day offsets
	dayOfWeek += offset[month - 1] + (day - 1)               
	dayOfWeek %= 7
	return int(dayOfWeek // 1)

def update_time():
	current_time = RTC.datetime()
	GLOBALS["Time"]["Year"] = current_time[0]
	GLOBALS["Time"]["Month"] = current_time[1]
	GLOBALS["Time"]["Day"] = current_time[2]
	GLOBALS["Time"]["Hour"] = current_time[4]
	GLOBALS["Time"]["Minutes"] = current_time[5]
	GLOBALS["Time"]["Seconds"] = current_time[6]

def apply_time():
	weekday = weekDay(GLOBALS["Time"]["Year"], GLOBALS["Time"]["Month"], GLOBALS["Time"]["Day"])
	RTC.datetime((GLOBALS["Time"]["Year"], GLOBALS["Time"]["Month"], GLOBALS["Time"]["Day"], weekday, GLOBALS["Time"]["Hour"], GLOBALS["Time"]["Minutes"], GLOBALS["Time"]["Seconds"], 0))

def get_time():
	return (GLOBALS["Time"]["Year"], GLOBALS["Time"]["Month"], GLOBALS["Time"]["Day"], GLOBALS["Time"]["Hour"], GLOBALS["Time"]["Minutes"], GLOBALS["Time"]["Seconds"])

def get_now_alarm_minutes():
	alarm_hour = GLOBALS["Alarm"]["Hour"]
	alarm_minute = GLOBALS["Alarm"]["Minute"]
	now_time = get_time()
	now_hour = now_time[3]
	now_minute = now_time[4]

	alarm_minutes = 60 * alarm_hour + alarm_minute
	now_minutes = 60 * now_hour + now_minute
	
	return (now_minutes, alarm_minutes)

def index_for_key(the_list, list_name, the_key):
	keys = permutate_list(list_name, list(the_list.keys()))
	for idx, key in enumerate(keys):
		if key == the_key:
			return idx
	return -1

""" Return a next-state with queue. Keys is in format [(category_key, value_key)] """
def orchestrate_write_ui(keys, withDirty=True):
	if len(keys) == 0:
		return ["idle"]

	keys = list(map(lambda x: (x[0], index_for_key(GLOBALS[x[0]], x[0], x[1])), keys))
	first_el = keys.pop(0)
	keys.append(None) # type: ignore

	return ["write", first_el[0], first_el[1], keys, withDirty]

def toggle_alarm(on, withDirty=True):
	GLOBALS["Alarm"]["Enabled"] = 1 if on else 0
	if withDirty: # Disable dirty to prevent excessive writes damaging the flash
		GLOBALS_DIRTY["Dirty"] = True
