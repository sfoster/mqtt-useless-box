IoT Useless Box
===============

An experiment to process input and control a servo using MQTT and Amazon's IoT services

Hardware
---------

* Raspberry Pi
* Mini servo motor (E.g Tower Pro Micro Servo SG90)
* SPST Toggle switch
* Jumper wires and optional 1k resistor

This project is built on a Raspberry Pi. I used a version 1, it should work equally well with any of the variants up to and including v2. The rPi has a single hardware PWM port which is necessary for smooth and accurate control of the servo

The servo has 3 wires. Colors can vary a little but the middle wire should always get +5V, brown or black is ground, green/yellow/white is the signal and should be connected to GPIO18 (pin 12 on my rPi). Optionally a 1K resistor between GPIO18 and the signal wire may help limit damage to the rPi if the servo misbehaves. 

The servo really needs it own power supply. If you use the 5V pins from the rPi, the voltage drop when it is active may cause the rPi to struggle and shutdown. Connect a 5V source (e.g separate USB supply, regulated battery or wall adapter/charger) by connecting the positive to the servo's positive wire, and connecting both the secondary and rPi's ground together. 

Install
-------

Flash the latest (Jessie at time of writing) Rasbian to an SD Card, and go through the normal setup. This project doesnt use any of the GUI, so you could use the minimal image. Do the usual apt-get update && apt-get upgrade and then install: 
```
    wget http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key && sudo apt-key add mosquitto-repo.gpg.key
    sudo wget -O /etc/apt/sources.list.d/mosquitto-jessie.list http://repo.mosquitto.org/debian/mosquitto-jessie.list

    sudo apt-get install python-pip python-dev mosquitto mosquitto-clients

    sudo pip install paho-mqtt wiringpi2
```

Run
---

To start the mosquitto (MQTT broker) service, `mosquitto --daemon`. To test this is working, you can start a listener e.g. `mosquitto_sub -t /some/topic` and publish a message throug the broker with `mosquitto_pub -t /some/topic -m the_message`. If you've got the mosquitto clients (or any MQTT client) installed on another machine you can publish from there also: `mosquitto_pub -h {hostname or IP of the rPi} -t /some/topic -m foo`. In both cases you should see the message show up in your subscriber. 

Start the servo sript with `sudo servo.py`. Currently it needs to run as root to access the GPIO pins. Now publish a message on /control/switch_off to activate the servo. It also listens for /control/rotate and you can pass a message payload of a value from 0-180.
 


