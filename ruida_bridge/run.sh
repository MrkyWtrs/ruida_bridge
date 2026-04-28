#!/usr/bin/with-contenv bashio

config_or_default() {
  local key="$1"
  local default="$2"
  local value

  value="$(bashio::config "$key" 2>/dev/null || true)"

  if [ -z "$value" ]; then
    echo "$default"
  else
    echo "$value"
  fi
}

export MQTT_HOST="$(config_or_default 'mqtt_host' 'core-mosquitto')"
export MQTT_PORT="$(config_or_default 'mqtt_port' '1883')"
export MQTT_USER="$(config_or_default 'mqtt_user' '')"
export MQTT_PASS="$(config_or_default 'mqtt_pass' '')"
export MQTT_TOPIC_PREFIX="$(config_or_default 'mqtt_topic_prefix' 'ruida')"
export MQTT_CLIENT_ID="$(config_or_default 'mqtt_client_id' 'ruida-ha-bridge')"
export HA_DISCOVERY_PREFIX="$(config_or_default 'ha_discovery_prefix' 'homeassistant')"

export RUIDA_IP="$(config_or_default 'ruida_ip' '0.0.0.0')"
export RUIDA_OVERRIDE_CONTROLLER_EXTENTS="$(config_or_default 'override_controller_extents' 'false')"
export RUIDA_PORT="$(config_or_default 'ruida_port' '50200')"
export RUIDA_LOCAL_PORT="$(config_or_default 'ruida_local_port' '40200')"
export RUIDA_MAX_X_MM="$(config_or_default 'ruida_max_x_mm' '0')"
export RUIDA_MAX_Y_MM="$(config_or_default 'ruida_max_y_mm' '0')"
export RUIDA_MAX_Z_MM="$(config_or_default 'ruida_max_z_mm' '0')"
export RUIDA_Z_BUTTON_STEP_MM="$(config_or_default 'ruida_z_button_step_mm' '1')"


export RUIDA_DEVICE_ID="$(config_or_default 'device_id' 'ruida_bridge')"
export RUIDA_DEVICE_NAME="$(config_or_default 'device_name' 'Ruida Bridge')"
export RUIDA_ENTITY_PREFIX="$(config_or_default 'entity_prefix' 'ruida')"


export RUIDA_WEB_PORT="8099"
export RUIDA_APP_VERSION="$(bashio::addon.version)"

python3 /web.py &
exec python3 /app.py
