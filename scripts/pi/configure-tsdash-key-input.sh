#!/bin/bash
set -euo pipefail

readonly CONFIG_URL="http://127.0.0.1:16680/index.html?pageId=pinConfig&action=saveFunction&functionName=Digital_Input&instanceId=KeyOnInput&SETTING_Function%20Name=KeyOnInput&SETTING_Platform%20ID=pi4j&SETTING_Connector%20ID=raspberrypi&SETTING_PIN%20Name=GPIO%2017&SETTING_OutputChannel%20Name=ignitionOn&SETTING_Active%20State=High&SETTING_PIN%20Pull%20Resistance=OFF&SETTING_Datalog%20Pin%20Active=true"

response=$(curl -fsS --max-time 10 "$CONFIG_URL")
if [[ $response != *"Settings Valid"* || $response != *"ignitionOn"* ]]; then
    echo "TSDash did not accept the virtual key input configuration." >&2
    exit 1
fi

echo "Saved TSDash KeyOnInput as AppEvent.ignitionOn."
echo "Restart TSDash to activate it: sudo systemctl restart getty@tty1"
