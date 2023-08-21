from machine import I2C, Pin
from pico_i2c_lcd import I2cLcd
import utime

import globals
import buzzer
from states import StateMachine
from idlestate import IdleState, LockedState
from categorystate import CategoryState
from rwstate import ReadState, WriteState
from alarmstate import AlarmState


def init():
	did_read_globals = globals.read_globals()

	pull_mode = Pin.PULL_DOWN if (globals.GLOBALS["Fixed"]["BtnPullDown"] != 0) else Pin.PULL_UP
	buttons = [Pin(globals.GLOBALS["Pins"][f"Btn{str(i)}"], Pin.IN, pull_mode) for i in range(3)]
	
	i2clcd = I2C(0, sda=Pin(globals.GLOBALS["Pins"]["LcdIsda"]), scl=Pin(globals.GLOBALS["Pins"]["LcdIscl"]), freq=globals.GLOBALS["Fixed"]["LcdIFreq"])
	lcd = I2cLcd(i2clcd, globals.GLOBALS["Pins"]["LcdIAddr"], globals.GLOBALS["Fixed"]["LcdIRows"], globals.GLOBALS["Fixed"]["LcdICols"])
	lcd.backlight_on()
	lcd.move_to(0, 0)
	
	buzzer.start_buzzing()
	lcd.putstr(str(len(globals.GLOBALS)) + " " + ("Read" if did_read_globals else "New"))
	utime.sleep_ms(500)
	buzzer.stop_buzzing()

	state_machine = StateMachine(IdleState(), lcd, buttons)
	while True:
		globals.update_time()
		val = state_machine.execute()
		val_state = val[0] if val != None else None

		if val_state == "idle":
			state_machine.transition_to(IdleState())
		elif val_state == "category":
			state_machine.transition_to(CategoryState())
		elif val_state == "read":
			state_machine.transition_to(ReadState(val[1], val[2] if len(val) >= 3 else 0))
		elif val_state == "write":
			state_machine.transition_to(WriteState(val[1], val[2], val[3] if len(val) >= 4 else []))
		elif val_state == "locked":
			state_machine.transition_to(LockedState())
		elif val_state == "alarm":
			state_machine.transition_to(AlarmState())

init()
