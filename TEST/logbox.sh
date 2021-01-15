#!/bin/bash

DATE=$(date +"%Y-%m-%d_%H%M")

raspistill -w 320 -h 240 -q 75 -o /home/pi/Desktop/TEST/LOGBOX_IMAGES/$DATE.jpg
