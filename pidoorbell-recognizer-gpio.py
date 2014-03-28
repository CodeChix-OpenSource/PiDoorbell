#! /usr/bin/env python

# Copyright (C) 2013-2014 Rupa Dachere <rupa@codechix.org>>
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
#  Dependencies:
#	HC_SR04.py, piphoto.py, sms_auth_info.py,
#	dropbox_token.py, dropbox_uploader.sh
#	ffmpeg, fswebcam, raspistill
#
#  Takes photo or video.  Checks to see if USB webcam 
#	or RaspberryPi Camera module is present and automatically
#	uses the correct input device
#	Modifications by Akkana Peck - akkana@gmail.com
#

import sys, threading
sys.path.append("/home/pi/pycon2014/pidoorbell")
from subprocess import call, Popen, PIPE
from time import time, sleep
import datetime, argparse
import RPi.GPIO as GPIO
from HC_SR04 import init_HC_SR04, average_distance
from piphoto import take_still

# bunch of defines to tweak when needed

BASEDIR_FOR_PIDOORBELL_VIDEOS = "./dropbox-pidoorbell/"

MAX_TRIGGER_DISTANCE   = 30   # inches
MIN_TRIGGER_DISTANCE   = 0    # inches
VALID_PIC_THRESHOLD    = 5    # weak attempt at mitigating "noise" (butterfly/moth/damned spiders))
DEFAULT_LATENCY        = 20   # default secs to wait to compensate for network latency/bandwidth
DELAY_BETWEEN_VISITORS = 20   # delay between polling for visitors 

# picture modes - video capture (10 seconds) or photo
VIDEO = 1
PHOTO = 2

FFMPEG_CMD = "ffmpeg -f video4linux2 -s 320x240 -i /dev/video0 -f alsa -ar 22050 -ac 1 \
                 -i hw:1,0 -ab 48k -timelimit 10 ./dropbox-pidoorbell/"

SEND_NOTIFICATIONS_ALL   = "python ./send_notifications.py -m all -u"
SEND_NOTIFICATIONS_SMS   = "python ./send_notifications.py -m sms -u"
SEND_NOTIFICATIONS_TWEET = "python ./send_notifications.py -m tweet -u"

# Progress print stmts for demo's
PRINT_STARTING_VIDEOCLIP = "\n\n************************** STARTING VIDEOCLIP:   ************************ \n\n" 
PRINT_STOPPING_VIDEOCLIP = "\n\n**** ENDING VIDEOCLIP FOR - "
PRINT_UPLOAD_TO_DROPBOX  = "\n\n************************** UPLOADING TO DROPBOX: ************************ \n\n" 

