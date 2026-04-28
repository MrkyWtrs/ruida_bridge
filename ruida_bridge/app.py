from queue import SimpleQueue, Empty
from pathlib import Path
import json
import os
import socket
import time
import traceback
import shutil
import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw
print("RUIDA APP STARTED", flush=True)


DEVICE_ID = os.environ.get("RUIDA_DEVICE_ID", "ruida_bridge")
DEVICE_NAME = os.environ.get("RUIDA_DEVICE_NAME", "Ruida Bridge")
ENTITY_PREFIX = os.environ.get("RUIDA_ENTITY_PREFIX", "ruida")


def eid(name: str) -> str:
    return f"{ENTITY_PREFIX}_{name}"


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on", "enable", "enabled")


def env_str(name: str, default: str) -> str:
    raw = os.environ.get(name, default)
    raw = str(raw).strip()
    if raw == "" or raw.lower() in ("null", "none"):
        return default
    return raw

def env_int(name: str, default: int, min_value: int | None = None, max_value: int | None = None) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except Exception:
        value = default
    if min_value is not None:
        value = max(min_value, value)
    if max_value is not None:
        value = min(max_value, value)
    return value


def env_choice(name: str, default: str, choices: set[str]) -> str:
    value = os.environ.get(name, default).strip().lower()
    return value if value in choices else default


def env_rgb(name: str, default: tuple[int, int, int]) -> tuple[int, int, int] | tuple[int, int, int, int]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default

    named_colors = {
        "mediumblue": (0, 0, 205),
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "navy": (0, 0, 128),
        "darkblue": (0, 0, 139),
        "transparent": (0, 0, 0, 0),
    }

    key = raw.lower().replace(" ", "")
    if key in named_colors:
        return named_colors[key]

    if raw.startswith("#") and len(raw) == 7:
        try:
            return (int(raw[1:3], 16), int(raw[3:5], 16), int(raw[5:7], 16))
        except Exception:
            return default

    return default


def blend_rgb(a: tuple[int, int, int], b: tuple[int, int, int], b_weight: float) -> tuple[int, int, int]:
    a_weight = 1.0 - b_weight
    return tuple(max(0, min(255, int((av * a_weight) + (bv * b_weight)))) for av, bv in zip(a, b))
def env_float(name: str, default: float, min_value: float | None = None, max_value: float | None = None) -> float:
    raw = os.environ.get(name, str(default))
    try:
        value = float(str(raw).strip())
    except Exception:
        value = default

    if min_value is not None:
        value = max(min_value, value)
    if max_value is not None:
        value = min(max_value, value)

    return value

MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = env_int("MQTT_PORT", 1883)
MQTT_USER = os.environ.get("MQTT_USER", "")
MQTT_PASS = os.environ.get("MQTT_PASS", "")
MQTT_TOPIC_PREFIX = env_str("MQTT_TOPIC_PREFIX", "ruida")
CMD_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/cmd"
CLIENT_ID = os.environ.get("MQTT_CLIENT_ID", "ruida-ha-bridge")
HA_DISCOVERY_PREFIX = os.environ.get("HA_DISCOVERY_PREFIX", "homeassistant")
RUIDA_IP = os.environ.get("RUIDA_IP", "0.0.0.0")
RUIDA_PORT = env_int("RUIDA_PORT", 50200)
RUIDA_LOCAL_PORT = env_int("RUIDA_LOCAL_PORT", 40200)
STATE_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/status"
ATTR_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/attributes"
RESULT_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/result"
ROTARY_STATE_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/rotary_enabled"
FILE_LIST_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/file_list"
PREVIEW_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/preview"
ARCHIVE_DIR = Path("/config/images")
HA_PREVIEW_DIR = Path("/homeassistant/www/ruida_bridge")
HA_PREVIEW_FILE = HA_PREVIEW_DIR / "latest.png"
HA_PREVIEW_URL = "/local/ruida_bridge/latest.png"
MAX_X_MM = env_float("RUIDA_MAX_X_MM", 0)
MAX_Y_MM = env_float("RUIDA_MAX_Y_MM", 0)

PREVIEW_FIT_MODE = env_choice("RUIDA_PREVIEW_FIT_MODE", "geometry", {"geometry", "bed"})
PREVIEW_SHOW_GRID = env_bool("RUIDA_PREVIEW_SHOW_GRID", True)
PREVIEW_SHOW_POINTS = env_bool("RUIDA_PREVIEW_SHOW_POINTS", False)
PREVIEW_SHOW_BOUNDS = env_bool("RUIDA_PREVIEW_SHOW_BOUNDS", True)
PREVIEW_SHOW_LABELS = env_bool("RUIDA_PREVIEW_SHOW_LABELS", True)
PREVIEW_LINE_WIDTH = env_int("RUIDA_PREVIEW_LINE_WIDTH", 15, 1, 20)
PREVIEW_BACKGROUND_RGB = env_rgb("RUIDA_PREVIEW_BACKGROUND", (0, 0, 205))
PREVIEW_FOREGROUND_RGB = env_rgb("RUIDA_PREVIEW_FOREGROUND", (255, 255, 255))
PREVIEW_GRID_RGB = blend_rgb(PREVIEW_BACKGROUND_RGB, PREVIEW_FOREGROUND_RGB, 0.22)
PREVIEW_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/preview"
PREVIEW_IMAGE_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/preview_image"
PREVIEW_STATUS_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/preview_status"
X_AXIS_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/axis/x"
Y_AXIS_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/axis/y"
Z_AXIS_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/axis/z"
XY_LOCATION_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/xy_location"
LASER_1_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/laser/1"
LASER_2_TOPIC = f"{MQTT_TOPIC_PREFIX}/bridge/laser/2"
LASER_1_ENABLE_SETTING_ID = 0x0010
LASER_2_ENABLE_SETTING_ID = 0x0016
LASER_ENABLE_BIT = 0x2000



# Archive/debug renders live in addon_config storage.
PREVIEW_DIR = Path("/config/images")
DOWNLOAD_DIR = Path("/homeassistant/www/ruida_bridge/downloads")
DOWNLOAD_RAW_DEBUG = env_bool("RUIDA_DOWNLOAD_RAW_DEBUG", False)

# Stable Home Assistant preview image lives in HA www.
HA_PREVIEW_DIR = Path("/homeassistant/www/ruida_bridge")
HA_PREVIEW_FILE = HA_PREVIEW_DIR / "latest.png"
HA_PREVIEW_URL = "/local/ruida_bridge/latest.png"


Z_BUTTON_STEP_MM = env_int("RUIDA_Z_BUTTON_STEP_MM", 1)
GO_TO_Z_MAX_DELTA_MM = env_float("RUIDA_GO_TO_Z_MAX_DELTA_MM", 10.0, 0.1, 100.0)
GO_TO_Z_ALLOW_OUT_OF_RANGE = env_bool("RUIDA_GO_TO_Z_ALLOW_OUT_OF_RANGE", False)
ROTARY_ENABLE_SETTING_ID = 0x0226
rotary_enabled_state = None

AXIS_SETTING_KEYS = {
    "x_max_speed", "x_max_travel", "x_home_offset",
    "y_max_speed", "y_max_travel", "y_home_offset",
    "z_max_speed", "z_max_travel", "z_home_offset",
}

LASER_SETTING_KEYS = {
    "laser_1_frequency", "laser_1_minimum_power", "laser_1_maximum_power",
    "laser_2_frequency", "laser_2_minimum_power", "laser_2_maximum_power",
}

MACHINE_SETTINGS = [
    {"id": 0x0221, "key": "diameter", "name": "Rotary Diameter", "unit": "mm", "icon": "mdi:diameter"},
    {"id": 0x020E, "key": "focus_distance", "name": "Focus distance", "unit": "mm", "icon": "mdi:focus-field"},
    {"id": 0x0023, "key": "x_max_speed", "name": "X max speed", "unit": "mm/s", "icon": "mdi:axis-x-arrow"},
    {"id": 0x0026, "key": "x_max_travel", "name": "X max travel", "unit": "mm", "icon": "mdi:axis-x-arrow"},
    {"id": 0x002A, "key": "x_home_offset", "name": "X home offset", "unit": "mm", "icon": "mdi:axis-x-arrow"},
    {"id": 0x0033, "key": "y_max_speed", "name": "Y max speed", "unit": "mm/s", "icon": "mdi:axis-y-arrow"},
    {"id": 0x0036, "key": "y_max_travel", "name": "Y max travel", "unit": "mm", "icon": "mdi:axis-y-arrow"},
    {"id": 0x003A, "key": "y_home_offset", "name": "Y home offset", "unit": "mm", "icon": "mdi:axis-y-arrow"},
    {"id": 0x0043, "key": "z_max_speed", "name": "Z max speed", "unit": "mm/s", "icon": "mdi:axis-z-arrow"},
    {"id": 0x0046, "key": "z_max_travel", "name": "Z max travel", "unit": "mm", "icon": "mdi:axis-z-arrow"},
    {"id": 0x004A, "key": "z_home_offset", "name": "Z home offset", "unit": "mm", "icon": "mdi:axis-z-arrow"},
    {"id": 0x0012, "key": "laser_1_minimum_power", "name": "Laser 1 minimum power", "unit": "%", "icon": "mdi:laser-pointer"},
    {"id": 0x0013, "key": "laser_1_maximum_power", "name": "Laser 1 maximum power", "unit": "%", "icon": "mdi:laser-pointer"},
    {"id": 0x0011, "key": "laser_1_frequency", "name": "Laser 1 frequency", "unit": "Hz", "icon": "mdi:sine-wave"},
    {"id": 0x0018, "key": "laser_2_minimum_power", "name": "Laser 2 minimum power", "unit": "%", "icon": "mdi:laser-pointer"},
    {"id": 0x0019, "key": "laser_2_maximum_power", "name": "Laser 2 maximum power", "unit": "%", "icon": "mdi:laser-pointer"},
    {"id": 0x0017, "key": "laser_2_frequency", "name": "Laser 2 frequency", "unit": "Hz", "icon": "mdi:sine-wave"},
]

HOME_COMMANDS = [
    bytes.fromhex("c9020000060d20"),
    bytes.fromhex("c6010000"),
    bytes.fromhex("c6210000"),
    bytes.fromhex("d0298989d9100000000000000000000000"),
]

LEFT_COMMANDS = [
    bytes.fromhex("c9020000060d20"),
    bytes.fromhex("c6010000"),
    bytes.fromhex("c6210000"),
    bytes.fromhex("d900020f7f7f3170"),
]

RIGHT_COMMANDS = [
    bytes.fromhex("c9020000060d20"),
    bytes.fromhex("c6010000"),
    bytes.fromhex("c6210000"),
    bytes.fromhex("d900020000004e10"),
]

UP_COMMANDS = [
    bytes.fromhex("c9020000060d20"),
    bytes.fromhex("c6010000"),
    bytes.fromhex("c6210000"),
    bytes.fromhex("d901020f7f7f3170"),
]

DOWN_COMMANDS = [
    bytes.fromhex("c9020000060d20"),
    bytes.fromhex("c6010000"),
    bytes.fromhex("c6210000"),
    bytes.fromhex("d901020000004e10"),
]

COMMAND_MAP = {
    "home": HOME_COMMANDS,
    "left": LEFT_COMMANDS,
    "right": RIGHT_COMMANDS,
    "up": UP_COMMANDS,
    "down": DOWN_COMMANDS,
}

BUTTON_META = {
    "home": {
        "name": "Home Machine",
        "unique_id": eid("home_machine"),
        "icon": "mdi:home-import-outline",
    },
    "left": {
        "name": "Jog Left",
        "unique_id": eid("jog_left"),
        "icon": "mdi:arrow-left-bold",
    },
    "right": {
        "name": "Jog Right",
        "unique_id": eid("jog_right"),
        "icon": "mdi:arrow-right-bold",
    },
    "up": {
        "name": "Jog Up",
        "unique_id": eid("jog_up"),
        "icon": "mdi:arrow-up-bold",
    },
    "down": {
        "name": "Jog Down",
        "unique_id": eid("jog_down"),
        "icon": "mdi:arrow-down-bold",
    },
    "z_up": {
        "name": "Jog Z Up",
        "unique_id": eid("jog_z_up"),
        "icon": "mdi:arrow-up-bold-box",
    },
    "z_down": {
        "name": "Jog Z Down",
        "unique_id": eid("jog_z_down"),
        "icon": "mdi:arrow-down-bold-box",
    },
    "file_list": {
        "name": "Get File List",
        "unique_id": eid("get_file_list"),
        "icon": "mdi:file-document-multiple-outline",
    },
}

