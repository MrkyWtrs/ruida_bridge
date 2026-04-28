import json
import os

def env_str(name: str, default: str) -> str:
    raw = os.environ.get(name, default)
    raw = str(raw).strip()
    if raw == "" or raw.lower() in ("null", "none"):
        return default
    return raw

def env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default))
    raw = str(raw).strip()
    if raw == "" or raw.lower() in ("null", "none"):
        return int(default)
    return int(raw)

import time
from threading import Lock

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request, send_from_directory

APP_VERSION = os.environ.get("RUIDA_APP_VERSION", "unknown")
MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = env_int("MQTT_PORT", 1883)
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")
MQTT_TOPIC_PREFIX = env_str("MQTT_TOPIC_PREFIX", "ruida")
CLIENT_ID = os.environ.get("MQTT_CLIENT_ID", "ruida-ha-bridge") + "-web"
WEB_PORT = int(os.environ.get("RUIDA_WEB_PORT", "8099"))
RUIDA_IP = os.environ.get("RUIDA_IP", "")
RUIDA_MAX_X_MM = os.environ.get("RUIDA_MAX_X_MM", "")
RUIDA_MAX_Y_MM = os.environ.get("RUIDA_MAX_Y_MM", "")
RUIDA_MAX_Z_MM = os.environ.get("RUIDA_MAX_Z_MM", "")
RUIDA_OVERRIDE_CONTROLLER_EXTENTS = str(os.environ.get("RUIDA_OVERRIDE_CONTROLLER_EXTENTS", "false")).strip().lower() in ("1", "true", "yes", "on", "enable", "enabled")

CMD_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/cmd"
STATE_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/status"
ATTR_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/attributes"
RESULT_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/result"
FILE_LIST_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/file_list"
PREVIEW_STATUS_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/preview_status"
ROTARY_STATE_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/rotary_enabled"
X_AXIS_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/axis/x"
Y_AXIS_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/axis/y"
Z_AXIS_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/axis/z"
XY_LOCATION_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/xy_location"
LASER_1_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/laser/1"
LASER_2_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/laser/2"

STATIC_DIR = "/static"
HA_PREVIEW_FILE = "/homeassistant/www/ruida_bridge/latest.png"

app = Flask(__name__, static_folder=None)
lock = Lock()
state = {
    "bridge": "unknown",
    "attributes": {},
    "last_result": {},
    "file_list": [],
    "preview": {},
    "rotary": "unknown",
    "axis": {"x": {}, "y": {}, "z": {}},
    "xy_location": {},
    "laser": {"1": {}, "2": {}},
    "updated": int(time.time()),
}


def decode_json(payload: bytes):
    try:
        return json.loads(payload.decode("utf-8"))
    except Exception:
        return None


def on_connect(client, userdata, flags, reason_code, properties):
    topics = [
        STATE_TOPIC,
        ATTR_TOPIC,
        RESULT_TOPIC,
        FILE_LIST_TOPIC,
        PREVIEW_STATUS_TOPIC,
        ROTARY_STATE_TOPIC,
        X_AXIS_TOPIC,
        Y_AXIS_TOPIC,
        Z_AXIS_TOPIC,
        XY_LOCATION_TOPIC,
        LASER_1_TOPIC,
        LASER_2_TOPIC,
    ]
    for topic in topics:
        client.subscribe(topic, qos=1)


def on_message(client, userdata, msg):
    topic = msg.topic
    raw_text = msg.payload.decode("utf-8", errors="replace")
    data = decode_json(msg.payload)

    with lock:
        if topic == STATE_TOPIC:
            state["bridge"] = raw_text
        elif topic == ATTR_TOPIC:
            state["attributes"] = data or {}
        elif topic == RESULT_TOPIC:
            state["last_result"] = data or {"raw": raw_text}
        elif topic == FILE_LIST_TOPIC:
            state["file_list"] = data if isinstance(data, list) else []
        elif topic == PREVIEW_STATUS_TOPIC:
            state["preview"] = data or {}
        elif topic == ROTARY_STATE_TOPIC:
            state["rotary"] = raw_text
        elif topic == X_AXIS_TOPIC:
            state["axis"]["x"] = data or {}
        elif topic == Y_AXIS_TOPIC:
            state["axis"]["y"] = data or {}
        elif topic == Z_AXIS_TOPIC:
            state["axis"]["z"] = data or {}
        elif topic == XY_LOCATION_TOPIC:
            state["xy_location"] = data or {}
        elif topic == LASER_1_TOPIC:
            state["laser"]["1"] = data or {}
        elif topic == LASER_2_TOPIC:
            state["laser"]["2"] = data or {}
        state["updated"] = int(time.time())


def publish_command(payload):
    if isinstance(payload, str):
        mqtt_client.publish(CMD_TOPIC, payload, qos=1, retain=False)
    else:
        mqtt_client.publish(CMD_TOPIC, json.dumps(payload), qos=1, retain=False)


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


def get_config_status():
    missing = []

    def positive_float(value):
        try:
            return float(str(value).strip()) > 0
        except Exception:
            return False

    if not MQTT_HOST.strip():
        missing.append("MQTT host")
    if not MQTT_USER.strip():
        missing.append("MQTT username")
    if not MQTT_PASS.strip():
        missing.append("MQTT password")
    if not RUIDA_IP.strip():
        missing.append("Ruida controller IP")
    if RUIDA_IP.strip() in {"0.0.0.0", "127.0.0.1", "localhost"}:
        missing.append("Ruida controller IP still appears to be a default/test value")
    if RUIDA_OVERRIDE_CONTROLLER_EXTENTS:
        if not positive_float(RUIDA_MAX_X_MM):
            missing.append("maximum X travel must be greater than 0 when controller extents are overridden")
        if not positive_float(RUIDA_MAX_Y_MM):
            missing.append("maximum Y travel must be greater than 0 when controller extents are overridden")
        if not positive_float(RUIDA_MAX_Z_MM):
            missing.append("maximum Z travel must be greater than 0 when controller extents are overridden")

    return {
        "configured": len(missing) == 0,
        "missing": missing,
        "message": "Ruida Bridge is configured." if not missing else "Ruida Bridge needs setup before use.",
    }


