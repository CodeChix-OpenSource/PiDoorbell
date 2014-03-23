#! /usr/bin/env python

# Copyright (C) 2013 Rupa Dachere <rupa@codechix.org>>
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

import sys, threading
sys.path.append("/home/pi/pycon2014/pidoorbell")
import subprocess
from subprocess import call, Popen
from time import time, sleep
import datetime, argparse
import sms_auth_info
import RPi.GPIO as GPIO
from hc_sr04 import init_HC_SR04, average_distance

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

FSWEBCAM_CMD = "fswebcam ./dropbox-pidoorbell/"

SEND_NOTIFICATIONS_ALL   = "python ./send_notifications.py -m all -u"
SEND_NOTIFICATIONS_SMS   = "python ./send_notifications.py -m sms -u"
SEND_NOTIFICATIONS_TWEET = "python ./send_notifications.py -m tweet -u"

# Progress print stmts for demo's
PRINT_STARTING_VIDEOCLIP = "\n\n************************** STARTING VIDEOCLIP:   ************************ \n\n" 
PRINT_STARTING_PHOTO = "\n\n************************** STARTING PHOTO:   ************************ \n\n" 
PRINT_STOPPING_VIDEOCLIP = "\n\n**** ENDING VIDEOCLIP FOR - "
PRINT_STOPPING_PHOTO = "\n\n**** ENDING PHOTO FOR - "
PRINT_UPLOAD_TO_DROPBOX  = "\n\n************************** UPLOADING TO DROPBOX: ************************ \n\n" 

def get_db_file_link(dropbox_file_name):

    from dropbox import client, rest, session

    # get the stored key from step one and use it
    token_file = open(sms_auth_info.DB_TOKENS)
    token_key,token_secret = token_file.read().split('|')
    token_file.close()

    # init the session and the client
    sess = session.DropboxSession(sms_auth_info.DB_APP_KEY,
                                  sms_auth_info.DB_APP_SECRET,
                                  sms_auth_info.DB_ACCESS_TYPE )
    sess.set_token(token_key,token_secret)

    client = client.DropboxClient(sess)

    return_dict = client.share(dropbox_file_name)

    print "return_dict is: ", return_dict

    print "URL to filename: " + dropbox_file_name + " is:  " + return_dict['url']

    return return_dict['url']


class PiDoorbell_GPIO() :

    def run(self, interactive, latency, pic_mode) :

        global BASEDIR_FOR_PIDOORBELL_VIDEOS, \
               MIN_TRIGGER_DISTANCE, MAX_TRIGGER_DISTANCE, \
               BASEPORT_FOR_SENSOR_DATA, BASEPORT_BAUD_RATE

        valid_pic_count = 0

        try:
            init_HC_SR04()

            while True :
                data = average_distance()
                if data :
                    if interactive :
                        print "Distance: %.1f inches" % data
                        print data
                        if int(data) > MIN_TRIGGER_DISTANCE and int(data) < MAX_TRIGGER_DISTANCE:

                            print "******  DETECTED AN OBJECT AT --    ", data ,"-- INCHES ****** "

                            valid_pic_count += 1

                            if valid_pic_count == VALID_PIC_THRESHOLD:

                                #build pidoorbell_filename with date and timestamp
                                now = datetime.datetime.now()

                                if pic_mode == VIDEO:
                                    pidoorbell_filename = "visitor-video-%d:%d:%d-%d:%d.mpg" % \
                                        (now.year, now.month, now.day, now.hour, now.minute)
                                    #take a video snippet 
                                    take_videoclip_cmd = FFMPEG_CMD + pidoorbell_filename

                                    print PRINT_STARTING_VIDEOCLIP

                                    videoclip_cmd_rc = call(take_videoclip_cmd, shell=True)

                                    print PRINT_UPLOAD_TO_DROPBOX

                                    # sync_dropbox_cmd = "./dropbox_uploader.sh upload ./dropbox-pidoorbell/" + \
                                                       #pidoorbell_filename + " "+ pidoorbell_filename

                                    #process = subprocess.Popen(sync_dropbox_cmd, shell=True)

                                    print PRINT_STOPPING_VIDEOCLIP + pidoorbell_filename

                                # default to photo
                                else: 
                                    pidoorbell_filename = "visitor-video-%d:%d:%d-%d:%d.jpg" % \
                                               (now.year, now.month, now.day, now.hour, now.minute)
                                    #take a photo snippet 
                                    take_photo_cmd = FSWEBCAM_CMD + pidoorbell_filename

                                    print PRINT_STARTING_PHOTO

                                    photo_cmd_rc = call(take_photo_cmd, shell=True)

                                    print PRINT_UPLOAD_TO_DROPBOX
                                    # print PRINT_STOPPING_PHOTO + pidoorbell_filename

                                    sync_dropbox_cmd = "./dropbox_uploader.sh upload ./dropbox-pidoorbell/" + \
                                                       pidoorbell_filename + " "+ pidoorbell_filename

                                process = subprocess.Popen(sync_dropbox_cmd, shell=True)

                                ## account for network latency 
                                print "latency is %s " % latency
                                sleep(float(latency))

                                #link_to_db_file = get_db_file_link(pidoorbell_filename) 

                                get_link_cmd = "./dropbox_uploader.sh share " + pidoorbell_filename

                                p = subprocess.Popen(get_link_cmd, stdout=subprocess.PIPE, shell=True)
                                (output, err) = p.communicate()

                                # Send notifications using both Twilio (USA) and Twitter (worldwide)
                                # for demo purposes.  Else, use "-m sms" for SMS, "-m tweet" for TWITTER
                                # See definitions section for predefined vars to use (SEND_NOTIFICATIONS_SMS,
                                # SEND_NOTIFICATIONS_TWEET)

                                #send_sms_cmd = SEND_NOTIFICATIONS_ALL + output
                                send_sms_cmd = SEND_NOTIFICATIONS_SMS + output
                                sms_url_rc = call(send_sms_cmd, shell=True)

                                #reset valid_pic_count
                                valid_pic_count = 0

                                #sleep for a short while before checking again
                                sleep(DELAY_BETWEEN_VISITORS)

                                print "Done sleeping  - I'm awake again!!!! "
                                continue      
                    else:  # not interactive
                        print data

        except KeyboardInterrupt:
            # User pressed CTRL-C: reset GPIO settings.
            print "Cleaning up ..."
            GPIO.cleanup()

if __name__ == '__main__':

    # parse command line arguments to detect whether optional flags are set for
    #   interactive mode - "-i"
    #   latency - "-latency"
    #   picture mode - "-pic_mode"

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", action="store_true", help="Indicates interactive run mode for PiDoorbell")
    parser.add_argument("-latency", type=int, help="Increase latency to account for wifi/network issues. Default: 20s")
    parser.add_argument("-pic_mode", type=int, choices=[1,2], help="Specify Video Capture (1) or Photo (2). Default: Photo (1)")

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

    pidoorbell_gpio = PiDoorbell_GPIO()
    pidoorbell_gpio.run(args.i, latency, pic_mode)

