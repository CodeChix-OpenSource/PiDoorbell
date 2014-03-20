#!/usr/bin/env python

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

# Download the twilio-python library from http://twilio.com/docs/libraries
# Use python-twitter to tweet - github.com/bear/python-twitter

import sys
sys.path.append("/home/pi/pycon2013/pidoorbell")
from twilio.rest import TwilioRestClient
import twitter
import optparse
import sms_auth_info
 
def send_sms(sms_url):

        client = TwilioRestClient(sms_auth_info.account_sid, sms_auth_info.auth_token)
 
        print '\n\n ************************ SENDING SMS WITH URL: ', sms_url ," *************************\n\n"

        body_url = "PiDoorbell for PyCon 2014! Visitor @FrontDoor: " + sms_url
        message = client.sms.messages.create(to="XXXYYYZZZZ", from_="XXXYYYZZZZ", body=body_url)

def send_tweet(tweet_url):

        api = twitter.Api(consumer_key=sms_auth_info.twitter_auth_key, consumer_secret=sms_auth_info.twitter_auth_secret, \
		access_token_key=sms_auth_info.twitter_access_key, access_token_secret=sms_auth_info.twitter_access_secret)

        api.VerifyCredentials()

        print '\n\n ************************ SENDING TWEET WITH URL: ', tweet_url ," *************************\n\n"

        post_message = "PiDoorbell for PyCon 2014 using GPIO!! Visitor @FrontDoor: " + tweet_url
        status = api.PostUpdate(post_message)
        #print status


#### MAIN ####

parser = optparse.OptionParser()

parser.add_option('-u', '--sms_url',
    action="store", dest="sms_url",
    help="sms url string", default="spam")

parser.add_option('-m', '--mode',
    action="store", dest="mode",
    help="mode: \"sms\" or \"tweet\" or \"all\"", default="spam")

options, args = parser.parse_args()

if options.sms_url == "spam" or options.mode == "spam":
  print "**** HEY! You forgot the URL or MODE for the SMS: ***"
  print "**** Usage: send_sms -m <sms/tweet/all> -u <URL_string> ***"
  sys.exit()


if options.mode == "sms":
    send_sms(options.sms_url)
elif options.mode == "tweet":
    send_tweet(options.sms_url)
else:
    send_sms(options.sms_url)
    send_tweet(options.sms_url)

