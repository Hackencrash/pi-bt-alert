#!/bin/bash

if [ "$1" = "on" ]; then
  echo 0 | sudo tee /sys/class/backlight/panel_backlight@0/bl_power >/dev/null
else
  echo 1 | sudo tee /sys/class/backlight/panel_backlight@0/bl_power >/dev/null
fi
