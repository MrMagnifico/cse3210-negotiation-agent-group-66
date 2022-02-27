#!/bin/sh
timeout 10 python -m geniusweb.simplerunner.NegoRunner test/resources/settings.json > /tmp/output.tst

OUTPUT=$(awk '/INFO:protocol ended normally: /{print}' /tmp/output.tst | sed 's/INFO:protocol ended normally: //g')
echo $OUTPUT
echo $OUTPUT | jq 
