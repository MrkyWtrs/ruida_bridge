# Ruida Bridge

Ruida Bridge is a Home Assistant app that exposes Ruida controller data and control functions to Home Assistant using MQTT.

## Current version

Working baseline: **0.9.0 Continuous Jog Checkpoint**

## What it does

- Provides a Home Assistant Ingress web UI from the app page
- Publishes Ruida controller status and position data
- Publishes grouped axis data for:
  - X Axis
  - Y Axis
  - Z Axis
  - Current Location
- Publishes selected machine settings
- Publishes grouped laser status entities:
  - Laser 1 Enabled
  - Laser 2 Enabled
- Includes laser setting details as laser entity attributes:
  - frequency
  - minimum power
  - maximum power
  - raw enable value
- Provides Home Assistant buttons for:
  - Home Machine
  - Jog Left
  - Jog Right
  - Jog Up
  - Jog Down
  - Jog Z Up
  - Jog Z Down
  - Get File List
- Provides Home Assistant controls for:
  - Set Rotary Diameter
  - Rotary Enable
- Supports MQTT JSON commands for:
  - relative XY moves
  - absolute XY moves
  - rotary diameter updates
  - rotary enable/disable
  - saved file list refresh
  - RD preview rendering
- Enforces configurable XY bounds before sending move commands
- Publishes command results to `ruida/bridge/result`
- Publishes saved file list data to `ruida/bridge/file_list`
- Publishes RD preview metadata to `ruida/bridge/preview`
- Publishes RD preview image metadata to `ruida/bridge/preview_status`
- Publishes the actual preview image to `ruida/bridge/preview_image`


## Web frontend

Version 0.6.0 adds a first-pass Home Assistant Ingress web frontend.

The app configuration enables:

```yaml
ingress: true
ingress_port: 8099
panel_icon: mdi:laser-cutter
panel_title: Ruida Bridge
```

After rebuilding and starting the app, Home Assistant should show **Open Web UI** on the Ruida Bridge app page.

The web frontend is served by `web.py` and static files in `/static`.

Frontend controls currently include:

- Large preview image panel
- Bridge status
- Machine status
- Current XY readout
- Home
- Jog left/right/up/down
- Jog Z up/down
- Get file list
- Render selected RD file path

The frontend does not bypass the existing backend. It publishes to the same MQTT command topic already used by Home Assistant controls:

```text
ruida/bridge/cmd
```

The web server listens on port `8099`, matching the configured `ingress_port`.

## Required configuration

This app expects these values from the Home Assistant app configuration:

- `mqtt_host`
- `mqtt_port`
- `mqtt_user`
- `mqtt_pass`
- `mqtt_topic_prefix`
- `mqtt_client_id`
- `ha_discovery_prefix`
- `ruida_ip`
- `ruida_port`
- `ruida_local_port`
- `ruida_max_x_mm`
- `ruida_max_y_mm`
- `ruida_z_button_step_mm`
- `device_id`
- `device_name`
- `entity_prefix`
- `preview_fit_mode`
- `preview_show_grid`
- `preview_show_points`
- `preview_show_bounds`
- `preview_show_labels`
- `preview_line_width`
- `preview_background`
- `preview_foreground`

These values are exported by `run.sh` as environment variables for `app.py`. The same MQTT-related values are also used by `web.py` for the Ingress frontend.

## Home Assistant identity options

Version 0.5.0 adds configurable Home Assistant identity values so the app can be reused on other Home Assistant instances or for multiple Ruida devices.

Default values:

- `device_id`: `ruida_bridge`
- `device_name`: `Ruida Bridge`
- `entity_prefix`: `ruida`

With the default values, existing entity IDs remain unchanged.

Example default entities:

- `sensor.ruida_status`
- `sensor.ruida_x_axis`
- `image.ruida_preview_image`

Changing `entity_prefix` changes the generated Home Assistant entity IDs.

Example:

