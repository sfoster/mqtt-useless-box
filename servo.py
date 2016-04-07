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
    

PWM_MODE_MS = 0
PWM_PIN=18
ROTATE_NEUTRAL = 90
PWM_RANGE = 1024
PWM_CLOCK = 375
TICK_S = 0.5
MESSAGE_DELIM = '\t'

last_ts = 0

# can call wiringPiSetupSys() if we've previously exported GPIO pins
wiringpi.wiringPiSetupGpio()

# use PWM on port 18
wiringpi.pinMode(PWM_PIN, 2)
wiringpi.pwmSetMode(PWM_MODE_MS)
wiringpi.pwmSetClock(PWM_CLOCK)
wiringpi.pwmSetRange(PWM_RANGE)

rotation = ROTATE_NEUTRAL

def angle_to_duty_cycle(angle=0):
	# 2.5ms of 20ms pulse is full 180deg swing
	ubound = 0.1
	offset = 0.5/20 * PWM_RANGE
	# set duty cycle as 0-180deg expressed as 0-1024
	return int(offset + float(angle) / 180 * ubound * PWM_RANGE)

def on_connect(aioClient):
	global last_ts
    	rotate_arm(ROTATE_NEUTRAL)
	time.sleep(TICK_S)
	wiringpi.pwmWrite(PWM_PIN, 0)
    	# Once connected, hook into i/o events
    	aioClient.subscribe(aio_switch_feedid)
    	aioClient.subscribe(aio_rotate_feedid)
	print 'subscribing to feeds: %s, %s' % (aio_switch_feedid, aio_rotate_feedid)
	last_ts = time.time()

def on_message(aioClient, feed_id, msg):
	payload = msg.partition(MESSAGE_DELIM)
	if type(payload[2]) is '':
		print '%s, missing timestamp in payload: %s' % (feed_id, msg)
		return None
	try:
		global last_ts		
		value = float(payload[0])
		ts = float(payload[2])
		if ((feed_id == aio_switch_feedid) 
		and (ts > last_ts)  
		and (feed_id == aio_switch_feedid)  
	       	and (value == 1)
		):
			print "%s: switch is on, turn it off" % feed_id 
			rotate_arm(180)
			time.sleep(TICK_S)
			rotate_arm(ROTATE_NEUTRAL)
			time.sleep(TICK_S)
			wiringpi.pwmWrite(PWM_PIN, 0)
			last_ts = time.time()

		elif (
		(feed_id == aio_rotate_feedid) 
		and (ts > last_ts)):
			rotate_arm(value)
			time.sleep(TICK_S)
			wiringpi.pwmWrite(PWM_PIN, 0)
			last_ts = time.time()
	except ValueError:
		print "%s: bad switch message: %s" % msg 

def rotate_arm(angle=ROTATE_NEUTRAL):
	global rotation
	angle = float(angle)
	if (angle > 180):
		angle = 180 
	elif (angle < 0): 
		angle = 0 

 	target = angle_to_duty_cycle(angle)
	rotation = target
	wiringpi.pwmWrite(PWM_PIN, rotation)
	print "rotate to target angle: %s, duty-cycle: %s/1024" % (angle, rotation)

class MyMQTTClient(MQTTClient):
 def _mqtt_message(self, client, userdata, msg):
        print 'Client on_message called.'
        # Parse out the feed id and call on_message callback.
        # Assumes topic looks like "username/feeds/id"
	print "MyMQTTClient _mqtt_message handling %s: %s" % (msg.topic, msg.payload)

        parsed_topic = msg.topic.split('/')
        if self.on_message is not None and self._username == parsed_topic[0]:
            feed = parsed_topic[2]
            payload = '' if msg.payload is None else msg.payload.decode('utf-8')
            self.on_message(self, feed, payload)

client = MQTTClient(aio_userid, aio_key)
start_time = time.time()

# Register callbacks
client.on_connect = on_connect
client.on_message = on_message

# Zero the servo
wiringpi.pwmWrite(PWM_PIN, 0)

# connect and loop
client.connect()
client.loop_background()

try:
	# connect and loop
	while True:
		# wiringpi.pwmWrite(PWM_PIN, rotation)
		time.sleep(TICK_S)

except KeyboardInterrupt:
	print "%s, cleaning up and exiting" % __file__
	if client.is_connected(): 
		client._client.loop_stop()
	wiringpi.pwmWrite(PWM_PIN, 0)
	wiringpi.pinMode(PWM_PIN, 0) # sets GPIO pin to input Mode

