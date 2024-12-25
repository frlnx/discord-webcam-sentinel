#!/bin/bash

if not [ $(id -u) = 0 ]; then
    echo "Please run this script as root"
    exit 1
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi

# Replace {pwd} with `pwd`
cat webcam-discord-sentinel.service | sed "s/{pwd}/$(pwd)/g" > /etc/systemd/system/webcam-discord-sentinel.service
systemctl enable webcam-discord-sentinel
