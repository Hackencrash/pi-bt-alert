#!/bin/bash

MSG="$1"
LEVEL="${2:-info}"
DURATION="${3:-5}"
CAMERA_TIME="${4:-0}"

USER_ID=$(id -u emotion)
RUNTIME=/run/user/$USER_ID
STATE_FILE="/tmp/alert_state"

get_priority() {
  case "$1" in
    time) echo 0 ;;
    info) echo 1 ;;
    warning) echo 2 ;;
    critical) echo 3 ;;
    *) echo 1 ;;
  esac
}

NEW_PRIORITY=$(get_priority "$LEVEL")

if [ -f "$STATE_FILE" ]; then
  CURRENT_PRIORITY=$(cat "$STATE_FILE" 2>/dev/null || echo 1)
else
  CURRENT_PRIORITY=-1
fi

# Ignore lower-priority alerts
if [ "$NEW_PRIORITY" -lt "$CURRENT_PRIORITY" ]; then
  exit 0
fi

# Record the new active priority
echo "$NEW_PRIORITY" > "$STATE_FILE"

# Capture OLD alert PIDs BEFORE starting new one
OLD_PIDS=$(pgrep -f "/home/emotion/alert_display.py")

# Start NEW alert
sudo -u emotion \
  XDG_RUNTIME_DIR="$RUNTIME" \
  WAYLAND_DISPLAY=wayland-0 \
  DISPLAY=:0 \
  nohup python3 /home/emotion/alert_display.py "$MSG" "$LEVEL" "$DURATION" "$CAMERA_TIME" >/dev/null 2>&1 &

sleep 0.5

# Kill only OLD alerts
if [ -n "$OLD_PIDS" ]; then
  kill $OLD_PIDS 2>/dev/null
fi

/home/emotion/screen.sh on