REL_PACKET_MAP = {
    "x": {
        100: {
            "pos": "03 b5 52 89 8b 89 89 8f 05 a9",
            "neg": "04 39 52 89 8b 07 77 71 fb e9",
        },
        5: {
            "pos": "03 b1 52 89 8b 89 89 89 2f 81",
            "neg": "04 1d 52 89 8b 07 77 77 d1 f1",
        },
        2: {
            "pos": "03 e1 52 89 8b 89 89 89 07 d9",
            "neg": "04 0d 52 89 8b 07 77 77 f9 b9",
        },
        1: {
            "pos": "03 f1 52 89 8b 89 89 89 0f e1",
            "neg": "03 dd 52 89 8b 07 77 77 f1 91",
        },
    },
    "y": {
        100: {
            "pos": "03 35 52 09 8b 89 89 8f 05 a9",
            "neg": "03 b9 52 09 8b 07 77 71 fb e9",
        },
        5: {
            "pos": "03 31 52 09 8b 89 89 89 2f 81",
            "neg": "03 9d 52 09 8b 07 77 77 d1 f1",
        },
        2: {
            "pos": "03 61 52 09 8b 89 89 89 07 d9",
            "neg": "03 8d 52 09 8b 07 77 77 f9 b9",
        },
        1: {
            "pos": "03 71 52 09 8b 89 89 89 0f e1",
            "neg": "03 5d 52 09 8b 07 77 77 f1 91",
        },
    },
    "z": {
        100: {
            "pos": "03 b7 52 8b 8b 89 89 8f 05 a9",
            "neg": "04 3b 52 8b 8b 07 77 71 fb e9",
        },
        5: {
            "pos": "03 b3 52 8b 8b 89 89 89 2f 81",
            "neg": "04 1f 52 8b 8b 07 77 77 d1 f1",
        },
        2: {
            "pos": "03 e3 52 8b 8b 89 89 89 07 d9",
            "neg": "04 0f 52 8b 8b 07 77 77 f9 b9",
        },
        1: {
            "pos": "03 f3 52 8b 8b 89 89 89 0f e1",
            "neg": "03 df 52 8b 8b 07 77 77 f1 91",
        },
    },
}


CONTINUOUS_JOG_MAP = {
    "left": {
        "prep": "c9020000060d20",
        "start": "d9d820",
        "stop": "d9d830",
    },
    "right": {
        "prep": "c9020000060d20",
        "start": "d9d821",
        "stop": "d9d831",
    },
    "up": {
        "prep": "c9020000060d20",
        "start": "d9d822",
        "stop": "d9d832",
    },
    "down": {
        "prep": "c9020000060d20",
        "start": "d9d823",
        "stop": "d9d833",
    },
    "z_up": {
        "prep": "c9020000030650",
        "start": "d824",
        "stop": "d834",
    },
    "z_down": {
        "prep": "c9020000030650",
        "start": "d825",
        "stop": "d835",
    },
}

command_queue = SimpleQueue()
current_x_mm = None
current_y_mm = None
current_z_mm = None
cached_settings = {}
settings_loaded = False

def decode_ruida_u35(data: bytes) -> int:
    """Decode a 5-byte Ruida unsigned value using 7-bit payload bytes."""
    if len(data) != 5:
        raise ValueError(f"Expected 5 bytes, got {len(data)}")

    value = 0
    for b in data:
        value = (value << 7) | (b & 0x7F)
    return value


