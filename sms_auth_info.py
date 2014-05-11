#!/usr/bin/python

##
## ************************************************************************************
##      CodeChix PiDoorbell - Home Automation with RaspberryPi with optional Arduino
##      codechix.org - May the code be with you...
##              2013-2014
##**********************************************************************************
##
## License:       	GPLv 2.0
## Version:        	3.0
## Project/Library:	PiDoorbell
## Description:    	This file contains *sensitive* (**SECURE THIS INFO**) on your 
##                 	API Tokens and Secrets for Twitter, Twilio and Dropbox.
##			Please be extra careful with sharing this info.
##			The pidoorbell-recognizer and send_notifications scripts
##			use this file to connect to all the required services.
## Assumptions:    	N/A
## Testing:        	N/A
## Authors:        	Rupa Dachere
##
## Main Contact:   rupa@codechix.org
## Alt. Contact:   organizers@codechix.org
##*********************************************************************************
##

# Twilio authentication credentials
# The values should be in double quotes, i.e., "xyz"

account_sid = <Your Twilio account secure ID>
auth_token = <Your Twilio authentication token>

#Twitter authentication credentials
# The values should be in singl quotes, i.e., 'xyz'

twitter_auth_key = <Your Twitter authentication key>
twitter_auth_secret = <Your Twitter authentication secret>
twitter_access_key = <Your Twitter access key>
twitter_access_secret = <Your Twitter access secret>

# Dropbox app key and secret from the Dropbox dev site

DB_APP_KEY = <Your Dropbox application key>
DB_APP_SECRET = <Your Dropbox application secret>
DB_ACCESS_TYPE = 'app_folder'

# going to store the access info in this file
# Update the following file with the Dropbox token
# as the first and only line in the file

DB_TOKENS = 'dropbox_token.txt'

