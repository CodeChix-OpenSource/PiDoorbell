#!/usr/bin/env python

# Raspberry Pi driver for the HC-SR04 ultrasonic rangefinder.
# Copyright (C) 2014 Akkana Peck <akkana@shallowsky.com>>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

# Adapted from code by Matt Hawkins of RaspberryPi-Spy.co.uk
# Wire the circuit as shown in
# http://www.raspberrypi-spy.co.uk/2013/01/ultrasonic-distance-measurement-using-python-part-2/
#
#  Modifications:
#
#      Author: Rupa Dachere
#      Date: March 19, 2014
#      Changes: 
#    	    	1. Fixed typo for call to measure_distance_cm()
#		2. Created measure_distance_in() for inches
#		3. Initialized stop in measure_distance_cm() and measure_distance_in()


import RPi.GPIO as GPIO
import time

GPIO_TRIGGER = 23
GPIO_ECHO    = 24

def init_HC_SR04():
    '''Call this once at the beginning of the script
       before measuring any distances.
    '''
    
    # Use BCM instead of physical pin numbering:
    GPIO.setmode(GPIO.BCM)

    # Set trigger and echo pins as output and input
    GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
    GPIO.setup(GPIO_ECHO, GPIO.IN)

    # Initialize trigger to low:
    GPIO.output(GPIO_TRIGGER, False)

def measure_distance_cm():
    '''Measure a single distance, in cemtimeters.
    '''
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
    start = time.time()
    stop = time.time()

    while GPIO.input(GPIO_ECHO) == 0:
        start = time.time()

    while GPIO.input(GPIO_ECHO) == 1:
        stop = time.time()

    # Convert to inches:
    return ((stop - start) * 34300)/2

def measure_distance_in():
    '''Measure a single distance, in inches.
    '''
    GPIO.output(GPIO_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)
    start = time.time()
    stop = time.time()

    while GPIO.input(GPIO_ECHO) == 0:
        start = time.time()

    while GPIO.input(GPIO_ECHO) == 1:
        stop = time.time()

    #print "In here 8: stop is %d start is %d" % (stop, start)

    # Convert to inches:
    return (((stop - start) * 34300)/2)*0.393701

def average_distance(samples=3):
    tot = 0.0
    for i in xrange(samples):
        tot += measure_distance_in()
        time.sleep(0.1)
    return tot / samples

if __name__ == '__main__':
    try:
        init_HC_SR04()
        while True:
            print "Distance: %.1f inches" % average_distance()
            time.sleep(1)
    except KeyboardInterrupt:
        # User pressed CTRL-C: reset GPIO settings.
        print "Cleaning up ..."
        GPIO.cleanup()