```yaml
entity_prefix: shop_laser

would generate entities such as:

sensor.shop_laser_status
sensor.shop_laser_x_axis
image.shop_laser_preview_image

Changing device_name changes the displayed Home Assistant device name.

Changing device_id changes the MQTT discovery device identifier and discovery topic path. Use a unique device_id if running more than one Ruida Bridge instance.

## Preview rendering options

Version 0.5.1 adds configurable preview rendering options.

Default values:

- `preview_fit_mode`: `geometry`
- `preview_show_grid`: `true`
- `preview_show_points`: `false`
- `preview_show_bounds`: `true`
- `preview_show_labels`: `true`
- `preview_line_width`: `4`
- `preview_background`: `MediumBlue`
- `preview_foreground`: `white`

Preview fit modes:

- `geometry`: fits the rendered image tightly around parsed geometry with a small margin.
- `bed`: renders against the configured bed size using `ruida_max_x_mm` and `ruida_max_y_mm`.

Preview image improvements:

- The renderer no longer auto-closes paths. If a shape is closed, that close line must come from parsed RD data.
- Images are rendered oversized and downsampled for cleaner diagonal/vector lines.
- The grid, point markers, bounds box, labels, line width, and colors can be changed from app options.
- Preview metadata includes the active render options.

Storage paths

This app uses the Home Assistant addon_config map.

Host-visible path:

/homeassistant/www/ruida_bridge/downloads/...

In-app path:

/config/...

Example:

Downloaded RD file: /homeassistant/www/ruida_bridge/downloads/test.rd
In-app resolved path: /config/test.rd
Preview archive folder in app: /config/images
Stable Home Assistant preview image path: /homeassistant/www/ruida_bridge/latest.png
Stable Home Assistant preview URL: /local/ruida_bridge/latest.png
MQTT topics

Command topic:

ruida/bridge/cmd

Result topic:

ruida/bridge/result

Bridge status topic:

ruida/bridge/status

Main attributes topic:

ruida/bridge/attributes

Rotary state topic:

ruida/bridge/rotary_enabled

Saved file list topic:

ruida/bridge/file_list

Preview metadata topic:

ruida/bridge/preview

Preview image status topic:

ruida/bridge/preview_status

Preview image topic:

ruida/bridge/preview_image

Grouped axis topics:

ruida/bridge/axis/x
ruida/bridge/axis/y
ruida/bridge/axis/z
ruida/bridge/xy_location

Grouped laser topics:

ruida/bridge/laser/1
ruida/bridge/laser/2
Home Assistant entities

The app publishes MQTT discovery entities for the Ruida Bridge device.

Status
sensor.ruida_status

Attributes include:

controller IP
bridge status
Position
sensor.ruida_x_axis
sensor.ruida_y_axis
sensor.ruida_z_axis
sensor.ruida_xy_location
Laser status
binary_sensor.ruida_laser_1_enabled
binary_sensor.ruida_laser_2_enabled

Laser entity attributes include:

enabled state
raw enable value
frequency
minimum power
maximum power
Rotary
number.ruida_rotary_diameter_setpoint
switch.ruida_rotary_enable
Saved files
sensor.ruida_file_list
button.ruida_get_file_list

The saved file list sensor exposes file data as attributes.

Jog buttons
button.ruida_home_machine
button.ruida_jog_left
button.ruida_jog_right
button.ruida_jog_up
button.ruida_jog_down
button.ruida_jog_z_up
button.ruida_jog_z_down
Preview image
image.ruida_preview_image

The Preview Image entity receives the rendered RD preview through MQTT and is attached to the Ruida Bridge device.

JSON command examples
Relative move
{"cmd":"rel_xy","dx":1,"dy":0}
Absolute move
{"cmd":"abs_xy","x":100,"y":100}
Set rotary diameter
{"cmd":"set_rotary_diameter","diameter_mm":100}
Enable rotary
{"cmd":"set_rotary_enabled","enabled":true}
Disable rotary
{"cmd":"set_rotary_enabled","enabled":false}
Get saved file list
{"cmd":"file_list"}
Render an RD file from the app config mount
{"cmd":"render_rd","path":"/homeassistant/www/ruida_bridge/downloads/test.rd"}
RD preview behavior

A successful render_rd command:

Resolves the requested RD file path.
Reads and unswizzles the RD file.
Extracts preview geometry.
Renders a PNG preview.
Saves a named preview image in the app image folder.
Copies the latest preview to the Home Assistant www folder.
Publishes preview metadata.
Publishes the preview image to the MQTT image entity.

Preview archive naming:

filename.rd → filename.png

Example:

test.rd → test.png

This avoids unlimited timestamped image buildup.

The stable Home Assistant preview file is always copied to:

/homeassistant/www/ruida_bridge/latest.png

The Home Assistant frontend URL is:

/local/ruida_bridge/latest.png

A cache-busted URL is included in preview metadata so Home Assistant can refresh the image after each render.

RD preview parser

Current supported preview geometry records:

0x88 - move absolute
0x89 - move relative
0x8A - move horizontal
0x8B - move vertical
0xA8 - cut absolute
0xA9 - cut relative
0xAA - cut horizontal
0xAB - cut vertical

The parser separates paths so unrelated shapes are not connected together.

The parser walks the RD byte stream command-by-command instead of scanning every byte for 0x88/0xA8. This prevents parameter bytes inside dense fill/scanline data from being misread as fake vector commands.

The renderer also avoids drawing synthetic closing lines between the last and first point of a path. This keeps the preview closer to the parsed RD data and prevents invented diagonals/shape closures.

Known limitation:

Advanced RD geometry is still incomplete.
Circles, arcs, curves, fills, scan/hatch records, and some compound shapes may not render correctly until more RD record types are decoded.
Command results

Command results are published to:

ruida/bridge/result

Example successful result:

{"ok":true,"cmd":"rel_xy","dx":1.0,"dy":0.0}

Example bounds failure:

{"ok":false,"error":"out_of_bounds","x":5000.0,"y":5000.0}
Startup behavior

On startup, the app:

Connects to MQTT.
Publishes MQTT discovery.
Publishes bridge availability.
Queues an automatic saved file list refresh.
Begins polling controller position, status, rotary state, laser state, and cached settings.
Notes
XY moves are checked against configured max X/Y limits before being sent.
Z jog button step size is controlled by ruida_z_button_step_mm.
Rotary diameter writes use the known-good LightBurn-style packet burst.
Rotary enable writes preserve the current rotary diameter.
Laser enable detection uses bitmask 0x2000.
The preview image entity replaces the older camera-style preview approach.
Version 0.5.0 adds configurable Home Assistant identity options for easier reuse across installs.
Remaining preview parser improvements

Future preview parser work:

Continue improving advanced RD shape parsing/rendering.
0xAA and 0x8A are now parsed as horizontal cut/move records.
Determine whether those records represent scan-line movement, fill raster/vector segments, or layer/process metadata.
Once decoded, decide whether fill jobs should render as:
scan lines
solid filled regions
hatch-style preview
metadata-only fill detection

Current preview status:

Line/vector preview: working and useful
Fill preview: serviceable for artwork placement, not accurate as a true toolpath/process preview


---

# Beta testing safety and backup notes

Ruida Bridge can send real movement commands to a physical laser controller. Treat beta testing the same way you would treat testing a new control panel.

## Before testing

- Back up the current add-on folder before replacing files.
- Save a copy of the current add-on configuration.
- Confirm the configured maximum X and Y travel values match the machine.
- Remove material from the bed before movement testing.
- Keep a hand near the emergency stop.
- Test small jog movements before large movements.
- Confirm jog direction before using absolute or relative movement commands.
- Do not run unattended tests.

## Suggested backup command

Run from the Home Assistant terminal:

    cp -a /addons/ruida_bridge /addons/ruida_bridge.backup_$(date +%Y%m%d_%H%M%S)

## Restore from backup

Stop the add-on first, then restore the previous folder:

    rm -rf /addons/ruida_bridge
    cp -a /addons/ruida_bridge.backup_YYYYMMDD_HHMMSS /addons/ruida_bridge

Then reload local add-ons and start Ruida Bridge again.

## Minimum beta bug report info

Include:

- Ruida Bridge version
- Home Assistant Core version
- Supervisor version
- Ruida controller model
- add-on log excerpt
- screenshot if UI-related
- MQTT result payload if command-related
- RD file if preview/render-related