def format_runtime_ms(ms: int) -> str:
    """Format milliseconds as M:SS.mmm."""
    minutes, remainder = divmod(ms, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{minutes}:{seconds:02d}.{millis:03d}"


def publish_result(ok: bool, **data) -> None:
    payload = {"ok": ok, **data}
    client.publish(RESULT_TOPIC, json.dumps(payload), qos=1, retain=False)


def publish_preview(payload: dict) -> None:
    client.publish(PREVIEW_TOPIC, json.dumps(payload), qos=1, retain=True)


def publish_preview_image_file() -> None:
    if HA_PREVIEW_FILE.exists():
        client.publish(PREVIEW_IMAGE_TOPIC, HA_PREVIEW_FILE.read_bytes(), qos=1, retain=True)


def axis_payload(axis: str, position_mm, settings: dict, timestamp: int) -> dict:
    axis_lower = axis.lower()
    return {
        "axis": axis.upper(),
        "position_mm": position_mm,
        "offset_mm": settings.get(f"{axis_lower}_home_offset"),
        "max_speed_mm_s": settings.get(f"{axis_lower}_max_speed"),
        "max_travel_mm": settings.get(f"{axis_lower}_max_travel"),
        "timestamp": timestamp,
    }


def laser_payload(laser_num: int, enabled, enable_raw, settings: dict, timestamp: int) -> dict:
    prefix = f"laser_{laser_num}"
    return {
        "laser": laser_num,
        "enabled": enabled,
        "state": "ON" if enabled else "OFF",
        "enable_raw": enable_raw,
        "frequency_hz": settings.get(f"{prefix}_frequency"),
        "minimum_power_percent": settings.get(f"{prefix}_minimum_power"),
        "maximum_power_percent": settings.get(f"{prefix}_maximum_power"),
        "timestamp": timestamp,
    }


def format_xy_location(x_mm, y_mm) -> str:
    if x_mm is None or y_mm is None:
        return "unknown"
    return f"{x_mm:.2f}x, {y_mm:.2f}y"


def swizzle_byte(b: int, magic: int = 0x88) -> int:
    b ^= (b >> 7) & 0xFF
    b ^= (b << 7) & 0xFF
    b ^= (b >> 7) & 0xFF
    b ^= magic
    b = (b + 1) & 0xFF
    return b


def unswizzle_byte(b: int, magic: int = 0x88) -> int:
    b = (b - 1) & 0xFF
    b ^= magic
    b ^= (b >> 7) & 0xFF
    b ^= (b << 7) & 0xFF
    b ^= (b >> 7) & 0xFF
    return b


def swizzle(data: bytes) -> bytes:
    return bytes(swizzle_byte(b) for b in data)


def unswizzle(data: bytes) -> bytes:
    return bytes(unswizzle_byte(b) for b in data)


def checksum(data: bytes) -> int:
    return sum(data) & 0xFFFF


def build_udp_packet(command: bytes) -> bytes:
    body = swizzle(command)
    csum = checksum(body)
    return bytes([(csum >> 8) & 0xFF, csum & 0xFF]) + body


def query(sock: socket.socket, cmd: bytes) -> bytes:
    sock.sendto(build_udp_packet(cmd), (RUIDA_IP, RUIDA_PORT))
    sock.recvfrom(4096)  # ack
    reply, _ = sock.recvfrom(4096)
    return unswizzle(reply)


def query_setting(sock: socket.socket, setting_id: int) -> bytes:
    return query(sock, bytes([0xDA, 0x00, (setting_id >> 8) & 0xFF, setting_id & 0xFF]))


def tail_u32(reply: bytes) -> int:
    if not reply or len(reply) < 5:
        return 0

    value_bytes = reply[-5:]
    value = 0
    for b in value_bytes:
        value = (value << 7) | (b & 0x7F)
    return value


def decode_status_text(b1: int, b2: int) -> str:
    if b1 == 0 and b2 == 0:
        return "Idle"
    if b1 == 12 and b2 == 0:
        return "Idle"
    if b1 == 8 and b2 == 1:
        return "Running"
    if b1 == 8 and b2 == 3:
        return "Paused"
    return f"Unknown ({b1}/{b2})"


def setting_value_from_raw(setting: dict, raw: int):
    key = setting["key"]

    integer_keys = {
        "pulses_per_rotation",
    }

    percent_whole_keys = {
        "laser_1_minimum_power",
        "laser_1_maximum_power",
        "laser_2_minimum_power",
        "laser_2_maximum_power",
    }

    if key in integer_keys:
        return int(round(raw / 1000))

    if key in percent_whole_keys:
        return raw

    return round(raw / 1000, 2)


def send_ruida_packet(hex_payload: str) -> None:
    payload = bytes.fromhex(hex_payload)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(payload, (RUIDA_IP, RUIDA_PORT))


def send_ruida_command(command_hex: str) -> None:
    command = bytes.fromhex(command_hex)
    payload = build_udp_packet(command)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(payload, (RUIDA_IP, RUIDA_PORT))


def send_continuous_jog(action: str, phase: str) -> None:
    action = str(action or "").strip().lower()
    phase = str(phase or "").strip().lower()

    if action not in CONTINUOUS_JOG_MAP:
        raise ValueError(f"unsupported continuous jog action: {action}")

    if phase not in ("start", "stop"):
        raise ValueError(f"unsupported continuous jog phase: {phase}")

    jog = CONTINUOUS_JOG_MAP[action]

    if phase == "start":
        send_ruida_command(jog["prep"])
        time.sleep(0.10)

        send_ruida_command(jog["start"])
        return

    send_ruida_command(jog["stop"])


def send_relative_axis(axis: str, delta_mm: float) -> None:
    if axis not in REL_PACKET_MAP:
        raise ValueError(f"unsupported axis: {axis}")

    packet_set = REL_PACKET_MAP[axis]
    packet_delay_s = 0.05 if axis == "z" else 0.2

    for step in (100, 5, 2, 1):
        while delta_mm >= step:
            send_ruida_packet(packet_set[step]["pos"])
            time.sleep(packet_delay_s)
            delta_mm -= step
        while delta_mm <= -step:
            send_ruida_packet(packet_set[step]["neg"])
            time.sleep(packet_delay_s)
            delta_mm += step


def send_rel_xy(dx_mm: float, dy_mm: float) -> None:
    send_relative_axis("x", dx_mm)
    send_relative_axis("y", dy_mm)


def send_z_button_move(direction: str) -> None:
    if direction == "up":
        send_relative_axis("z", -float(Z_BUTTON_STEP_MM))
    elif direction == "down":
        send_relative_axis("z", float(Z_BUTTON_STEP_MM))
    else:
        raise ValueError(f"unsupported Z button direction: {direction}")


def send_abs_z(target_z_mm: float) -> dict:
    if current_z_mm is None:
        return {"ok": False, "error": "current_z_unknown"}

    target_z_mm = float(target_z_mm)
    current_z = float(current_z_mm)
    z_max = cached_settings.get("z_max_travel")

    if not GO_TO_Z_ALLOW_OUT_OF_RANGE and target_z_mm < 0:
        return {"ok": False, "error": "z_target_below_zero", "target_z_mm": target_z_mm}

    if not GO_TO_Z_ALLOW_OUT_OF_RANGE and z_max is not None and float(z_max) > 0 and target_z_mm > float(z_max):
        return {
            "ok": False,
            "error": "z_target_above_max_travel",
            "target_z_mm": target_z_mm,
            "z_max_travel_mm": float(z_max),
        }

    delta_z = round(target_z_mm - current_z, 3)

    if abs(delta_z) < 0.005:
        return {
            "ok": True,
            "cmd": "go_to_z",
            "target_z_mm": round(target_z_mm, 3),
            "current_z_mm": round(current_z, 3),
            "delta_z_mm": 0.0,
            "skipped": True,
            "reason": "already_at_target",
        }

    if abs(delta_z) > GO_TO_Z_MAX_DELTA_MM:
        return {
            "ok": False,
            "error": "z_delta_exceeds_limit",
            "target_z_mm": round(target_z_mm, 3),
            "current_z_mm": round(current_z, 3),
            "delta_z_mm": delta_z,
            "max_delta_mm": GO_TO_Z_MAX_DELTA_MM,
        }

    send_relative_axis("z", delta_z)

    return {
        "ok": True,
        "cmd": "go_to_z",
        "target_z_mm": round(target_z_mm, 3),
        "start_z_mm": round(current_z, 3),
        "delta_z_mm": delta_z,
        "max_delta_mm": GO_TO_Z_MAX_DELTA_MM,
    }


def encode_ruida_u35(value: int) -> bytes:
    if value < 0:
        raise ValueError("value must be >= 0")

    return bytes([
        (value >> 28) & 0x7F,
        (value >> 21) & 0x7F,
        (value >> 14) & 0x7F,
        (value >> 7) & 0x7F,
        value & 0x7F,
    ])


def build_abs_xy_command(x_mm: float, y_mm: float) -> bytes:
    x_units = int(round(x_mm * 1000))
    y_units = int(round(y_mm * 1000))
    return b"\xD9\x10\x00" + encode_ruida_u35(x_units) + encode_ruida_u35(y_units)


def build_abs_xy_udp_payload(x_mm: float, y_mm: float) -> bytes:
    command = build_abs_xy_command(x_mm, y_mm)
    return build_udp_packet(command)


def send_abs_xy(x_mm: float, y_mm: float) -> None:
    payload = build_abs_xy_udp_payload(x_mm, y_mm)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(payload, (RUIDA_IP, RUIDA_PORT))


def send_command(sock: socket.socket, cmd: bytes) -> bytes:
    sock.sendto(build_udp_packet(cmd), (RUIDA_IP, RUIDA_PORT))
    ack, _ = sock.recvfrom(4096)
    return unswizzle(ack)


def send_command_burst(sock: socket.socket, commands: list[bytes]) -> list[str]:
    ack_hex = []
    for cmd in commands:
        ack = send_command(sock, cmd)
        ack_hex.append(ack.hex())
    return ack_hex


def ruida_scramble_byte(b: int) -> int:
    fb = b & 0x80
    lb = b & 0x01
    res = b - fb - lb
    res |= (lb << 7)
    res |= (fb >> 7)
    res ^= 0x88
    res += 1
    if res > 0xFF:
        res -= 0x100
    return res


def ruida_scramble_bytes(data: bytes) -> bytes:
    return bytes(ruida_scramble_byte(b) for b in data)


def ruida_checksum(scrambled_payload: bytes) -> bytes:
    s = sum(scrambled_payload) & 0xFFFF
    return bytes([(s >> 8) & 0xFF, s & 0xFF])


def ruida_encode_number_mm(value_mm: float, length: int = 5, scale: int = 1000) -> bytes:
    """Encode a Ruida 5-byte base-128 number."""
    n = int(round(value_mm * scale))
    out = []
    while n > 0:
        out.append(n & 0x7F)
        n >>= 7
    while len(out) < length:
        out.append(0)
    out.reverse()
    return bytes(out)


def ruida_build_udp_packet(payload_unscrambled: bytes) -> bytes:
    scrambled = ruida_scramble_bytes(payload_unscrambled)
    return ruida_checksum(scrambled) + scrambled


def ruida_send_raw(sock: socket.socket, payload_unscrambled: bytes) -> bytes:
    """Send one Ruida UDP packet and return the first reply."""
    pkt = ruida_build_udp_packet(payload_unscrambled)
    sock.sendto(pkt, (RUIDA_IP, RUIDA_PORT))
    reply, _ = sock.recvfrom(4096)
    return reply


def ruida_send_scrambled_payload(sock: socket.socket, scrambled_payload: bytes) -> bytes:
    """Send a payload that is already Ruida-scrambled."""
    pkt = ruida_checksum(scrambled_payload) + scrambled_payload
    sock.sendto(pkt, (RUIDA_IP, RUIDA_PORT))
    reply, _ = sock.recvfrom(4096)
    return reply


def set_rotary_diameter(sock: socket.socket, diameter_mm: float) -> dict:
    """
    Replay the LightBurn-style rotary write burst with a new diameter.
    Companion packets remain fixed to the known-good capture.
    """
    if diameter_mm <= 0:
        return {"ok": False, "error": "invalid_diameter", "diameter_mm": diameter_mm}

    pkt_af = bytes.fromhex("d4098baf89898989898989898989")
    pkt_steps_360 = bytes.fromhex("d4098b1789891df5c989891df5c9")
    pkt_0f = bytes.fromhex("d4098b0f89898989898989898989")
    pkt_03 = bytes.fromhex("d4098b0389898989898989898989")

    diam_5 = ruida_encode_number_mm(diameter_mm, length=5, scale=1000)
    diam_unscrambled = bytes.fromhex("DA010221") + diam_5 + diam_5
    pkt_diam = ruida_scramble_bytes(diam_unscrambled)

    replies = []

    for payload in (pkt_af, pkt_steps_360, pkt_diam, pkt_0f, pkt_03):
        reply = ruida_send_scrambled_payload(sock, payload)
        replies.append(reply.hex())
        if reply != b"\xC6":
            return {
                "ok": False,
                "error": "unexpected_reply",
                "diameter_mm": diameter_mm,
                "reply_hex": reply.hex(),
                "all_replies": replies,
            }

    return {
        "ok": True,
        "diameter_mm": round(diameter_mm, 3),
        "steps_per_rev": 360,
        "replies": replies,
    }


def set_rotary_enabled(sock: socket.socket, enabled: bool) -> dict:
    """
    Replay the LightBurn-style rotary write burst with only the rotary enable flag changed.
    The enable flag is machine setting 0x0226.
    """
    pkt_rotary_enable = bytes.fromhex("d4098baf89898989098989898909")
    pkt_rotary_disable = bytes.fromhex("d4098baf89898989898989898989")
    pkt_steps_360 = bytes.fromhex("d4098b1789891df5c989891df5c9")
    pkt_0f = bytes.fromhex("d4098b0f89898989898989898989")
    pkt_03 = bytes.fromhex("d4098b0389898989898989898989")

    # Preserve current rotary diameter instead of overwriting it.
    diameter_reply = query_setting(sock, 0x0221)
    diameter_raw = tail_u32(diameter_reply)
    diameter_mm = diameter_raw / 1000.0

    diam_5 = ruida_encode_number_mm(diameter_mm, length=5, scale=1000)
    diam_unscrambled = bytes.fromhex("DA010221") + diam_5 + diam_5
    pkt_diam = ruida_scramble_bytes(diam_unscrambled)

    flag_packet = pkt_rotary_enable if enabled else pkt_rotary_disable
    replies = []

    for payload in (flag_packet, pkt_steps_360, pkt_diam, pkt_0f, pkt_03):
        reply = ruida_send_scrambled_payload(sock, payload)
        replies.append(reply.hex())
        if reply != b"\xC6":
            return {
                "ok": False,
                "error": "unexpected_reply",
                "enabled": enabled,
                "diameter_mm": round(diameter_mm, 3),
                "reply_hex": reply.hex(),
                "all_replies": replies,
            }

    return {
        "ok": True,
        "enabled": enabled,
        "state": "ON" if enabled else "OFF",
        "diameter_mm": round(diameter_mm, 3),
        "steps_per_rev": 360,
        "replies": replies,
    }


def decode_ruida_s14(b1: int, b2: int) -> int:
    """Decode a signed 14-bit Ruida relative coordinate."""
    value = ((b1 & 0x7F) << 7) | (b2 & 0x7F)
    if value & 0x2000:
        value -= 0x4000
    return value


def flatten_preview_paths(paths: list[list[tuple[float, float]]]) -> list[tuple[float, float]]:
    return [point for path in paths for point in path]


def extract_preview_paths(raw: bytes) -> list[list[tuple[float, float]]]:
    """
    RD preview extraction for common Ruida motion/cut records.

    Supported records:
        0x88 + abs X + abs Y       = move absolute
        0x89 + rel X + rel Y       = move relative
        0x8A + rel X               = move horizontal
        0x8B + rel Y               = move vertical
        0xA8 + abs X + abs Y       = cut absolute
        0xA9 + rel X + rel Y       = cut relative
        0xAA + rel X               = cut horizontal
        0xAB + rel Y               = cut vertical

    This parser walks the RD byte stream command-by-command instead of scanning
    every byte for 0x88/0xA8. That prevents parameter bytes inside dense fill or
    scanline data from being misread as new absolute vector commands.
    """
    paths: list[list[tuple[float, float]]] = []
    current_path: list[tuple[float, float]] = []
    current_x: float | None = None
    current_y: float | None = None

    def valid_xy(x_mm: float, y_mm: float) -> bool:
        return 0 <= x_mm <= 10000 and 0 <= y_mm <= 10000

    def finish_path() -> None:
        nonlocal current_path
        if current_path:
            paths.append(current_path)
            current_path = []

    def point(x_mm: float, y_mm: float) -> tuple[float, float]:
        return (round(x_mm, 3), round(y_mm, 3))

    def start_path(x_mm: float, y_mm: float) -> None:
        nonlocal current_path
        finish_path()
        current_path = [point(x_mm, y_mm)]

    def append_cut(x_mm: float, y_mm: float) -> None:
        nonlocal current_path
        p = point(x_mm, y_mm)
        if not current_path:
            current_path = [p]
        elif current_path[-1] != p:
            current_path.append(p)

    i = 0
    while i < len(raw):
        command = raw[i]

        try:
            if command == 0x88 and i <= len(raw) - 11:
                x_mm = decode_ruida_u35(raw[i + 1:i + 6]) / 1000.0
                y_mm = decode_ruida_u35(raw[i + 6:i + 11]) / 1000.0
                if valid_xy(x_mm, y_mm):
                    current_x = x_mm
                    current_y = y_mm
                    start_path(current_x, current_y)
                i += 11
                continue

            if command == 0x89 and i <= len(raw) - 5:
                if current_x is not None and current_y is not None:
                    next_x = current_x + (decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0)
                    next_y = current_y + (decode_ruida_s14(raw[i + 3], raw[i + 4]) / 1000.0)
                    if valid_xy(next_x, next_y):
                        current_x = next_x
                        current_y = next_y
                        start_path(current_x, current_y)
                i += 5
                continue

            if command == 0x8A and i <= len(raw) - 3:
                if current_x is not None and current_y is not None:
                    next_x = current_x + (decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0)
                    if valid_xy(next_x, current_y):
                        current_x = next_x
                        start_path(current_x, current_y)
                i += 3
                continue

            if command == 0x8B and i <= len(raw) - 3:
                if current_x is not None and current_y is not None:
                    next_y = current_y + (decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0)
                    if valid_xy(current_x, next_y):
                        current_y = next_y
                        start_path(current_x, current_y)
                i += 3
                continue

            if command == 0xA8 and i <= len(raw) - 11:
                x_mm = decode_ruida_u35(raw[i + 1:i + 6]) / 1000.0
                y_mm = decode_ruida_u35(raw[i + 6:i + 11]) / 1000.0
                if valid_xy(x_mm, y_mm):
                    current_x = x_mm
                    current_y = y_mm
                    append_cut(current_x, current_y)
                i += 11
                continue

            if command == 0xA9 and i <= len(raw) - 5:
                if current_x is not None and current_y is not None:
                    next_x = current_x + (decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0)
                    next_y = current_y + (decode_ruida_s14(raw[i + 3], raw[i + 4]) / 1000.0)
                    if valid_xy(next_x, next_y):
                        current_x = next_x
                        current_y = next_y
                        append_cut(current_x, current_y)
                i += 5
                continue

            if command == 0xAA and i <= len(raw) - 3:
                if current_x is not None and current_y is not None:
                    next_x = current_x + (decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0)
                    if valid_xy(next_x, current_y):
                        current_x = next_x
                        append_cut(current_x, current_y)
                i += 3
                continue

            if command == 0xAB and i <= len(raw) - 3:
                if current_x is not None and current_y is not None:
                    next_y = current_y + (decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0)
                    if valid_xy(current_x, next_y):
                        current_y = next_y
                        append_cut(current_x, current_y)
                i += 3
                continue

        except Exception:
            i += 1
            continue

        i += 1

    finish_path()
    return paths


def extract_preview_points(raw: bytes) -> list[tuple[float, float]]:
    """Compatibility wrapper returning a flattened point list."""
    return flatten_preview_paths(extract_preview_paths(raw))

def get_file_list(sock: socket.socket) -> list[dict]:
    """Read saved jobs from the controller using the existing bound UDP socket."""
    jobs: list[dict] = []

    count_reply = query(sock, bytes.fromhex("DA000405"))
    if len(count_reply) < 5:
        raise ValueError(f"Unexpected saved-job-count reply: {count_reply.hex()}")

    job_count = count_reply[-1] & 0x7F

    for slot in range(1, job_count + 1):
        name_reply = query(sock, bytes([0xE8, 0x01, 0x00, slot]))
        if len(name_reply) < 5:
            raise ValueError(f"Unexpected filename reply for slot {slot}: {name_reply.hex()}")

        name_bytes = name_reply[4:]
        zero_pos = name_bytes.find(b"\x00")
        if zero_pos != -1:
            name_bytes = name_bytes[:zero_pos]
        name = name_bytes.decode("ascii", errors="replace")

        info_reply = query(sock, bytes([0xDA, 0x00, 0x07, 0x10 + slot]))
        if len(info_reply) < 9:
            raise ValueError(f"Unexpected info reply for slot {slot}: {info_reply.hex()}")

        runtime_ms = decode_ruida_u35(info_reply[-5:])

        jobs.append(
            {
                "slot": slot,
                "name": name,
                "runtime_ms": runtime_ms,
                "runtime_text": format_runtime_ms(runtime_ms),
            }
        )

    return jobs




def safe_controller_filename(name: str, fallback: str = "download") -> str:
    """Return a filesystem-safe RD filename while preserving controller names."""
    cleaned = "".join(ch for ch in str(name or "").strip() if ch.isalnum() or ch in ("-", "_", "."))
    if not cleaned:
        cleaned = fallback
    if not cleaned.lower().endswith(".rd"):
        cleaned = f"{cleaned}.rd"
    return cleaned


def trim_controller_download_body(raw_body: bytes) -> bytes:
    """
    Controller download blocks are unswizzled RD bytes.

    Observed padding cases:
    - long 0x76 runs
    - long raw 0x00 tail padding, which becomes 0x89 after swizzling
    - occasional RD end marker 0xD7

    Keep actual RD bytes and remove transfer padding only.
    """
    padding_start = raw_body.find(b"\x76" * 32)
    if padding_start != -1:
        return raw_body[:padding_start]

    # Controller download tail padding may be raw NUL bytes. Only strip it when
    # it is a long padding run, not a few legitimate zero bytes.
    zero_run = b"\x00" * 32
    zero_padding_start = raw_body.find(zero_run)
    if zero_padding_start != -1:
        return raw_body[:zero_padding_start]

    end_marker = raw_body.rfind(b"\xD7")
    if end_marker != -1:
        return raw_body[:end_marker + 1]

    return raw_body


def receive_download_block(sock: socket.socket, slot: int, block_num: int) -> tuple[bytes, int, dict]:
    """
    Request one controller file block and return the unswizzled block payload.

    Wire format observed from RDWorks:
      E5 01 <slot> 00 00 00 00 <block_num>

    Some controller files finish a block with a short UDP fragment. Others appear
    to stop after one or more full-size fragments and rely on silence/timeout.
    If at least one data packet was received, a socket timeout is treated as the
    end of that block instead of a hard failure.
    """
    command = bytes([0xE5, 0x01, slot & 0xFF]) + encode_ruida_u35_block_number(block_num)
    sock.sendto(build_udp_packet(command), (RUIDA_IP, RUIDA_PORT))

    ack, _ = sock.recvfrom(4096)
    ack_unswizzled = unswizzle(ack) if ack != b"\xC6" else b"\xC6"
    if ack_unswizzled != b"\xC6":
        raise ValueError(f"unexpected download ACK for slot {slot}, block {block_num}: {ack.hex()}")

    parts: list[bytes] = []
    packet_lengths: list[int] = []
    ended_by = "unknown"

    while True:
        try:
            packet, _ = sock.recvfrom(4096)
        except socket.timeout:
            if parts:
                ended_by = "timeout_after_data"
                break
            return b"", 0, {
                "block": block_num,
                "packet_count": 0,
                "packet_lengths": [],
                "ended_by": "timeout_no_data",
            }

        if packet == b"\xC6":
            continue

        packet_lengths.append(len(packet))
        decoded = unswizzle(packet)
        parts.append(decoded)

        # RDWorks often sends 1472-byte full fragments followed by a shorter
        # final fragment. This remains the cleanest end condition when present.
        if len(packet) < 1472:
            ended_by = "short_fragment"
            break

    block = b"".join(parts)
    expected_header = command
    if block.startswith(expected_header):
        block_payload = block[len(expected_header):]
    else:
        block_payload = block

    # The controller appends a 2-byte transfer trailer to each download block.
    # It is not RD file data. Preserve the pre-strip wire payload length so the
    # caller does not mistake a full block for a short final block.
    wire_payload_len = len(block_payload)
    stripped_block_trailer_hex = None
    if len(block_payload) >= 2:
        stripped_block_trailer_hex = block_payload[-2:].hex()
        block_payload = block_payload[:-2]

    return block_payload, len(block_payload), {
        "block": block_num,
        "packet_count": len(packet_lengths),
        "packet_lengths": packet_lengths,
        "wire_payload_len": wire_payload_len,
        "payload_len": len(block_payload),
        "stripped_block_trailer_hex": stripped_block_trailer_hex,
        "ended_by": ended_by,
    }


def encode_ruida_u35_block_number(block_num: int) -> bytes:
    """Encode a block number as the same 5-byte 7-bit Ruida-style value used elsewhere."""
    if block_num < 0:
        raise ValueError("block number must be >= 0")

    return bytes([
        (block_num >> 28) & 0x7F,
        (block_num >> 21) & 0x7F,
        (block_num >> 14) & 0x7F,
        (block_num >> 7) & 0x7F,
        block_num & 0x7F,
    ])



def download_controller_file(sock: socket.socket, slot: int, name: str | None = None) -> dict:
    """Download one saved controller file by slot and save it as a swizzled .rd file."""
    if slot < 1 or slot > 255:
        raise ValueError(f"slot must be 1-255, got {slot}")

    metadata_reply = query(sock, bytes([0xE5, 0x00, slot & 0xFF]))
    if not metadata_reply.startswith(bytes([0xE5, 0x00, slot & 0xFF])):
        raise ValueError(f"unexpected download metadata reply for slot {slot}: {metadata_reply.hex()}")

    raw_body = bytearray()
    controller_name = name or f"slot_{slot:03d}"
    max_payload_per_block = 2114
    max_blocks = 1024
    block_debug: list[dict] = []

    for block_num in range(max_blocks):
        block_payload, block_payload_len, block_info = receive_download_block(sock, slot, block_num)
        block_debug.append(block_info)

        # If the controller ACKs a block request but sends no block data, treat it
        # as end-of-file after prior data. If it happens on block 0, it is still a
        # real failure.
        if block_payload_len == 0:
            if raw_body:
                break
            raise TimeoutError(f"no file data received for slot {slot}, block {block_num}")

        wire_payload_len = int(block_info.get("wire_payload_len", block_payload_len))

        if block_num == 0 and block_payload.startswith(b"\xE7\x01"):
            name_end = block_payload.find(b"\x00", 2)
            if name_end != -1:
                decoded_name = block_payload[2:name_end].decode("ascii", errors="replace").strip()
                if decoded_name:
                    controller_name = decoded_name
                block_payload = block_payload[name_end + 1:]
                block_payload_len = len(block_payload)
                block_info["wire_payload_len"] = wire_payload_len
                block_info["file_payload_len"] = block_payload_len
                block_info["stripped_name_header"] = True

        raw_body.extend(block_payload)

        if b"\x76" * 32 in raw_body:
            break

        # Stop only on a truly short wire payload. Block 0 usually has an
        # E7 filename header that we strip before appending, so its file payload
        # can be shorter than max_payload_per_block even when another block is
        # still available.
        if block_info.get("ended_by") == "short_fragment" and wire_payload_len < max_payload_per_block:
            break
    else:
        raise TimeoutError(f"download did not finish within {max_blocks} blocks for slot {slot}")

    raw_download = trim_controller_download_body(bytes(raw_body))
    if not raw_download:
        raise ValueError(f"downloaded file body is empty for slot {slot}")

    file_name = safe_controller_filename(controller_name, fallback=f"slot_{slot:03d}")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOWNLOAD_DIR / file_name

    # Controller sends the RD body unswizzled. Save normal .rd files in the
    # same swizzled format that LightBurn/RDWorks write to disk.
    out_path.write_bytes(swizzle(raw_download))

    raw_debug_path = None
    if DOWNLOAD_RAW_DEBUG:
        raw_debug_path = DOWNLOAD_DIR / f"{out_path.stem}.raw_unswizzled"
        raw_debug_path.write_bytes(raw_download)

    return {
        "ok": True,
        "cmd": "download_file",
        "slot": slot,
        "file_name": file_name,
        "controller_name": controller_name,
        "path": str(out_path),
        "bytes": len(raw_download),
        "raw_untrimmed_bytes": len(raw_body),
        "metadata_reply_hex": metadata_reply.hex(),
        "blocks": block_debug,
        "raw_debug_path": str(raw_debug_path) if raw_debug_path else None,
    }


def download_missing_controller_files(sock: socket.socket, jobs: list[dict]) -> list[dict]:
    """Download controller files that are listed but not already present locally."""
    downloaded: list[dict] = []
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    for job in jobs:
        slot = int(job.get("slot", 0))
        name = str(job.get("name") or f"slot_{slot:03d}")
        target = DOWNLOAD_DIR / safe_controller_filename(name, fallback=f"slot_{slot:03d}")

        if target.exists():
            continue

        try:
            downloaded.append(download_controller_file(sock, slot=slot, name=name))
        except Exception as exc:
            traceback.print_exc()
            downloaded.append({
                "ok": False,
                "cmd": "download_file",
                "slot": slot,
                "file_name": target.name,
                "error": str(exc),
            })

    return downloaded


def list_local_download_files() -> list[dict]:
    """Return local RD/LightBurn files stored in the downloads folder."""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    allowed_suffixes = {".rd", ".lbrn", ".lbrn2"}
    files: list[dict] = []

    for path in sorted(DOWNLOAD_DIR.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in allowed_suffixes:
            continue

        stat = path.stat()
        files.append({
            "slot": None,
            "name": path.name,
            "runtime_ms": None,
            "runtime_text": "local",
            "source": "local",
            "path": str(path),
            "size_bytes": stat.st_size,
            "modified": int(stat.st_mtime),
        })

    return files


def merge_controller_and_local_files(controller_jobs: list[dict]) -> list[dict]:
    """Merge controller jobs with local-only files in the downloads folder."""
    merged: list[dict] = []
    controller_names: set[str] = set()

    for job in controller_jobs:
        item = dict(job)
        item["source"] = "controller"
        safe_name = safe_controller_filename(
            str(item.get("name") or ""),
            fallback=f"slot_{int(item.get('slot', 0)):03d}",
        )
        item["local_file"] = str(DOWNLOAD_DIR / safe_name)
        item["local_exists"] = (DOWNLOAD_DIR / safe_name).exists()
        controller_names.add(safe_name.lower())
        controller_names.add(str(item.get("name") or "").lower())
        merged.append(item)

    for local_file in list_local_download_files():
        local_name = str(local_file.get("name") or "")
        if local_name.lower() in controller_names:
            continue
        merged.append(local_file)

    return merged



def preview_path_length(path: list[tuple[float, float]]) -> float:
    total = 0.0
    for idx in range(1, len(path)):
        x1, y1 = path[idx - 1]
        x2, y2 = path[idx]
        total += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    return total


def filter_isolated_preview_clusters(paths: list[list[tuple[float, float]]]) -> list[list[tuple[float, float]]]:
    """
    Remove small preview clusters that are far away from the main parsed artwork.

    This targets parser/download-preview artifacts such as a single isolated scan
    dash hundreds of mm away from the real design, while preserving separate real
    artwork clusters such as letters, islands, dots, or disconnected shapes.
    """
    if len(paths) < 3:
        return paths

    items = []
    for item in paths:
        if len(item) < 2:
            continue

        xs = [pt[0] for pt in item]
        ys = [pt[1] for pt in item]

        items.append({
            "path": item,
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys),
            "length": preview_path_length(item),
        })

    if len(items) < 3:
        return paths

    gap_mm = 3.0
    clusters = []

    for item in sorted(items, key=lambda row: (row["min_y"], row["min_x"])):
        placed = False

        for cluster in clusters:
            close_x = item["min_x"] <= cluster["max_x"] + gap_mm and item["max_x"] >= cluster["min_x"] - gap_mm
            close_y = item["min_y"] <= cluster["max_y"] + gap_mm and item["max_y"] >= cluster["min_y"] - gap_mm

            if close_x and close_y:
                cluster["items"].append(item)
                cluster["min_x"] = min(cluster["min_x"], item["min_x"])
                cluster["max_x"] = max(cluster["max_x"], item["max_x"])
                cluster["min_y"] = min(cluster["min_y"], item["min_y"])
                cluster["max_y"] = max(cluster["max_y"], item["max_y"])
                cluster["length"] += item["length"]
                placed = True
                break

        if not placed:
            clusters.append({
                "items": [item],
                "min_x": item["min_x"],
                "max_x": item["max_x"],
                "min_y": item["min_y"],
                "max_y": item["max_y"],
                "length": item["length"],
            })

    changed = True
    while changed:
        changed = False
        merged = []

        while clusters:
            base = clusters.pop(0)
            idx = 0

            while idx < len(clusters):
                other = clusters[idx]
                close_x = other["min_x"] <= base["max_x"] + gap_mm and other["max_x"] >= base["min_x"] - gap_mm
                close_y = other["min_y"] <= base["max_y"] + gap_mm and other["max_y"] >= base["min_y"] - gap_mm

                if close_x and close_y:
                    base["items"].extend(other["items"])
                    base["min_x"] = min(base["min_x"], other["min_x"])
                    base["max_x"] = max(base["max_x"], other["max_x"])
                    base["min_y"] = min(base["min_y"], other["min_y"])
                    base["max_y"] = max(base["max_y"], other["max_y"])
                    base["length"] += other["length"]
                    clusters.pop(idx)
                    changed = True
                else:
                    idx += 1

            merged.append(base)

        clusters = merged

    if len(clusters) <= 1:
        return paths

    largest_path_count = max(len(cluster["items"]) for cluster in clusters)
    largest_length = max(cluster["length"] for cluster in clusters)

    kept = []
    for cluster in clusters:
        path_count = len(cluster["items"])
        width = cluster["max_x"] - cluster["min_x"]
        height = cluster["max_y"] - cluster["min_y"]

        isolated_junk = (
            path_count <= 2
            and cluster["length"] <= 15.0
            and width <= 25.0
            and height <= 5.0
            and largest_path_count >= 100
            and largest_length >= 100.0
        )

        if isolated_junk:
            continue

        kept.extend(item["path"] for item in cluster["items"])

    return kept or paths


def split_preview_paths_on_large_jumps(paths: list[list[tuple[float, float]]]) -> list[list[tuple[float, float]]]:
    """
    Split parsed preview paths when one segment makes an impossible jump.

    This preserves the valid geometry after the bad jump instead of deleting the
    entire path. It targets parser artifacts like a single bogus start point at
    y=2072 followed by otherwise valid artwork near y=400.
    """
    max_segment_mm = 500.0
    cleaned: list[list[tuple[float, float]]] = []

    for path in paths:
        if len(path) < 2:
            continue

        current: list[tuple[float, float]] = [path[0]]

        for point in path[1:]:
            previous = current[-1]
            segment_length = ((point[0] - previous[0]) ** 2 + (point[1] - previous[1]) ** 2) ** 0.5

            if segment_length > max_segment_mm:
                if len(current) >= 2:
                    cleaned.append(current)
                current = [point]
            else:
                current.append(point)

        if len(current) >= 2:
            cleaned.append(current)

    return cleaned or paths


def preview_command_counts(raw: bytes) -> dict:
    return {
        "c88": raw.count(0x88),
        "c89": raw.count(0x89),
        "c8a": raw.count(0x8A),
        "c8b": raw.count(0x8B),
        "ca8": raw.count(0xA8),
        "ca9": raw.count(0xA9),
        "caa": raw.count(0xAA),
        "cab": raw.count(0xAB),
    }


def is_reasonable_preview_point(x: float, y: float) -> bool:
    import math
    return math.isfinite(x) and math.isfinite(y) and abs(x) <= 10000.0 and abs(y) <= 10000.0


def is_reasonable_preview_delta(value: float) -> bool:
    import math
    return math.isfinite(value) and abs(value) <= 100.0


def classify_preview_mode(raw: bytes) -> str:
    counts = preview_command_counts(raw)

    scan_heavy = (
        counts["caa"] >= 300
        and counts["caa"] > max(100, counts["ca9"] * 4)
        and (
            counts["c8a"] > 0
            or counts["c88"] > 300
            or counts["c89"] > 75
            or counts["ca8"] > 10
        )
    )

    if scan_heavy:
        return "mixed_scan" if counts["ca8"] > 0 or counts["ca9"] > 0 else "scan"

    return "vector"


def extract_scan_preview_paths(raw: bytes) -> list[list[tuple[float, float]]]:
    """
    Scan-heavy RD preview extraction.

    For scan-heavy files:
    - move records update current position only
    - cut records create individual visible segments
    - 0xAA is treated as horizontal scan coverage, not a long vector path
    """
    paths: list[list[tuple[float, float]]] = []
    x: float | None = None
    y: float | None = None

    def add_segment(x1: float, y1: float, x2: float, y2: float) -> None:
        if not is_reasonable_preview_point(x1, y1):
            return
        if not is_reasonable_preview_point(x2, y2):
            return
        if abs(x2 - x1) < 0.001 and abs(y2 - y1) < 0.001:
            return
        if abs(x2 - x1) > 500.0 or abs(y2 - y1) > 500.0:
            return

        paths.append([
            (round(x1, 3), round(y1, 3)),
            (round(x2, 3), round(y2, 3)),
        ])

    i = 0
    while i < len(raw):
        command = raw[i]

        try:
            if command == 0x88 and i <= len(raw) - 11:
                nx = decode_ruida_u35(raw[i + 1:i + 6]) / 1000.0
                ny = decode_ruida_u35(raw[i + 6:i + 11]) / 1000.0
                if is_reasonable_preview_point(nx, ny):
                    x = nx
                    y = ny
                i += 11
                continue

            if command == 0x89 and i <= len(raw) - 5:
                if x is not None and y is not None:
                    dx = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0
                    dy = decode_ruida_s14(raw[i + 3], raw[i + 4]) / 1000.0
                    if is_reasonable_preview_delta(dx) and is_reasonable_preview_delta(dy):
                        nx = x + dx
                        ny = y + dy
                        if is_reasonable_preview_point(nx, ny):
                            x = nx
                            y = ny
                i += 5
                continue

            if command == 0x8A and i <= len(raw) - 3:
                if x is not None and y is not None:
                    dx = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0
                    if is_reasonable_preview_delta(dx):
                        nx = x + dx
                        if is_reasonable_preview_point(nx, y):
                            x = nx
                i += 3
                continue

            if command == 0x8B and i <= len(raw) - 3:
                if x is not None and y is not None:
                    dy = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0
                    if is_reasonable_preview_delta(dy):
                        ny = y + dy
                        if is_reasonable_preview_point(x, ny):
                            y = ny
                i += 3
                continue

            if command == 0xA8 and i <= len(raw) - 11:
                nx = decode_ruida_u35(raw[i + 1:i + 6]) / 1000.0
                ny = decode_ruida_u35(raw[i + 6:i + 11]) / 1000.0
                if x is not None and y is not None:
                    add_segment(x, y, nx, ny)
                if is_reasonable_preview_point(nx, ny):
                    x = nx
                    y = ny
                i += 11
                continue

            if command == 0xA9 and i <= len(raw) - 5:
                if x is not None and y is not None:
                    dx = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0
                    dy = decode_ruida_s14(raw[i + 3], raw[i + 4]) / 1000.0
                    if is_reasonable_preview_delta(dx) and is_reasonable_preview_delta(dy):
                        nx = x + dx
                        ny = y + dy
                        add_segment(x, y, nx, ny)
                        if is_reasonable_preview_point(nx, ny):
                            x = nx
                            y = ny
                i += 5
                continue

            if command == 0xAA and i <= len(raw) - 3:
                if x is not None and y is not None:
                    dx = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0
                    if is_reasonable_preview_delta(dx):
                        nx = x + dx
                        add_segment(x, y, nx, y)
                        if is_reasonable_preview_point(nx, y):
                            x = nx
                i += 3
                continue

            if command == 0xAB and i <= len(raw) - 3:
                if x is not None and y is not None:
                    dy = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0
                    if is_reasonable_preview_delta(dy):
                        ny = y + dy
                        add_segment(x, y, x, ny)
                        if is_reasonable_preview_point(x, ny):
                            y = ny
                i += 3
                continue

        except Exception:
            i += 1
            continue

        i += 1

    return paths



def detect_scan_y_interval(raw: bytes) -> float | None:
    """
    Detect scan row interval from repeated Y movement in the RD command stream.

    This is used only for scan/fill preview cleanup. It looks for small repeated
    Y moves around horizontal scan activity instead of assuming a fixed row pitch.
    """
    from collections import Counter

    x: float | None = None
    y: float | None = None
    saw_horizontal_scan = False
    y_steps: list[float] = []

    def remember_step(delta_y: float) -> None:
        step = abs(delta_y)
        if 0.005 <= step <= 2.0:
            # Round to 0.001 mm to avoid tiny floating-point/encoding noise.
            y_steps.append(round(step, 3))

    i = 0
    while i < len(raw):
        command = raw[i]

        try:
            if command == 0x88 and i <= len(raw) - 11:
                nx = decode_ruida_u35(raw[i + 1:i + 6]) / 1000.0
                ny = decode_ruida_u35(raw[i + 6:i + 11]) / 1000.0
                if is_reasonable_preview_point(nx, ny):
                    x = nx
                    y = ny
                i += 11
                continue

            if command == 0x89 and i <= len(raw) - 5:
                if x is not None and y is not None:
                    dx = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0
                    dy = decode_ruida_s14(raw[i + 3], raw[i + 4]) / 1000.0

                    if is_reasonable_preview_delta(dx) and is_reasonable_preview_delta(dy):
                        if saw_horizontal_scan:
                            remember_step(dy)

                        nx = x + dx
                        ny = y + dy
                        if is_reasonable_preview_point(nx, ny):
                            x = nx
                            y = ny

                i += 5
                continue

            if command == 0x8A and i <= len(raw) - 3:
                if x is not None and y is not None:
                    dx = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0
                    if is_reasonable_preview_delta(dx):
                        nx = x + dx
                        if is_reasonable_preview_point(nx, y):
                            x = nx
                            saw_horizontal_scan = True
                i += 3
                continue

            if command == 0x8B and i <= len(raw) - 3:
                if x is not None and y is not None:
                    dy = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0

                    if is_reasonable_preview_delta(dy):
                        if saw_horizontal_scan:
                            remember_step(dy)

                        ny = y + dy
                        if is_reasonable_preview_point(x, ny):
                            y = ny

                i += 3
                continue

            if command == 0xA8 and i <= len(raw) - 11:
                nx = decode_ruida_u35(raw[i + 1:i + 6]) / 1000.0
                ny = decode_ruida_u35(raw[i + 6:i + 11]) / 1000.0
                if is_reasonable_preview_point(nx, ny):
                    if x is not None and y is not None and saw_horizontal_scan:
                        remember_step(ny - y)
                    x = nx
                    y = ny
                    saw_horizontal_scan = True
                i += 11
                continue

            if command == 0xA9 and i <= len(raw) - 5:
                if x is not None and y is not None:
                    dx = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0
                    dy = decode_ruida_s14(raw[i + 3], raw[i + 4]) / 1000.0

                    if is_reasonable_preview_delta(dx) and is_reasonable_preview_delta(dy):
                        if saw_horizontal_scan:
                            remember_step(dy)

                        nx = x + dx
                        ny = y + dy
                        if is_reasonable_preview_point(nx, ny):
                            x = nx
                            y = ny
                            saw_horizontal_scan = True

                i += 5
                continue

            if command == 0xAA and i <= len(raw) - 3:
                if x is not None and y is not None:
                    dx = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0
                    if is_reasonable_preview_delta(dx):
                        nx = x + dx
                        if is_reasonable_preview_point(nx, y):
                            x = nx
                            saw_horizontal_scan = True
                i += 3
                continue

            if command == 0xAB and i <= len(raw) - 3:
                if x is not None and y is not None:
                    dy = decode_ruida_s14(raw[i + 1], raw[i + 2]) / 1000.0

                    if is_reasonable_preview_delta(dy):
                        if saw_horizontal_scan:
                            remember_step(dy)

                        ny = y + dy
                        if is_reasonable_preview_point(x, ny):
                            y = ny

                i += 3
                continue

        except Exception:
            i += 1
            continue

        i += 1

    if not y_steps:
        return None

    counts = Counter(y_steps)
    best_step, best_count = counts.most_common(1)[0]

    # Avoid trusting one-off movement/setup deltas.
    if best_count < 5:
        return None

    return float(best_step)

def cleanup_scan_preview_paths(
    paths: list[list[tuple[float, float]]],
    scan_interval_mm: float | None = None,
) -> list[list[tuple[float, float]]]:
    if not paths:
        return paths

    from collections import defaultdict

    if scan_interval_mm is None or scan_interval_mm <= 0:
        scan_interval_mm = estimate_scan_row_pitch(paths)

    if scan_interval_mm <= 0:
        scan_interval_mm = 0.05

    rows: dict[int, list[tuple[float, float]]] = defaultdict(list)
    row_y_values: dict[int, list[float]] = defaultdict(list)
    vectors: list[list[tuple[float, float]]] = []

    for seg in paths:
        if len(seg) != 2:
            continue

        (x1, y1), (x2, y2) = seg

        if not is_reasonable_preview_point(x1, y1) or not is_reasonable_preview_point(x2, y2):
            continue

        if abs(y2 - y1) > max(0.05, scan_interval_mm * 0.50):
            # In scan/fill mode, non-horizontal cut vectors are usually travel or
            # row-transition artifacts. Preserve only near-vertical helpers and
            # reject diagonal bridges that create visible slivers in filled text.
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)

            if dx <= 0.10 and dy <= 500.0:
                vectors.append([
                    (round(x1, 3), round(y1, 3)),
                    (round(x2, 3), round(y2, 3)),
                ])

            continue

        if x2 < x1:
            x1, x2 = x2, x1

        if (x2 - x1) < max(0.03, scan_interval_mm * 0.50):
            continue

        y_mid = (y1 + y2) / 2.0
        row_index = int(round(y_mid / scan_interval_mm))
        rows[row_index].append((x1, x2))
        row_y_values[row_index].append(y_mid)

    cleaned: list[list[tuple[float, float]]] = []

    merge_gap_mm = max(0.03, scan_interval_mm * 1.20)
    min_span_mm = max(0.04, scan_interval_mm * 0.80)

    for row_index, spans in sorted(rows.items()):
        spans.sort(key=lambda item: item[0])
        merged: list[list[float]] = []

        for x1, x2 in spans:
            if not merged:
                merged.append([x1, x2])
                continue

            previous = merged[-1]
            if x1 - previous[1] <= merge_gap_mm:
                previous[1] = max(previous[1], x2)
            else:
                merged.append([x1, x2])

        y_values = row_y_values.get(row_index) or [row_index * scan_interval_mm]
        y_row = sum(y_values) / len(y_values)

        for x1, x2 in merged:
            if x2 - x1 >= min_span_mm:
                cleaned.append([
                    (round(x1, 3), round(y_row, 3)),
                    (round(x2, 3), round(y_row, 3)),
                ])

    return cleaned + vectors


