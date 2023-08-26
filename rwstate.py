import globals
from iterstate import IterState
import utime

class ReadState(IterState):
	identifier = "R"
	category_key = None

	def __init__(self, category_key, index=0):
		self.category_key = category_key
		self.index = index
	
	def enter(self, state_machine):
		self.keys = globals.permutate_list(self.category_key, list(globals.GLOBALS[self.category_key].keys()))

	def draw(self, state_machine, lcd):
		if self.needs_update:
			lcd.clear()
			lcd.move_to(0, 0)
			lcd.putstr(f"{str(self.index)}/{str(len(self.keys) - 1)} " + str(self.keys[self.index]))
			lcd.move_to(0, 1)
			lcd.putstr(str(globals.GLOBALS[self.category_key][self.keys[self.index]]))

			self.needs_update = False
			return True

		return False

	def execute(self, state_machine, buttons):
		if buttons[0] and buttons[1]:
			return ["category"]
		elif buttons[2]:
			return ["write", self.category_key, self.index]
		else:
			super().execute(state_machine, buttons)

class WriteState(IterState):
	identifier = "W"
	category_key = None

	our_value = 0
	increment = 1
	next_queue = []
	set_dirty_flag = True

	def __init__(self, category_key, index, next_queue=[], set_dirty_flag=True):
		self.category_key = category_key
		self.index = index
		self.next_queue = next_queue
		self.set_dirty_flag = set_dirty_flag 
	
	def enter(self, state_machine):
		self.keys = globals.permutate_list(self.category_key, list(globals.GLOBALS[self.category_key].keys()))
		state_machine.lcd.move_to(0, 0)
		state_machine.lcd.putstr(f"{str(self.index)}/{str(len(self.keys) - 1)} " + str(self.keys[self.index]))

		self.our_value = globals.GLOBALS[self.category_key][self.keys[self.index]]

	def draw(self, state_machine, lcd):
		if self.needs_update:
			lcd.move_to(0, 1)
			lcd.putstr("[" + str(self.our_value) + "] ")

			self.needs_update = False
			return True

		return False

	def modify_by(self, amount):
		self.our_value += amount * self.increment
		self.needs_update = True

	def modify_increment_by(self, increase, lcd):
		if increase:
			self.increment *= 10
		else:
			self.increment //= 10
		
		if self.increment < 1: self.increment = 1
		if self.increment > 1000000: self.increment = 1000000
		self.increment = int(self.increment)

		lcd.move_to(0, 1)
		lcd.putstr("<" + str(self.increment) + "> ")
		utime.sleep_ms(500)
		self.needs_update = True

	def execute(self, state_machine, buttons):
		if buttons[0] and buttons[1]:
			return ["category"] if len(self.next_queue) == 0 else ["idle"]
		elif buttons[0] and buttons[2]:
			self.modify_increment_by(False, state_machine.lcd)
		elif buttons[1] and buttons[2]:
			self.modify_increment_by(True, state_machine.lcd)
		elif buttons[2]: # Fully write
			globals.update_time()
			globals.GLOBALS[self.category_key][self.keys[self.index]] = self.our_value
			if self.set_dirty_flag:
				globals.GLOBALS_DIRTY["Dirty"] = True

			try:
				globals.apply_time()
			except Exception as ex:
				print(ex)
				state_machine.lcd.move_to(0, 0)
				state_machine.lcd.putstr(str(ex))
				utime.sleep_ms(1500)
			
			if len(self.next_queue) == 0:
				return ["read", self.category_key, self.index]
			else:
				queue_el = self.next_queue.pop(0)
				return ["idle"] if queue_el == None else ["write", queue_el[0], queue_el[1], self.next_queue, self.set_dirty_flag]
		elif buttons[0]:
			self.modify_by(-1)
		elif buttons[1]:
			self.modify_by(1)
