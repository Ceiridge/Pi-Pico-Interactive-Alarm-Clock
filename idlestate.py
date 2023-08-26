import globals
from states import State
import utime

class IdleState(State):
	identifier = " "

	backlight_on_ticks = 0
	will_disable_backlights = False

	def enter(self, state_machine):
		state_machine.lcd.backlight_off()

		if globals.GLOBALS["Alarm"]["Enabled"] != 0:
			alarm = (globals.GLOBALS["Alarm"]["Hour"], globals.GLOBALS["Alarm"]["Minute"])

			state_machine.lcd.move_to(9, 1)
			state_machine.lcd.putstr(f"<{self.format_num(alarm[0])}:{self.format_num(alarm[1])}>")

	def draw(self, state_machine, lcd):
		# Hacky dirty globals save
		if globals.GLOBALS_DIRTY["Dirty"]:
			globals.GLOBALS_DIRTY["Dirty"] = False
			globals.store_globals()

		time = globals.get_time()

		lcd.move_to(0, 0)
		lcd.putstr(f"{self.format_num(time[2])}.{self.format_num(time[1])}.{str(time[0])}")
		lcd.move_to(0, 1)
		lcd.putstr(f"{self.format_num(time[3])}:{self.format_num(time[4])}:{self.format_num(time[5])}")
		return False

	def format_num(self, num):
		if num < 10:
			return "0" + str(num)
		else:
			return str(num)

	def execute(self, state_machine, buttons):
		now = utime.ticks_ms()
		alarm_on = globals.GLOBALS["Alarm"]["Enabled"] != 0

		# Switch to locked before the alarm
		if alarm_on:
			now_minutes, alarm_minutes = globals.get_now_alarm_minutes()
			if alarm_minutes - now_minutes <= globals.GLOBALS["Ui"]["LockMinutes"] and alarm_minutes >= now_minutes:
				return ["locked"]

		if self.will_disable_backlights and abs(utime.ticks_diff(now, self.backlight_on_ticks)) >= globals.GLOBALS["Ui"]["BacklightMs"]:
			self.will_disable_backlights = False
			state_machine.lcd.backlight_off()
	

		if buttons[0] and buttons[1] and buttons[2]: # Toggle alarm
			globals.toggle_alarm(not alarm_on, withDirty=False)
			return ["idle"]
		elif buttons[0] and buttons[2]: # Set time
			return globals.orchestrate_write_ui([("Time", "Year"), ("Time", "Month"), ("Time", "Day"), ("Time", "Hour"), ("Time", "Minutes"), ("Time", "Seconds")])
		elif buttons[1] and buttons[2]: # Set alarm
			return globals.orchestrate_write_ui([("Alarm", "Hour"), ("Alarm", "Minute")], withDirty=False)
		elif buttons[0] and buttons[1]: # Switch mode
			return ["category"]
		elif buttons[0] or buttons[1] or buttons[2]: # Light
			self.backlight_on_ticks = now
			self.will_disable_backlights = True
			state_machine.lcd.backlight_on()


class LockedState(IdleState):
	identifier = "L"

	def enter(self, state_machine):
		super().enter(state_machine)
		state_machine.lcd.backlight_on()

	def execute(self, state_machine, buttons):
		now_minutes, alarm_minutes = globals.get_now_alarm_minutes()

		if now_minutes == alarm_minutes:
			return ["alarm"]
		elif now_minutes > alarm_minutes:
			return ["idle"]

		if buttons[2] or (buttons[0] and buttons[1]): # Unlock
			return ["alarm"]