def extract_preview_geometry(raw: bytes) -> tuple[str, list[list[tuple[float, float]]]]:
    preview_mode = classify_preview_mode(raw)

    if preview_mode in ("scan", "mixed_scan"):
        scan_paths = cleanup_scan_preview_paths(extract_scan_preview_paths(raw), detect_scan_y_interval(raw))
        if scan_paths:
            return preview_mode, scan_paths

    return "vector", extract_preview_paths(raw)

def compute_bounds(paths: list[list[tuple[float, float]]] | list[tuple[float, float]]) -> dict:
    if not paths:
        raise ValueError("no preview points found")

    if isinstance(paths[0], tuple):
        points = paths  # type: ignore[assignment]
    else:
        points = flatten_preview_paths(paths)  # type: ignore[arg-type]

    if not points:
        raise ValueError("no preview points found")

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    min_x = min(xs)
    min_y = min(ys)
    max_x = max(xs)
    max_y = max(ys)

    return {
        "min_x_mm": round(min_x, 3),
        "min_y_mm": round(min_y, 3),
        "max_x_mm": round(max_x, 3),
        "max_y_mm": round(max_y, 3),
        "width_mm": round(max_x - min_x, 3),
        "height_mm": round(max_y - min_y, 3),
    }



def is_scan_fill_preview(paths: list[list[tuple[float, float]]]) -> bool:
    """
    Detect dense horizontal scan/fill previews.

    These should render as filled scan coverage instead of thin individual
    vector strokes, otherwise the preview looks like gray striping.
    """
    if len(paths) < 100:
        return False

    horizontal = 0
    total = 0

    for path in paths:
        if len(path) != 2:
            continue

        (x1, y1), (x2, y2) = path
        total += 1

        if abs(y2 - y1) <= 0.05 and abs(x2 - x1) >= 0.05:
            horizontal += 1

    return total >= 100 and horizontal / max(total, 1) >= 0.90


