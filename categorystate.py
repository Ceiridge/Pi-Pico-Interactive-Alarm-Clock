import globals
from iterstate import IterState

class CategoryState(IterState):
	identifier = "C"
	
	def enter(self, state_machine):
		self.keys = globals.permutate_list("GLOBALS", list(globals.GLOBALS.keys()))

	def execute(self, state_machine, buttons):
		if buttons[0] and buttons[1]:
			return ["idle"]
		elif buttons[2]:
			return ["read", self.keys[self.index]]
		else:
			super().execute(state_machine, buttons)
