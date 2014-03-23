# Blink an LED on pin 18.
# Connect a low-ohm (like 360 ohm) resistor in series with the LED.

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

pin = 18

GPIO.setup(pin, GPIO.OUT)

while True:
    GPIO.output(pin, 0)
    time.sleep(.5)
    GPIO.output(pin, 1)
    time.sleep(.5)

