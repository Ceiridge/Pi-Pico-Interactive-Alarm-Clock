import globals
from states import State
import buzzer

import utime
import urandom

class AlarmState(State):
	identifier = "A"
	fast_inputs = True

	started_at_ms = 0
	last_right_input_ms = 0

	cols = globals.GLOBALS["Fixed"]["LcdICols"]

	target_bitstring = ""
	input_bitstring = ""
	input_dirty = False
	times = -1

	def enter(self, state_machine):
		self.started_at_ms = utime.ticks_ms()
		self.buzz = buzzer.BuzzerAlarm()
		self.next_bitstring(state_machine.lcd)

	def exit(self, state_machine):
		globals.toggle_alarm(False, withDirty=False) # Disable alarm after exiting
		self.buzz.deinit()

	def draw(self, state_machine, lcd):
		if self.input_dirty:
			self.input_dirty = False
			lcd.move_to(0, 1)
			lcd.putstr(self.input_bitstring)
		
		return False

	def execute(self, state_machine, buttons):
		now = utime.ticks_ms()
		passed_ms = abs(utime.ticks_diff(now, self.started_at_ms))
		passed_right_input = abs(utime.ticks_diff(now, self.last_right_input_ms))

		if passed_ms > (globals.GLOBALS["Alarm"]["DurationS"] * 1000):
			return ["idle"]

		if (not self.buzz.buzzing) and passed_right_input > globals.GLOBALS["Ui"]["AlarmGraceMs"]:
			self.buzz.start()

		if (buttons[0] or buttons[1]) and (not (buttons[0] and buttons[1])) and (not buttons[2]):
			new_str = self.input_bitstring + ("0" if buttons[0] else "1")

			if self.target_bitstring.startswith(new_str):
				self.input_bitstring = new_str
				self.input_dirty = True

				self.last_right_input_ms = utime.ticks_ms()
				self.buzz.stop()

				if len(self.target_bitstring) == len(self.input_bitstring):
					self.next_bitstring(state_machine.lcd)

					if passed_ms > 60000 and self.times >= globals.GLOBALS["Ui"]["AlarmReps"]:
						return ["idle"]
			else:
				self.last_right_input_ms = 0

			utime.sleep_ms(500)


	def next_bitstring(self, lcd):
		self.times += 1
		utime.sleep_ms(1000)
		urandom.seed(utime.ticks_ms())
		
		self.target_bitstring = "".join([urandom.choice(["0", "1"]) for _ in range(self.cols - 1)])
		self.input_bitstring = ""
		self.last_right_input_ms = utime.ticks_ms()
		
		lcd.move_to(0, 0)
		lcd.putstr(self.target_bitstring)
		lcd.move_to(0, 1)
		lcd.putstr(" " * self.cols)
