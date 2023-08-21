from states import State

class IterState(State):
	identifier = "#"
	
	needs_update = True
	keys = []
	index = 0

	def draw(self, state_machine, lcd):
		if self.needs_update:
			lcd.clear()
			lcd.move_to(0, 0)
			lcd.putstr(str(self.index) + " of " + str(len(self.keys) - 1))
			lcd.move_to(0, 1)
			lcd.putstr(str(self.keys[self.index]))

			self.needs_update = False
			return True

		return False

	def execute(self, state_machine, buttons):
		if buttons[0]:
			self.index -= 1
			self.needs_update = True
		elif buttons[1]:
			self.index += 1
			self.needs_update = True

		if self.needs_update:
			self.index %= len(self.keys)