class PiDoorbell_GPIO() :

    def run(self, interactive, latency, pic_mode, local_mode) :

        global BASEDIR_FOR_PIDOORBELL_VIDEOS, \
               MIN_TRIGGER_DISTANCE, MAX_TRIGGER_DISTANCE, \
               BASEPORT_FOR_SENSOR_DATA, BASEPORT_BAUD_RATE

        if not local_mode:
            import sms_auth_info

        valid_pic_count = 0

        try:
            init_HC_SR04()

            while True :
                data = average_distance()
                if not data :
                    continue

                if not interactive :
                    print data
                    continue

                print "Distance: %.1f inches" % data
                print data
                if int(data) <= MIN_TRIGGER_DISTANCE or int(data) >= MAX_TRIGGER_DISTANCE:
                    continue

                # There's an object in the target distance range
                print "******  DETECTED AN OBJECT AT --    ", data ,"-- INCHES ****** "

                valid_pic_count += 1

                if valid_pic_count < VALID_PIC_THRESHOLD:
                    continue

                # We have enough pics:
                # build pidoorbell_filename with date and timestamp
                now = datetime.datetime.now()

                if pic_mode == VIDEO:
                    pidoorbell_filename = "visitor-video-%d:%d:%d-%d:%d.mpg" % \
                        (now.year, now.month, now.day, now.hour, now.minute)
                    #take a video snippet 
                    take_videoclip_cmd = FFMPEG_CMD + pidoorbell_filename

                    print PRINT_STARTING_VIDEOCLIP

                    videoclip_cmd_rc = call(take_videoclip_cmd, shell=True)

                    print PRINT_STOPPING_VIDEOCLIP + pidoorbell_filename

                # default to photo
                else: 
                    pidoorbell_filename = "visitor-photo-%d:%d:%d-%d:%d.jpg" % \
                               (now.year, now.month, now.day, now.hour, now.minute)
                    # take a photo snippet
                    try:
                        take_still(BASEDIR_FOR_PIDOORBELL_VIDEOS+pidoorbell_filename, verbose=True)
                    except SystemError:
                        print "Couldn't take a photo"
                        continue

                #reset valid_pic_count
                valid_pic_count = 0

                if local_mode:
                    print "Local mode: not syncing to the outside world"
                    sleep(DELAY_BETWEEN_VISITORS)
                    continue

                # Not local mode, so proceed with dropbox and sms:
                print PRINT_UPLOAD_TO_DROPBOX

                sync_dropbox_cmd = "./dropbox_uploader.sh upload ./dropbox-pidoorbell/" + \
                    pidoorbell_filename + " "+ pidoorbell_filename
                process = Popen(sync_dropbox_cmd, shell=True)

                ## account for network latency 
                print "latency is %s " % latency
                sleep(float(latency))

                get_link_cmd = "./dropbox_uploader.sh share " + pidoorbell_filename

                p = Popen(get_link_cmd, stdout=PIPE, shell=True)
                (output, err) = p.communicate()

                # Send notifications using both Twilio (USA) and Twitter (worldwide)
                # for demo purposes.  Else, use "-m sms" for SMS, "-m tweet" for TWITTER
                # See definitions section for predefined vars to use (SEND_NOTIFICATIONS_SMS,
                # SEND_NOTIFICATIONS_TWEET)

                send_sms_cmd = SEND_NOTIFICATIONS_ALL + output
                sms_url_rc = call(send_sms_cmd, shell=True)

                #sleep for a short while before checking again
                sleep(DELAY_BETWEEN_VISITORS)

                print "Done sleeping  - I'm awake again!!!! "
                continue      

        except KeyboardInterrupt:
            # User pressed CTRL-C: reset GPIO settings.
            print "Cleaning up ..."
            GPIO.cleanup()

if __name__ == '__main__':

    # parse command line arguments to detect whether optional flags are set for
    #   interactive mode - "-i"
    #   latency - "-latency"
    #   picture mode - "-pic_mode"
    #   local mode (skip Twilio, Twitter and Dropbox) - '-local'

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", action="store_true", help="Indicates interactive run mode for PiDoorbell")
    parser.add_argument("-latency", type=int, help="Increase latency to account for wifi/network issues. Default: 20s")
    parser.add_argument("-pic_mode", type=int, choices=[1,2], help="Specify Video Capture (1) or Photo (2). Default: Photo (1)")
    parser.add_argument("-local", action="store_true", help="Run locally, don't use services like Dropbox, Twitter or Twilio")

    args = parser.parse_args()
    if args.latency:
        print "latency is: ", args.latency
        latency = args.latency
    else:
        latency = DEFAULT_LATENCY

    if args.pic_mode:
        print "picture mode is: ",args.pic_mode
        pic_mode = args.pic_mode
    else:
        pic_mode = PHOTO

    if args.local:
        print "picture mode is: ",args.pic_mode
        local_mode = args.local
    else:
        local_mode = False

    print "pic_mode is ", pic_mode, "local_mode is ", local_mode

    pidoorbell_gpio = PiDoorbell_GPIO()
    pidoorbell_gpio.run(args.i, latency, pic_mode, local_mode)

