#!/usr/bin/env python

import os
from time import sleep
import wiringpi
import paho.mqtt.client as paho
import sys

mqtt_host = os.environ.get('MQTT_HOST', '10.0.1.3')
mqtt_port = os.environ.get('MQTT_PORT', '1883')
topic_prefix = '/control/'

PWM_MODE_MS = 0
PWM_PIN=18
ROTATE_NEUTRAL = 90
PWM_RANGE = 1024
PWM_CLOCK = 375
TICK_S = 0.5

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

def on_connect(pahoClient, obj, rc):
    	# Once connected, hook into i/o events
    	client.subscribe(topic_prefix + 'rotate')
    	client.subscribe(topic_prefix + 'switch_off')
    	rotate_arm(ROTATE_NEUTRAL)
	sleep(TICK_S)
	wiringpi.pwmWrite(PWM_PIN, 0)


def on_message(client, userdata, msg):
	if (  msg.topic == topic_prefix + 'switch_off'):
		print "%s: switch off" % msg.topic 
		rotate_arm(180)
		sleep(TICK_S)
		rotate_arm(ROTATE_NEUTRAL)
		sleep(TICK_S)
		wiringpi.pwmWrite(PWM_PIN, 0)

	elif (msg.topic == topic_prefix + 'rotate'):
		# print "%s: rotate to:%s" % (msg.topic, float(msg.payload))
		rotate_arm(msg.payload)
		sleep(TICK_S)
		wiringpi.pwmWrite(PWM_PIN, 0)

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
	print "rotate to target angle: %s, duty-cycle: %s" % (angle, rotation)

client = paho.Client()

# Register callbacks
client.on_connect = on_connect
client.on_message = on_message

# Zero the servo
wiringpi.pwmWrite(PWM_PIN, 0)

# connect and loop
client.connect(mqtt_host, mqtt_port)

client.loop_start()

try:
	# connect and loop
	while True:
		# wiringpi.pwmWrite(PWM_PIN, rotation)
		sleep(TICK_S)

except KeyboardInterrupt:
	print "%s, cleaning up and exiting" % __file__
	client.loop_stop()
	wiringpi.pwmWrite(PWM_PIN, 0)
	wiringpi.pinMode(PWM_PIN, 0) # sets GPIO pin to input Mode

