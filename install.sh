#!/bin/bash

sudo update-rc.d -f servo-service.sh remove
sudo install -D servo-service.sh /etc/init.d/servo-service.sh
sudo chmod +x /etc/init.d/servo-service.sh
sudo update-rc.d servo-service.sh defaults

sudo update-rc.d -f switch-service.sh remove
sudo install -D switch-service.sh /etc/init.d/switch-service.sh
sudo chmod +x /etc/init.d/switch-service.sh
sudo update-rc.d switch-service.sh defaults
