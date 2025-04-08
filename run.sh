#!/usr/bin/env bash
export SENSOR_NAME=$(jq -r .sensor /data/options.json)

if [ "$SENSOR_NAME" = "null" ] || [ -z "$SENSOR_NAME" ]; then
  echo "❌ SENSOR_NAME is not set in options.json!"
  exit 1
fi

echo "SENSOR_NAME from options.json: $SENSOR_NAME"

exec python /app/app.py
