import globals
import utime

class StateMachine():
	def __init__(self, initial_state, lcd, buttons):
		self.current_state = initial_state
		self.lcd = lcd
		self.buttons = buttons

		self.exit_state(NoneState())
		self.enter_state(self.current_state)

	def transition_to(self, new_state):
		self.exit_state(self.current_state)
		self.enter_state(new_state)
		self.current_state = new_state

	def execute(self):
		sleep_duration = 10 if self.current_state.fast_inputs else globals.GLOBALS["Ui"]["InputDelay"]
		pressed_buttons = self.detect_buttons(sleep_duration)

		val = self.current_state.execute(self, pressed_buttons)
		self.draw()
		return val

	def draw(self):
		if self.current_state.draw(self, self.lcd):
			self.draw_identifier(self.current_state)
	
	def detect_buttons(self, sleep_ms=0):
		pressed_buttons = [False] * len(self.buttons)
		has_pressed_one = False
		sleep_amount = 1 if (sleep_ms == 0) else sleep_ms

		for _ in range(sleep_amount):
			if sleep_ms > 0:
				utime.sleep_ms(1)

			for btn_idx, btn in enumerate(self.buttons):
				if btn.value() == 1: # Btn is high
					pressed_buttons[btn_idx] = True
					has_pressed_one = True
		
		# Delay when a button is pressed to prevent spillovers
		if has_pressed_one: utime.sleep_ms(globals.GLOBALS["Ui"]["InputDelay"] // 2)
		return pressed_buttons


	def draw_identifier(self, the_state):
		self.lcd.move_to(globals.GLOBALS["Fixed"]["LcdICols"] - 1, 0)
		self.lcd.putstr(the_state.identifier)

	def enter_state(self, state):
		state.enter(self)
		self.draw_identifier(state)

	def exit_state(self, state):
		self.lcd.backlight_on()
		self.lcd.clear()
		state.exit(self)

class State():
	identifier = "X"
	fast_inputs = False

	def enter(self, state_machine):
		pass
	
	def execute(self, state_machine, buttons):
		pass

	""" Returns true if screen needs identifier """
	def draw(self, state_machine, lcd):
		return False

	def exit(self, state_machine):
		pass

class NoneState(State):
	identifier = "-"