def estimate_scan_row_pitch(paths: list[list[tuple[float, float]]]) -> float:
    ys = sorted({
        round(((path[0][1] + path[-1][1]) / 2.0), 3)
        for path in paths
        if len(path) == 2 and abs(path[0][1] - path[-1][1]) <= 0.05
    })

    gaps = [
        ys[idx] - ys[idx - 1]
        for idx in range(1, len(ys))
        if 0.001 <= ys[idx] - ys[idx - 1] <= 2.0
    ]

    if not gaps:
        return 0.10

    gaps.sort()
    return gaps[len(gaps) // 2]


def merge_scan_fill_spans(paths: list[list[tuple[float, float]]]) -> list[list[tuple[float, float]]]:
    """
    Merge scan-fill spans conservatively.

    Rules:
    - only consider nearly-horizontal 2-point paths as scan rows
    - only merge tiny gaps
    - only merge when the gap is supported by BOTH neighboring rows
    - leave non-scan/vector paths unchanged
    """
    if not paths:
        return paths

    row_pitch_mm = estimate_scan_row_pitch(paths)
    if row_pitch_mm <= 0:
        return paths

    horizontal_tol = max(0.02, row_pitch_mm * 0.35)
    merge_gap_mm = max(0.03, row_pitch_mm * 0.25)
    min_span_mm = max(0.10, row_pitch_mm * 1.50)
    support_tol_mm = max(merge_gap_mm * 1.5, row_pitch_mm * 0.50)

    scan_rows: dict[int, dict[str, object]] = {}
    passthrough: list[list[tuple[float, float]]] = []

    for path in paths:
        if len(path) != 2:
            passthrough.append(path)
            continue

        (x1, y1), (x2, y2) = path
        if abs(y2 - y1) > horizontal_tol:
            passthrough.append(path)
            continue

        y = (y1 + y2) / 2.0
        left = min(x1, x2)
        right = max(x1, x2)

        key = int(round(y / row_pitch_mm))
        if key not in scan_rows:
            scan_rows[key] = {
                "y_values": [],
                "spans": [],
            }

        scan_rows[key]["y_values"].append(y)
        scan_rows[key]["spans"].append((left, right))

    if not scan_rows:
        return paths

    row_y: dict[int, float] = {}
    row_spans: dict[int, list[tuple[float, float]]] = {}

    for key, info in scan_rows.items():
        ys = info["y_values"]
        spans = info["spans"]

        row_y[key] = sum(ys) / len(ys)
        row_spans[key] = sorted(spans, key=lambda span: (span[0], span[1]))

    def gap_supported_by_neighbors(row_key: int, gap_left: float, gap_right: float) -> bool:
        """
        Only merge if BOTH neighboring rows show fill through the same gap zone.
        This helps avoid bridging real holes in letters.
        """
        gap_mid = (gap_left + gap_right) / 2.0
        supported_rows = 0

        for neighbor_key in (row_key - 1, row_key + 1):
            spans = row_spans.get(neighbor_key, [])
            hit = False

            for left, right in spans:
                if (left - support_tol_mm) <= gap_mid <= (right + support_tol_mm):
                    hit = True
                    break

            if hit:
                supported_rows += 1

        return supported_rows >= 2

    merged_scan_paths: list[list[tuple[float, float]]] = []

    for key in sorted(row_spans.keys()):
        spans = row_spans[key]
        if not spans:
            continue

        current_left, current_right = spans[0]

        for left, right in spans[1:]:
            gap = left - current_right
            current_len = current_right - current_left
            next_len = right - left

            should_merge = (
                gap <= merge_gap_mm
                and current_len >= min_span_mm
                and next_len >= min_span_mm
                and gap_supported_by_neighbors(key, current_right, left)
            )

            if should_merge:
                current_right = max(current_right, right)
            else:
                merged_scan_paths.append([
                    (round(current_left, 3), round(row_y[key], 3)),
                    (round(current_right, 3), round(row_y[key], 3)),
                ])
                current_left, current_right = left, right

        merged_scan_paths.append([
            (round(current_left, 3), round(row_y[key], 3)),
            (round(current_right, 3), round(row_y[key], 3)),
        ])

    return passthrough + merged_scan_paths


def render_preview_png(
    paths: list[list[tuple[float, float]]] | list[tuple[float, float]],
    out_path: Path,
    title: str,
    bounds: dict,
    fit_mode: str | None = None,
) -> None:
    if not paths:
        raise ValueError("no preview points found")

    if isinstance(paths[0], tuple):
        draw_paths = [paths]  # type: ignore[list-item]
    else:
        draw_paths = paths  # type: ignore[assignment]

    fit_mode = str(fit_mode or PREVIEW_FIT_MODE).strip().lower()
    if fit_mode not in {"geometry", "bed"}:
        fit_mode = PREVIEW_FIT_MODE

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Render oversize first, then downsample for normal vector previews.
    # Dense scan/fill previews render at final size to avoid downsample banding.
    # Bed view uses the configured bed aspect ratio so the web ruler scale
    # matches the rendered bed frame.
    final_width_px = 1200
    if fit_mode == "bed" and MAX_X_MM > 0 and MAX_Y_MM > 0:
        final_height_px = max(1, int(round(final_width_px * (MAX_Y_MM / MAX_X_MM))))
    else:
        final_height_px = 900

    scan_fill_mode = is_scan_fill_preview(draw_paths)
    aa_scale = 1 if scan_fill_mode else 2
    width_px = final_width_px * aa_scale
    height_px = final_height_px * aa_scale

    # Legacy preview padding was tuned for older in-image labels.
    # Now that the web UI owns the rulers, bed view should use a much
    # tighter plotting margin so the bed scale matches the visible frame.
    if fit_mode == "bed":
        pad_x = 12 * aa_scale
        pad_y = 12 * aa_scale
    else:
        pad_x = 70 * aa_scale
        pad_y = 70 * aa_scale

    bg_color = PREVIEW_BACKGROUND_RGB
    fg_color = PREVIEW_FOREGROUND_RGB
    grid_color = PREVIEW_GRID_RGB
    line_width = PREVIEW_LINE_WIDTH * aa_scale

    image_mode = "RGBA" if len(bg_color) == 4 else "RGB"
    image = Image.new(image_mode, (width_px, height_px), bg_color)
    draw = ImageDraw.Draw(image)

    if fit_mode == "bed":
        view_min_x = 0.0
        view_min_y = 0.0
        view_max_x = max(MAX_X_MM, bounds["max_x_mm"], 1.0)
        view_max_y = max(MAX_Y_MM, bounds["max_y_mm"], 1.0)
    else:
        geom_w = max(bounds["width_mm"], 1.0)
        geom_h = max(bounds["height_mm"], 1.0)
        margin_x = max(geom_w * 0.05, 1.0)
        margin_y = max(geom_h * 0.05, 1.0)
        view_min_x = bounds["min_x_mm"] - margin_x
        view_min_y = bounds["min_y_mm"] - margin_y
        view_max_x = bounds["max_x_mm"] + margin_x
        view_max_y = bounds["max_y_mm"] + margin_y

    view_w = max(view_max_x - view_min_x, 1.0)
    view_h = max(view_max_y - view_min_y, 1.0)

    usable_w = width_px - (pad_x * 2)
    usable_h = height_px - (pad_y * 2)
    scale = min(usable_w / view_w, usable_h / view_h)

    plot_w = view_w * scale
    plot_h = view_h * scale
    offset_x = pad_x + (usable_w - plot_w) / 2.0
    offset_y = pad_y + (usable_h - plot_h) / 2.0

    def map_point(pt: tuple[float, float]) -> tuple[float, float]:
        x_mm, y_mm = pt
        x = offset_x + (x_mm - view_min_x) * scale
        y = offset_y + (y_mm - view_min_y) * scale
        return (x, y)

    def draw_text(pos: tuple[float, float], text: str, fill=None) -> None:
        if PREVIEW_SHOW_LABELS:
            draw.text(pos, text, fill=fill or fg_color)

    frame = [
        offset_x,
        offset_y,
        offset_x + plot_w,
        offset_y + plot_h,
    ]

    if fit_mode == "bed":
        draw.rectangle(
            frame,
            outline=fg_color,
            width=max(1, aa_scale),
        )

    if PREVIEW_SHOW_GRID:
        rough_step = max(view_w, view_h) / 10.0
        grid_steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000]
        grid_step = next((step for step in grid_steps if step >= rough_step), grid_steps[-1])

        start_x = int(view_min_x // grid_step) * grid_step
        end_x = int(view_max_x // grid_step + 1) * grid_step
        for gx in range(start_x, end_x + 1, grid_step):
            x, _ = map_point((float(gx), view_min_y))
            if offset_x <= x <= offset_x + plot_w:
                draw.line([(x, offset_y), (x, offset_y + plot_h)], fill=grid_color, width=max(1, aa_scale))
                draw_text((x + 4 * aa_scale, offset_y + 4 * aa_scale), str(gx), grid_color)

        start_y = int(view_min_y // grid_step) * grid_step
        end_y = int(view_max_y // grid_step + 1) * grid_step
        for gy in range(start_y, end_y + 1, grid_step):
            _, y = map_point((view_min_x, float(gy)))
            if offset_y <= y <= offset_y + plot_h:
                draw.line([(offset_x, y), (offset_x + plot_w, y)], fill=grid_color, width=max(1, aa_scale))
                draw_text((offset_x + 4 * aa_scale, y + 4 * aa_scale), str(gy), grid_color)

    if PREVIEW_SHOW_BOUNDS:
        min_corner = map_point((bounds["min_x_mm"], bounds["min_y_mm"]))
        max_corner = map_point((bounds["max_x_mm"], bounds["max_y_mm"]))
        draw.rectangle(
            [min_corner[0], min_corner[1], max_corner[0], max_corner[1]],
            outline=fg_color,
            width=max(1, aa_scale),
        )

    # Draw only the actual parsed paths. Do not auto-close paths; closing lines
    # must come from the RD data itself, otherwise the preview can invent geometry.
    if scan_fill_mode:
        merged_scan_paths = merge_scan_fill_spans(draw_paths)
        row_pitch_mm = estimate_scan_row_pitch(merged_scan_paths)
        scan_half_height_px = max(1.0, (row_pitch_mm * scale * 0.85))

        for path in merged_scan_paths:
            if len(path) != 2:
                if len(path) >= 2:
                    mapped = [map_point(pt) for pt in path]
                    draw.line(mapped, fill=fg_color, width=line_width, joint="curve")
                continue

            (x1_mm, y1_mm), (x2_mm, y2_mm) = path

            if abs(y2_mm - y1_mm) > 0.05:
                mapped = [map_point(pt) for pt in path]
                draw.line(mapped, fill=fg_color, width=line_width, joint="curve")
                continue

            left, center_y = map_point((min(x1_mm, x2_mm), (y1_mm + y2_mm) / 2.0))
            right, _ = map_point((max(x1_mm, x2_mm), (y1_mm + y2_mm) / 2.0))

            draw.rectangle(
                [left, center_y - scan_half_height_px, right, center_y + scan_half_height_px],
                fill=fg_color,
            )
    else:
        for path in draw_paths:
            if len(path) >= 2:
                mapped = [map_point(pt) for pt in path]
                draw.line(mapped, fill=fg_color, width=line_width, joint="curve")

            if PREVIEW_SHOW_POINTS:
                for idx, pt in enumerate(path):
                    x, y = map_point(pt)
                    radius = 4 * aa_scale if idx == 0 else 2 * aa_scale
                    draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=fg_color, fill=fg_color)

    if PREVIEW_SHOW_LABELS:
        label = (
            f"{title}  |  {bounds['width_mm']:.2f} x {bounds['height_mm']:.2f} mm  "
            f"|  {len(draw_paths)} path(s)  |  fit: {fit_mode}"
        )
        draw.text((pad_x, height_px - int(max(pad_x, pad_y) * 0.65)), label, fill=fg_color)

    image = image.resize((final_width_px, final_height_px), Image.Resampling.LANCZOS)
    image.save(out_path, format="PNG")

def resolve_data_path(file_path: str) -> Path:
    """
    Translate a host-visible addon_configs path to the app's mapped /config path.
    Leave other paths unchanged.
    """
    src = Path(file_path)

    if src.is_absolute() and str(src).startswith("/addon_configs/"):
        parts = src.parts
        if len(parts) >= 4:
            relative_parts = parts[3:]
            return Path("/config").joinpath(*relative_parts)

    return src


def render_rd_file(file_path: str, fit_mode: str | None = None) -> dict:
    src = resolve_data_path(file_path)
    if not src.exists():
        raise FileNotFoundError(f"file not found: {src}")

    fit_mode = str(fit_mode or PREVIEW_FIT_MODE).strip().lower()
    if fit_mode not in {"geometry", "bed"}:
        fit_mode = PREVIEW_FIT_MODE

    rd_bytes = src.read_bytes()
    raw = unswizzle(rd_bytes)
    preview_mode, paths = extract_preview_geometry(raw)
    paths = split_preview_paths_on_large_jumps(paths)
    paths = filter_isolated_preview_clusters(paths)
    points = flatten_preview_paths(paths)
    if not points:
        raise ValueError("no preview geometry found in RD file")

    bounds = compute_bounds(paths)

    # Named archive/debug copy in addon_config storage.
    # test.rd -> test.png, overwriting the previous preview for that file.
    render_name = f"{src.stem}.png"
    render_path = PREVIEW_DIR / render_name
    render_preview_png(paths, render_path, src.name, bounds, fit_mode=fit_mode)

    # Stable HA preview copy in /homeassistant/www
    HA_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(render_path, HA_PREVIEW_FILE)

    # Cache-busted URL for Home Assistant frontend use
    render_url = f"{HA_PREVIEW_URL}?v={time.time_ns()}"

    payload = {
        "render_ok": True,
        "name": src.stem,
        "file_name": src.name,
        "source_path": str(src),
        "image_file": render_name,
        "image_path": str(render_path),
        "image_url": render_url,
        "ha_preview_file": str(HA_PREVIEW_FILE),
        "path_count": len(paths),
        "point_count": len(points),
        "preview_fit_mode": fit_mode,
        "preview_mode": preview_mode,
        "preview_line_width": PREVIEW_LINE_WIDTH,
        "preview_show_grid": PREVIEW_SHOW_GRID,
        "preview_show_bounds": PREVIEW_SHOW_BOUNDS,
        "preview_show_points": PREVIEW_SHOW_POINTS,
        **bounds,
        "timestamp": int(time.time()),
    }

    client.publish(
        PREVIEW_STATUS_TOPIC,
        json.dumps(
            {
                "name": src.stem,
                "file_name": src.name,
                "image_file": render_name,
                "image_url": render_url,
                "path_count": len(paths),
                "point_count": len(points),
                "width_mm": bounds["width_mm"],
                "height_mm": bounds["height_mm"],
                "min_x_mm": bounds["min_x_mm"],
                "min_y_mm": bounds["min_y_mm"],
                "max_x_mm": bounds["max_x_mm"],
                "max_y_mm": bounds["max_y_mm"],
                "preview_fit_mode": PREVIEW_FIT_MODE,
                "preview_mode": preview_mode,
                "preview_line_width": PREVIEW_LINE_WIDTH,
                "preview_show_grid": PREVIEW_SHOW_GRID,
                "preview_show_bounds": PREVIEW_SHOW_BOUNDS,
                "preview_show_points": PREVIEW_SHOW_POINTS,
                "timestamp": payload["timestamp"],
            }
        ),
        qos=1,
        retain=True,
    )

    return payload

def publish_discovery() -> None:
    device = {
        "identifiers": [DEVICE_ID],
        "name": DEVICE_NAME,
        "manufacturer": "Custom",
        "model": "Ruida HA Bridge",
        "configuration_url": f"http://{RUIDA_IP}",
    }

    entities = [

        {
            "component": "image",
            "object_id": "preview_image",
            "payload": {
                "name": "Preview Image",
                "unique_id": eid("preview_image"),
                "default_entity_id": f"image.{eid('preview_image')}",
                "image_topic": PREVIEW_IMAGE_TOPIC,
                "content_type": "image/png",
                "json_attributes_topic": PREVIEW_STATUS_TOPIC,
                "icon": "mdi:image",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
            },
        },
        {
            "component": "number",
            "object_id": "rotary_diameter_setpoint",
            "payload": {
                "name": "Set Rotary Diameter",
                "unique_id": eid("rotary_diameter_setpoint"),
                "default_entity_id": f"number.{eid('rotary_diameter_setpoint')}",
                "command_topic": CMD_TOPIC,
                "command_template": '{"cmd":"set_rotary_diameter","diameter_mm":{{ value }}}',
                "state_topic": ATTR_TOPIC,
                "value_template": "{{ value_json.settings.diameter }}",
                "min": 1,
                "max": 1000,
                "step": 0.001,
                "mode": "box",
                "unit_of_measurement": "mm",
                "icon": "mdi:diameter",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
            },
        },
        {
            "component": "switch",
            "object_id": "rotary_enable",
            "payload": {
                "name": "Rotary Enable",
                "unique_id": eid("rotary_enable"),
                "default_entity_id": f"switch.{eid('rotary_enable')}",
                "command_topic": CMD_TOPIC,
                "command_template": '{"cmd":"set_rotary_enabled","enabled":{{ "true" if value == "ON" else "false" }}}',
                "state_topic": ROTARY_STATE_TOPIC,
                "payload_on": "ON",
                "payload_off": "OFF",
                "state_on": "ON",
                "state_off": "OFF",
                "icon": "mdi:rotate-3d-variant",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
            },
        },
        {
            "component": "sensor",
            "object_id": "file_list",
            "payload": {
                "name": "Saved File List",
                "unique_id": eid("file_list"),
                "default_entity_id": f"sensor.{eid('file_list')}",
                "state_topic": FILE_LIST_TOPIC,
                "value_template": "{{ value_json | count }}",
                "json_attributes_topic": FILE_LIST_TOPIC,
                "json_attributes_template": "{{ {'files': value_json} | tojson }}",
                "icon": "mdi:file-document-multiple-outline",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
            },
        },


        {
            "component": "sensor",
            "object_id": "x_axis",
            "payload": {
                "name": "X Axis",
                "unique_id": eid("x_axis"),
                "default_entity_id": f"sensor.{eid('x_axis')}",
                "state_topic": X_AXIS_TOPIC,
                "value_template": "{{ value_json.position_mm }}",
                "json_attributes_topic": X_AXIS_TOPIC,
                "unit_of_measurement": "mm",
                "icon": "mdi:axis-x-arrow",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
            },
        },
        {
            "component": "sensor",
            "object_id": "y_axis",
            "payload": {
                "name": "Y Axis",
                "unique_id": eid("y_axis"),
                "default_entity_id": f"sensor.{eid('y_axis')}",
                "state_topic": Y_AXIS_TOPIC,
                "value_template": "{{ value_json.position_mm }}",
                "json_attributes_topic": Y_AXIS_TOPIC,
                "unit_of_measurement": "mm",
                "icon": "mdi:axis-y-arrow",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
            },
        },
        {
            "component": "sensor",
            "object_id": "z_axis",
            "payload": {
                "name": "Z Axis",
                "unique_id": eid("z_axis"),
                "default_entity_id": f"sensor.{eid('z_axis')}",
                "state_topic": Z_AXIS_TOPIC,
                "value_template": "{{ value_json.position_mm }}",
                "json_attributes_topic": Z_AXIS_TOPIC,
                "unit_of_measurement": "mm",
                "icon": "mdi:axis-z-arrow",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
            },
        },
        {
            "component": "sensor",
            "object_id": "xy_location",
            "payload": {
                "name": "Current Location",
                "unique_id": eid("xy_location"),
                "default_entity_id": f"sensor.{eid('xy_location')}",
                "state_topic": XY_LOCATION_TOPIC,
                "value_template": "{{ value_json.location }}",
                "json_attributes_topic": XY_LOCATION_TOPIC,
                "icon": "mdi:crosshairs-gps",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
            },
        },

        {
            "component": "binary_sensor",
            "object_id": "laser_1_enabled",
            "payload": {
                "name": "Laser 1 Enabled",
                "unique_id": eid("laser_1_enabled"),
                "default_entity_id": f"binary_sensor.{eid('laser_1_enabled')}",
                "state_topic": LASER_1_TOPIC,
                "value_template": "{{ value_json.state }}",
                "json_attributes_topic": LASER_1_TOPIC,
                "payload_on": "ON",
                "payload_off": "OFF",
                "device_class": "power",
                "icon": "mdi:laser-pointer",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
            },
        },
        {
            "component": "binary_sensor",
            "object_id": "laser_2_enabled",
            "payload": {
                "name": "Laser 2 Enabled",
                "unique_id": eid("laser_2_enabled"),
                "default_entity_id": f"binary_sensor.{eid('laser_2_enabled')}",
                "state_topic": LASER_2_TOPIC,
                "value_template": "{{ value_json.state }}",
                "json_attributes_topic": LASER_2_TOPIC,
                "payload_on": "ON",
                "payload_off": "OFF",
                "device_class": "power",
                "icon": "mdi:laser-pointer",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
            },
        },

        {
            "component": "sensor",
            "object_id": "status",
            "payload": {
                "name": "Machine Status",
                "unique_id": eid("status"),
                "default_entity_id": f"sensor.{eid('status')}",
                "state_topic": ATTR_TOPIC,
                "value_template": "{{ value_json.status_text }}",
                "icon": "mdi:information-outline",
                "availability_topic": STATE_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
                "device": device,
                "json_attributes_topic": ATTR_TOPIC,
                "json_attributes_template": "{{ {'controller_ip': value_json.ruida_ip, 'bridge_status': 'online'} | tojson }}",
            },
        },
    ]

    for command, meta in BUTTON_META.items():
        entities.append(
            {
                "component": "button",
                "object_id": command,
                "payload": {
                    "name": meta["name"],
                    "unique_id": meta["unique_id"],
                    "default_entity_id": f"button.{meta['unique_id']}",
                    "command_topic": CMD_TOPIC,
                    "payload_press": command,
                    "icon": meta["icon"],
                    "availability_topic": STATE_TOPIC,
                    "payload_available": "online",
                    "payload_not_available": "offline",
                    "device": device,
                },
            }
        )

    for setting in MACHINE_SETTINGS:
        if setting["key"] in AXIS_SETTING_KEYS or setting["key"] in LASER_SETTING_KEYS:
            continue

        sensor_payload = {
            "name": setting["name"],
            "unique_id": eid(setting["key"]),
            "default_entity_id": f"sensor.{eid(setting['key'])}",
            "state_topic": ATTR_TOPIC,
            "value_template": f"{{{{ value_json.settings.{setting['key']} }}}}",
            "icon": setting["icon"],
            "availability_topic": STATE_TOPIC,
            "payload_available": "online",
            "payload_not_available": "offline",
            "device": device,
        }
        if setting["unit"]:
            sensor_payload["unit_of_measurement"] = setting["unit"]

        entities.append(
            {
                "component": "sensor",
                "object_id": setting["key"],
                "payload": sensor_payload,
            }
        )

    for entity in entities:
        topic = (
            f"{HA_DISCOVERY_PREFIX}/"
            f"{entity['component']}/{DEVICE_ID}/{entity['object_id']}/config"
        )
        client.publish(topic, json.dumps(entity["payload"]), qos=1, retain=True)


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"ON_CONNECT fired reason_code={reason_code}", flush=True)
    client.subscribe(CMD_TOPIC, qos=1)
    client.publish(STATE_TOPIC, payload="online", qos=1, retain=True)
    command_queue.put("sync_files")


def on_message(client, userdata, msg):
    global current_x_mm, current_y_mm, current_z_mm

    try:
        raw_payload = msg.payload.decode("utf-8").strip()
    except Exception:
        return

    if msg.topic != CMD_TOPIC:
        return

    payload = raw_payload.lower()

    if payload in COMMAND_MAP or payload == "sync_files":
        command_queue.put(payload)
        publish_result(True, cmd=payload, queued=True)
        return

    if payload == "file_list":
        command_queue.put("sync_files")
        publish_result(True, cmd="file_list", queued=True, sync_files=True)
        return

    if payload == "z_up":
        try:
            send_z_button_move("up")
            publish_result(True, cmd="z_up", step_mm=Z_BUTTON_STEP_MM)
        except Exception as exc:
            traceback.print_exc()
            publish_result(False, cmd="z_up", error=str(exc))
        return

    if payload == "z_down":
        try:
            send_z_button_move("down")
            publish_result(True, cmd="z_down", step_mm=Z_BUTTON_STEP_MM)
        except Exception as exc:
            traceback.print_exc()
            publish_result(False, cmd="z_down", error=str(exc))
        return

    try:
        data = json.loads(raw_payload)
        if isinstance(data, dict):
            cmd = str(data.get("cmd", "")).strip().lower()

            if cmd == "jog_start":
                action = str(data.get("action", "")).strip().lower()
                send_continuous_jog(action, "start")
                publish_result(True, cmd="jog_start", action=action)
                return

            if cmd == "jog_stop":
                action = str(data.get("action", "")).strip().lower()
                send_continuous_jog(action, "stop")
                publish_result(True, cmd="jog_stop", action=action)
                return

            if cmd == "file_list":
                command_queue.put("sync_files")
                publish_result(True, cmd="file_list", queued=True, sync_files=True)
                return

            if cmd == "sync_files":
                command_queue.put("sync_files")
                publish_result(True, cmd="sync_files", queued=True)
                return

            if cmd == "download_file":
                slot = int(data["slot"])
                name = str(data.get("name") or "")
                command_queue.put({"cmd": "download_file", "slot": slot, "name": name})
                publish_result(True, cmd="download_file", queued=True, slot=slot, name=name)
                return

            if cmd == "render_rd":
                file_path = str(data["path"]).strip()
                requested_fit_mode = str(data.get("fit_mode", "")).strip().lower()
                if requested_fit_mode not in {"geometry", "bed"}:
                    requested_fit_mode = PREVIEW_FIT_MODE

                preview_payload = render_rd_file(file_path, requested_fit_mode)

                publish_preview_image_file()

                publish_preview(preview_payload)
                publish_result(
                    True,
                    cmd="render_rd",
                    name=preview_payload["name"],
                    file_name=preview_payload["file_name"],
                    image_file=preview_payload["image_file"],
                    image_url=preview_payload["image_url"],
                    point_count=preview_payload["point_count"],
                    preview_fit_mode=preview_payload["preview_fit_mode"],
                )
                return

            if cmd == "rel_xy":
                dx_mm = float(data["dx"])
                dy_mm = float(data["dy"])

                if current_x_mm is None or current_y_mm is None:
                    publish_result(False, error="position_unknown")
                    return

                target_x_mm = current_x_mm + dx_mm
                target_y_mm = current_y_mm + dy_mm

                if not (0 <= target_x_mm <= MAX_X_MM and 0 <= target_y_mm <= MAX_Y_MM):
                    publish_result(
                        False,
                        error="out_of_bounds",
                        dx=dx_mm,
                        dy=dy_mm,
                        target_x=target_x_mm,
                        target_y=target_y_mm,
                    )
                    return

                send_rel_xy(dx_mm, dy_mm)
                publish_result(True, cmd="rel_xy", dx=dx_mm, dy=dy_mm)
                return

            if cmd == "abs_xy":
                x_mm = float(data["x"])
                y_mm = float(data["y"])

                if not (0 <= x_mm <= MAX_X_MM and 0 <= y_mm <= MAX_Y_MM):
                    publish_result(False, error="out_of_bounds", x=x_mm, y=y_mm)
                    return

                send_abs_xy(x_mm, y_mm)
                publish_result(True, cmd="abs_xy", x=x_mm, y=y_mm)
                return

            if cmd == "go_to_z":
                result = send_abs_z(float(data["z"]))
                publish_result(bool(result.get("ok")), **{k: v for k, v in result.items() if k != "ok"})
                return

            if cmd == "set_rotary_diameter":
                diameter_mm = float(data["diameter_mm"])
                command_queue.put({"cmd": "set_rotary_diameter", "diameter_mm": diameter_mm})
                publish_result(True, cmd="set_rotary_diameter", queued=True, diameter_mm=diameter_mm)
                return

            if cmd == "set_rotary_enabled":
                enabled_raw = data["enabled"]
                if isinstance(enabled_raw, bool):
                    enabled = enabled_raw
                elif isinstance(enabled_raw, str):
                    enabled = enabled_raw.strip().lower() in ("1", "true", "on", "yes", "enable", "enabled")
                else:
                    enabled = bool(enabled_raw)

                command_queue.put({"cmd": "set_rotary_enabled", "enabled": enabled})
                publish_result(True, cmd="set_rotary_enabled", queued=True, enabled=enabled)
                return

    except Exception as exc:
        traceback.print_exc()
        publish_result(False, error=str(exc))
        return


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
if MQTT_USER:
    client.username_pw_set(MQTT_USER, MQTT_PASS)

client.will_set(STATE_TOPIC, payload="offline", qos=1, retain=True)
client.on_connect = on_connect
client.on_message = on_message
print("BEFORE MQTT CONNECT", flush=True)
client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
print("AFTER MQTT CONNECT", flush=True)
client.loop_start()

publish_discovery()
command_queue.put("sync_files")

while True:
    payload = {
        "ruida_ip": RUIDA_IP,
        "ruida_port": RUIDA_PORT,
        "local_port": RUIDA_LOCAL_PORT,
        "udp_socket_open_ok": False,
        "udp_error": "",
        "x_mm": None,
        "y_mm": None,
        "z_mm": None,
        "xy_location": "unknown",
        "status_raw": None,
        "status_byte_1": None,
        "status_byte_2": None,
        "status_text": "unknown",
        "timestamp": int(time.time()),
        "settings": dict(cached_settings),
        "rotary_enabled": rotary_enabled_state,
        "laser_1_enabled": None,
        "laser_1_enable_raw": None,
        "laser_2_enabled": None,
        "laser_2_enable_raw": None,
    }

    controller_configured = RUIDA_IP.strip() not in ("", "0.0.0.0", "127.0.0.1", "localhost")
    if not controller_configured:
        payload["udp_error"] = "Ruida controller IP is not configured"
        payload["status_text"] = "not_configured"
        client.publish(STATE_TOPIC, json.dumps(payload), qos=1, retain=True)
        client.publish(ATTR_TOPIC, json.dumps(payload), qos=1, retain=True)
        time.sleep(2)
        continue

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.5)

    current_command = None
    current_command_name = None
    current_command_data = None

    try:
        current_command = command_queue.get_nowait()
        if isinstance(current_command, dict):
            current_command_name = current_command.get("cmd")
            current_command_data = current_command
        else:
            current_command_name = current_command
    except Empty:
        pass

    try:
        sock.bind(("0.0.0.0", RUIDA_LOCAL_PORT))
        payload["udp_socket_open_ok"] = True

        if current_command_name in COMMAND_MAP:
            payload[f"{current_command_name}_ack"] = send_command_burst(
                sock, COMMAND_MAP[current_command_name]
            )

        if current_command_name in ("file_list", "sync_files"):
            jobs = get_file_list(sock)

            downloaded = []
            if current_command_name == "sync_files":
                downloaded = download_missing_controller_files(sock, jobs)

            merged_files = merge_controller_and_local_files(jobs)
            client.publish(FILE_LIST_TOPIC, json.dumps(merged_files), qos=1, retain=False)

            publish_result(
                True,
                cmd=current_command_name,
                count=len(merged_files),
                controller_count=len(jobs),
                local_count=len([item for item in merged_files if item.get("source") == "local"]),
                downloaded_count=len([item for item in downloaded if item.get("ok")]),
                downloaded=downloaded,
                download_dir=str(DOWNLOAD_DIR),
            )

        if current_command_name == "download_file":
            slot = int(current_command_data["slot"])
            name = str(current_command_data.get("name") or "")
            result = download_controller_file(sock, slot=slot, name=name)
            publish_result(**result)

        if current_command_name == "set_rotary_diameter":
            diameter_mm = float(current_command_data["diameter_mm"])
            result = set_rotary_diameter(sock, diameter_mm)
            publish_result(cmd="set_rotary_diameter", **result)
            if result.get("ok"):
                settings_loaded = False

        if current_command_name == "set_rotary_enabled":
            enabled = bool(current_command_data["enabled"])
            result = set_rotary_enabled(sock, enabled)
            publish_result(cmd="set_rotary_enabled", **result)
            if result.get("ok"):
                rotary_enabled_state = enabled
                client.publish(
                    ROTARY_STATE_TOPIC,
                    "ON" if enabled else "OFF",
                    qos=1,
                    retain=True,
                )

        x_reply = query(sock, bytes([0xDA, 0x00, 0x04, 0x21]))
        y_reply = query(sock, bytes([0xDA, 0x00, 0x04, 0x31]))
        z_reply = query(sock, bytes([0xDA, 0x00, 0x04, 0x41]))
        status_reply = query(sock, bytes([0xDA, 0x00, 0x04, 0x00]))

        x_raw = tail_u32(x_reply)
        y_raw = tail_u32(y_reply)
        z_raw = tail_u32(z_reply)

        payload["x_mm"] = round(x_raw / 1000, 2)
        payload["y_mm"] = round(y_raw / 1000, 2)
        payload["z_mm"] = round(z_raw / 1000, 2)
        payload["xy_location"] = format_xy_location(payload["x_mm"], payload["y_mm"])

        current_x_mm = payload["x_mm"]
        current_y_mm = payload["y_mm"]
        current_z_mm = payload.get("z_mm")
        payload["status_raw"] = tail_u32(status_reply)
        payload["status_byte_1"] = status_reply[-2]
        payload["status_byte_2"] = status_reply[-1]
        payload["status_text"] = decode_status_text(
            payload["status_byte_1"], payload["status_byte_2"]
        )

        if not settings_loaded:
            new_settings = {}
            for setting in MACHINE_SETTINGS:
                reply = query_setting(sock, setting["id"])
                raw = tail_u32(reply)
                new_settings[setting["key"]] = setting_value_from_raw(setting, raw)

            cached_settings = new_settings
            settings_loaded = True

        try:
            rotary_reply = query_setting(sock, ROTARY_ENABLE_SETTING_ID)
            rotary_raw = tail_u32(rotary_reply)
            rotary_enabled_state = bool(rotary_raw)
            client.publish(
                ROTARY_STATE_TOPIC,
                "ON" if rotary_enabled_state else "OFF",
                qos=1,
                retain=True,
            )
        except Exception:
            traceback.print_exc()

        try:
            laser_1_reply = query_setting(sock, LASER_1_ENABLE_SETTING_ID)
            laser_1_raw = tail_u32(laser_1_reply)
            laser_1_enabled = bool(laser_1_raw & LASER_ENABLE_BIT)
            payload["laser_1_enabled"] = laser_1_enabled
            payload["laser_1_enable_raw"] = laser_1_raw
        except Exception:
            traceback.print_exc()

        try:
            laser_2_reply = query_setting(sock, LASER_2_ENABLE_SETTING_ID)
            laser_2_raw = tail_u32(laser_2_reply)
            laser_2_enabled = bool(laser_2_raw & LASER_ENABLE_BIT)
            payload["laser_2_enabled"] = laser_2_enabled
            payload["laser_2_enable_raw"] = laser_2_raw
        except Exception:
            traceback.print_exc()

        payload["settings"] = dict(cached_settings)
        payload["rotary_enabled"] = rotary_enabled_state

    except Exception as exc:
        traceback.print_exc()
        payload["udp_error"] = str(exc)

        if current_command_name in ("file_list", "sync_files"):
            publish_result(False, cmd=current_command_name, error=str(exc))
        elif current_command_name == "download_file":
            publish_result(False, cmd="download_file", error=str(exc))
        elif current_command_name == "set_rotary_diameter":
            publish_result(False, cmd="set_rotary_diameter", error=str(exc))
        elif current_command_name == "set_rotary_enabled":
            publish_result(False, cmd="set_rotary_enabled", error=str(exc))

    finally:
        sock.close()

    settings_snapshot = dict(payload.get("settings") or {})
    timestamp = int(payload.get("timestamp") or time.time())

    client.publish(
        X_AXIS_TOPIC,
        payload=json.dumps(axis_payload("x", payload.get("x_mm"), settings_snapshot, timestamp)),
        qos=1,
        retain=True,
    )
    client.publish(
        Y_AXIS_TOPIC,
        payload=json.dumps(axis_payload("y", payload.get("y_mm"), settings_snapshot, timestamp)),
        qos=1,
        retain=True,
    )
    client.publish(
        Z_AXIS_TOPIC,
        payload=json.dumps(axis_payload("z", payload.get("z_mm"), settings_snapshot, timestamp)),
        qos=1,
        retain=True,
    )
    client.publish(
        XY_LOCATION_TOPIC,
        payload=json.dumps(
            {
                "location": format_xy_location(payload.get("x_mm"), payload.get("y_mm")),
                "x_mm": payload.get("x_mm"),
                "y_mm": payload.get("y_mm"),
                "timestamp": timestamp,
            }
        ),
        qos=1,
        retain=True,
    )
    client.publish(
        LASER_1_TOPIC,
        payload=json.dumps(
            laser_payload(
                1,
                payload.get("laser_1_enabled"),
                payload.get("laser_1_enable_raw"),
                settings_snapshot,
                timestamp,
            )
        ),
        qos=1,
        retain=True,
    )
    client.publish(
        LASER_2_TOPIC,
        payload=json.dumps(
            laser_payload(
                2,
                payload.get("laser_2_enabled"),
                payload.get("laser_2_enable_raw"),
                settings_snapshot,
                timestamp,
            )
        ),
        qos=1,
        retain=True,
    )

    client.publish(ATTR_TOPIC, payload=json.dumps(payload), qos=1, retain=True)
    time.sleep(2)

