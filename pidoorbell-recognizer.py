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

# Read the output of an Arduino which is constantly printing sensor output.
# See also
# http://www.arcfn.com/2009/06/arduino-sheevaplug-cool-hardware.html
# http://shallowsky.com

import sys, serial, threading
sys.path.append("/home/pi/pycon2013/pidoorbell")
import subprocess
from subprocess import call, Popen
from time import time, sleep
import datetime
import sms_auth_info

# bunch of defines to tweak when needed

BASEDIR_FOR_PIDOORBELL_VIDEOS = "./dropbox-pidoorbell/"
BASEPORT_FOR_SENSOR_DATA      = "/dev/ttyACM0"
BASEPORT_BAUD_RATE            = 115200

MAX_TRIGGER_DISTANCE   = 30   # inches
MIN_TRIGGER_DISTANCE   = 0    # inches
VALID_PIC_THRESHOLD    = 5    # weak attempt at mitigating "noise" (butterfly/moth/damned spiders))
DEFAULT_LATENCY        = 20   # default secs to wait to compensate for network latency/bandwidth
DELAY_BETWEEN_VISITORS = 20   # delay between polling for visitors 

FFMPEG_CMD = "ffmpeg -f video4linux2 -s 320x240 -i /dev/video0 -f alsa -ar 22050 -ac 1 \
		 -i hw:1,0 -ab 48k -timelimit 10 ./dropbox-pidoorbell/"

SEND_NOTIFICATIONS_ALL   = "python ./send_notifications.py -m all -u "
SEND_NOTIFICATIONS_SMS   = "python ./send_notifications.py -m sms -u "
SEND_NOTIFICATIONS_TWEET = "python ./send_notifications.py -m tweet -u "

# Progress print stmts for demo's
PRINT_STARTING_VIDEOCLIP = "\n\n************************** STARTING VIDEOCLIP:   ************************ \n\n" 
PRINT_UPLOAD_TO_DROPBOX  = "\n\n************************** UPLOADING TO DROPBOX: ************************ \n\n" 
PRINT_STOPPING_VIDEOCLIP = "\n\n**** ENDING VIDEOCLIP FOR - "

def get_db_file_link(dropbox_file_name):

	from dropbox import client, rest, session

	# get the stored key from step one and use it
	token_file = open(sms_auth_info.DB_TOKENS)
	token_key,token_secret = token_file.read().split('|')
	token_file.close()

	# init the session and the client
	sess = session.DropboxSession(sms_auth_info.DB_APP_KEY, sms_auth_info.DB_APP_SECRET, \
								sms_auth_info.DB_ACCESS_TYPE )
	sess.set_token(token_key,token_secret)

	client = client.DropboxClient(sess)

	return_dict = client.share(dropbox_file_name)

	print "URL to filename: " + dropbox_file_name + " is:  " + return_dict['url']

	return return_dict['url']


class Arduino(threading.Thread) :

    def run(self, interactive, latency) :

        global BASEDIR_FOR_PIDOORBELL_VIDEOS, MIN_TRIGGER_DISTANCE, MAX_TRIGGER_DISTANCE, \
		BASEPORT_FOR_SENSOR_DATA, BASEPORT_BAUD_RATE

        # Port may vary, so look for it:
        self.ser = serial.Serial(BASEPORT_FOR_SENSOR_DATA, BASEPORT_BAUD_RATE, timeout=800)
        if not self.ser :
            print "Couldn't open a serial port"
            sys.exit(1)
        print "Opened ", BASEPORT_FOR_SENSOR_DATA

        self.ser.flushInput()
	valid_pic_count = 0
        while True :
            data = self.ser.readline().strip()
            if data :
                if interactive :
                    print data
		    if int(data) > MIN_TRIGGER_DISTANCE and int(data) < MAX_TRIGGER_DISTANCE:

                       print "******  DETECTED AN OBJECT AT --    ", data ,"-- INCHES ****** "

		       valid_pic_count += 1

		       if valid_pic_count == VALID_PIC_THRESHOLD:

			  #build videoclip filename with date and timestamp
			  now = datetime.datetime.now()
			  videoclip_filename = "visitor-video-%d:%d:%d-%d:%d.mpg" % \
					   (now.year, now.month, now.day, now.hour, now.minute)


			  #take a video snippet and reset valid_pic_count
			  take_videoclip_cmd = FFMPEG_CMD + videoclip_filename

			  print PRINT_STARTING_VIDEOCLIP

			  videoclip_cmd_rc = call(take_videoclip_cmd, shell=True)

			  print PRINT_UPLOAD_TO_DROPBOX
  
			  sync_dropbox_cmd = "./dropbox-uploader.sh upload ./dropbox-pidoorbell/" + \
						   videoclip_filename + " "+videoclip_filename
		  	
			  process = subprocess.Popen(sync_dropbox_cmd, shell=True)

			  print PRINT_STOPPING_VIDEOCLIP + videoclip_filename

			  ## account for network latency 
			  print "latency is %s " % latency
			  sleep(float(latency))

			  link_to_db_file = get_db_file_link(videoclip_filename) 


			  # Send notifications using both Twilio (USA) and Twitter (worldwide)
			  # for demo purposes.  Else, use "-m sms" for SMS, "-m tweet" for TWITTER
			  # See definitions section for predefined vars to use (SEND_NOTIFICATIONS_SMS,
			  # SEND_NOTIFICATIONS_TWEET)

			  send_sms_cmd = SEND_NOTIFICATIONS_ALL + link_to_db_file
			  sms_url_rc = call(send_sms_cmd, shell=True)


			  valid_pic_count = 0
			  
			  #sleep for a short while before checking again
			  sleep(DELAY_BETWEEN_VISITORS)

			  print "Done sleeping  - I'm awake again!!!! "
		          continue	
                else:
                    print data

# If -i, run in interactive mode
if len (sys.argv) > 1 and sys.argv[1] == '-i' :
    interactive = True

    # latency settings so that we can tweak this for
    # for demo purposes depending on conference network
    # bandwidth
    if len(sys.argv) <= 2:
       latency = DEFAULT_LATENCY
    else:
       latency = sys.argv[2]
else :
    interactive = False

arduino = Arduino()
arduino.run(interactive, latency)