@app.get("/api/state")
def api_state():
    with lock:
        snapshot = json.loads(json.dumps(state))
    snapshot["preview_image_url"] = f"api/preview.png?v={int(time.time())}"
    snapshot["web_time"] = int(time.time())
    snapshot["app_version"] = APP_VERSION
    snapshot["config_status"] = get_config_status()
    return jsonify(snapshot)


@app.get("/api/files")
def api_files():
    with lock:
        files = json.loads(json.dumps(state.get("file_list", [])))
    return jsonify(files)


@app.get("/api/result")
def api_result():
    with lock:
        result = json.loads(json.dumps(state.get("last_result", {})))
    return jsonify(result)


@app.get("/api/preview")
def api_preview():
    with lock:
        preview = json.loads(json.dumps(state.get("preview", {})))
    return jsonify(preview)


@app.post("/api/command")
def api_command():
    data = request.get_json(silent=True) or {}
    cmd = str(data.get("cmd", "")).strip().lower()

    string_commands = {
        "home",
        "left",
        "right",
        "up",
        "down",
        "z_up",
        "z_down",
        "z_home",
        "file_list",
        "sync_files",
    }

    if cmd in string_commands:
        publish_command(cmd)
        return jsonify({"ok": True, "queued": True, "cmd": cmd})

    if cmd in ("jog_start", "jog_stop"):
        action = str(data.get("action", "")).strip().lower()
        valid_actions = {"left", "right", "up", "down", "z_up", "z_down"}
        if action not in valid_actions:
            return jsonify({"ok": False, "error": "unknown_jog_action", "cmd": cmd, "action": action}), 400
        publish_command({"cmd": cmd, "action": action})
        return jsonify({"ok": True, "queued": True, "cmd": cmd, "action": action})

    if cmd == "run_file_slot":
        slot = int(data.get("slot", 0))
        if slot < 1 or slot > 255:
            return jsonify({"ok": False, "error": "slot must be between 1 and 255", "cmd": cmd, "slot": slot}), 400
        publish_command({"cmd": "run_file_slot", "slot": slot})
        return jsonify({"ok": True, "queued": True, "cmd": cmd, "slot": slot})

    if cmd == "stop":
        publish_command({"cmd": "stop"})
        return jsonify({"ok": True, "queued": True, "cmd": cmd})

    if cmd == "rel_xy":
        publish_command({"cmd": "rel_xy", "dx": float(data.get("dx", 0)), "dy": float(data.get("dy", 0))})
        return jsonify({"ok": True, "queued": True, "cmd": cmd})

    if cmd == "abs_xy":
        publish_command({"cmd": "abs_xy", "x": float(data["x"]), "y": float(data["y"])})
        return jsonify({"ok": True, "queued": True, "cmd": cmd})

    if cmd == "go_to_z":
        publish_command({"cmd": "go_to_z", "z": float(data["z"])})
        return jsonify({"ok": True, "queued": True, "cmd": cmd, "z": float(data["z"])})

    if cmd == "download_file":
        publish_command({"cmd": "download_file", "slot": int(data["slot"]), "name": str(data.get("name", ""))})
        return jsonify({"ok": True, "queued": True, "cmd": cmd, "slot": int(data["slot"]), "name": str(data.get("name", ""))})

    if cmd == "sync_files":
        publish_command({"cmd": "sync_files"})
        return jsonify({"ok": True, "queued": True, "cmd": cmd})

    if cmd == "render_rd":
        fit_mode = str(data.get("fit_mode", "")).strip().lower()
        payload = {"cmd": "render_rd", "path": str(data["path"])}
        if fit_mode in ("geometry", "bed"):
            payload["fit_mode"] = fit_mode
        publish_command(payload)
        return jsonify({"ok": True, "queued": True, "cmd": cmd, "fit_mode": payload.get("fit_mode", "geometry")})

    if cmd == "set_rotary_enabled":
        enabled_raw = data.get("enabled", False)
        if isinstance(enabled_raw, bool):
            enabled = enabled_raw
        elif isinstance(enabled_raw, str):
            enabled = enabled_raw.strip().lower() in ("1", "true", "on", "yes", "enable", "enabled")
        else:
            enabled = bool(enabled_raw)

        publish_command({"cmd": "set_rotary_enabled", "enabled": enabled})
        return jsonify({"ok": True, "queued": True, "cmd": cmd, "enabled": enabled})

    if cmd == "set_rotary_diameter":
        diameter_mm = float(data["diameter_mm"])
        publish_command({"cmd": "set_rotary_diameter", "diameter_mm": diameter_mm})
        return jsonify({"ok": True, "queued": True, "cmd": cmd, "diameter_mm": diameter_mm})

    return jsonify({"ok": False, "error": "unknown_command", "cmd": cmd}), 400


@app.get("/api/preview.png")
def api_preview_png():
    if os.path.exists(HA_PREVIEW_FILE):
        return send_from_directory(os.path.dirname(HA_PREVIEW_FILE), os.path.basename(HA_PREVIEW_FILE))
    return "No preview image has been rendered yet", 404


mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
if MQTT_USER:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()

print(f"RUIDA WEB UI STARTED on port {WEB_PORT}", flush=True)
app.run(host="0.0.0.0", port=WEB_PORT, debug=False, use_reloader=False)
