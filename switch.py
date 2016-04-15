#!/usr/bin/env python

import os
import time
import wiringpi
import simplejson as json
import sys
from Adafruit_IO import *

config_file = os.path.join(os.path.dirname(__file__), '.config')

aio_key = os.environ.get('AIO_KEY')
aio_userid = os.environ.get('AIO_USERNAME')
aio_switch_feedid = os.environ.get('AIO_FEED', 'switch')
aio_rotate_feedid = os.environ.get('AIO_ROTATE_FEED', 'rotate')

if os.path.isfile(config_file):
    with open(config_file) as data_file:
        data = json.load(data_file)
        if 'AIO_KEY' in data: 
            aio_key = data['AIO_KEY']
        if 'AIO_USERNAME' in data: 
            aio_userid = data['AIO_USERNAME']
        if 'AIO_FEED' in data: 
            aio_switch_feedid = data['AIO_FEED']
        if 'AIO_ROTATE_FEED' in data: 
            aio_rotate_feedid = data['AIO_ROTATE_FEED']
else:
    print "No config found at %s" % (config_file)
    sys.exit()
    
# for debug, we can also publish to a {feedid}_rotate channel to send degree values

IO_PIN=17
TICK_S = 0.5
switch_state = None
last_ts = time.time()
MESSAGE_DELIM = ';'

def on_switch_interrupt():
	global last_ts
	global switch_state
	time_now = time.time()
	print 'switch interrupt: %s since %s' % (time_now, last_ts)
	if (time_now - last_ts) >= 0.3:
		state = wiringpi.digitalRead(IO_PIN)
		if (state != switch_state):
			switch_state = state;
			msg = str(state) + MESSAGE_DELIM + str(time_now)
			print 'Switch interrupt: %s' % state
			print 'publishing to %s: %s' % (aio_switch_feedid, msg)
			client.publish(aio_switch_feedid, msg)
		last_ts = time_now


# can call wiringPiSetupSys() if we've previously exported GPIO pins
wiringpi.wiringPiSetupGpio()

# use external pullup
wiringpi.pinMode(IO_PIN, wiringpi.GPIO.INPUT)
wiringpi.wiringPiISR(IO_PIN, wiringpi.GPIO.INT_EDGE_BOTH, on_switch_interrupt)

def on_connect(aioClient):
    	# Once connected, hook into i/o events
    	aioClient.subscribe(aio_switch_feedid)

def on_message(aioClient, feed_id, msg):
	state = wiringpi.digitalRead(IO_PIN)
	print "%s: got switch msg: %s, current state is: %s" % (feed_id, msg, state) 

print 'Creating MQTTClient with userid %s, key: %s' % (aio_userid, aio_key)
client = MQTTClient(aio_userid, aio_key)

# Register callbacks
client.on_connect = on_connect
client.on_message = on_message

# connect and loop
client.connect()
client.loop_background()

try:
	# connect and loop
	while True:
		time.sleep(TICK_S)

except KeyboardInterrupt:
	print "%s, cleaning up and exiting" % __file__
	if client.is_connected(): 
		client._client.loop_stop()
	wiringpi.pinMode(IO_PIN, 0) # sets GPIO pin to input Mode

