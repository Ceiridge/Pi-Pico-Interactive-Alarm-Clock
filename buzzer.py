import globals

from machine import Pin, PWM
import _thread
import utime

buzzer_pwm = None
multithreaded = True # For debug purposes

def start_buzzing(loud=True):
	global buzzer_pwm
	stop_buzzing()

	buzzer_pwm = PWM(Pin(globals.GLOBALS["Pins"]["BuzzerData"], Pin.OUT))
	buzzer_pwm.freq(globals.GLOBALS["Buzzer"]["Frequency"])
	if loud:
		resume_buzzing()
	else:
		pause_buzzing()

def resume_buzzing():
	global buzzer_pwm
	if buzzer_pwm != None:
		buzzer_pwm.duty_u16(int(globals.GLOBALS["Buzzer"]["DutyCycle%"] * (1.0 / 100.0) * 65535.0))

def pause_buzzing():
	global buzzer_pwm 
	if buzzer_pwm != None:
		buzzer_pwm.duty_u16(0)

def stop_buzzing():
	global buzzer_pwm 
	if buzzer_pwm != None:
		buzzer_pwm.deinit()
		buzzer_pin = Pin(globals.GLOBALS["Pins"]["BuzzerData"], Pin.OUT)
		buzzer_pin.value(0)

class BuzzerAlarm():
	running = True
	buzzing = False

	def __init__(self):
		if multithreaded:
			globals.GLOBAL_LOCKS["Thread"].acquire() # Only allow one thread
			try:
				_thread.start_new_thread(self.alarm_thread, (self, ))
			finally:
				globals.GLOBAL_LOCKS["Thread"].release()
		else:
			self.buzzing = True
			self.alarm_thread()

	def deinit(self):
		self.stop()
		self.running = False

	def start(self):
		self.buzzing = True
	
	def stop(self):
		self.buzzing = False

	def alarm_thread(self):
		globals.GLOBAL_LOCKS["Thread"].acquire() # Only allow one thread

		try:
			start_buzzing(loud=False)
			unit = globals.GLOBALS["Buzzer"]["BeepUnitMs"]

			while self.running:
				# Buzz sound pattern: I-I-I-I---- (each character is one unit)
				if self.buzzing:
					needs_cont = True

					for _ in range(4):
						resume_buzzing()
						if self.aware_sleep(unit): break
						pause_buzzing()
						if self.aware_sleep(unit): break
					else:
						needs_cont = False

					if needs_cont: continue
					if self.aware_sleep(unit * 3): continue

			stop_buzzing()
		finally:
			globals.GLOBAL_LOCKS["Thread"].release()
			pass

	def aware_sleep(self, ms):
		for _ in range(0, ms, 10):
			utime.sleep_ms(10)

			if not self.buzzing: # Should stop
				return True

		return False
