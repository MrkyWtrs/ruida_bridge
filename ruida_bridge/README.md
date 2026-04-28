# Ruida Bridge 0.9.1 Controller Extents Checkpoint

Ruida Bridge is a Home Assistant App/add-on that connects a Ruida laser controller to Home Assistant using MQTT discovery and a local web dashboard.

## Current baseline

**Version:** 0.9.1 Controller Extents Checkpoint

Active frontend files are only in `static/`:

- `static/index.html`
- `static/style.css`
- `static/app.js`

The Dockerfile copies `static/` to `/static`, and `web.py` serves the frontend from `/static`.

## Requirements

- Home Assistant OS or a Supervisor-based Home Assistant install
- MQTT broker available to Home Assistant
- Ruida controller reachable from the Home Assistant host network
- Ruida controller network port: UDP `50200`
- Home Assistant MQTT integration enabled
- MQTT discovery enabled

## Installation

1. Copy the `ruida_bridge` folder into the Home Assistant local add-ons directory: `/addons/ruida_bridge`
2. In Home Assistant, go to **Settings → Add-ons → Add-on Store**
3. Open the overflow menu and choose **Reload**
4. Find **Ruida Bridge** in the local add-ons section
5. Open the add-on and review the **Configuration** tab
6. Set the MQTT host, MQTT credentials, Ruida controller IP, Ruida port, and bed size limits
7. Start the add-on
8. Open the add-on web UI from the add-on page

## Required configuration

Typical options:

    mqtt_host: "core-mosquitto"
    mqtt_port: 1883
    mqtt_user: "your_mqtt_user"
    mqtt_pass: "your_mqtt_password"
    mqtt_topic_prefix: "ruida"
    mqtt_client_id: "ruida-ha-bridge"
    ha_discovery_prefix: "homeassistant"
    ruida_ip: "0.0.0.0"
    ruida_port: 50200
    ruida_local_port: 40200
    override_controller_extents: false
    ruida_max_x_mm: 0
    ruida_max_y_mm: 0
    ruida_max_z_mm: 0
    ruida_z_button_step_mm: 1

## First startup checks

After starting the add-on:

1. Check the add-on log for startup errors
2. Confirm MQTT connects successfully
3. Confirm the Ruida controller responds to polling
4. Confirm Home Assistant discovers the Ruida Bridge device
5. Confirm the dashboard loads
6. Confirm X/Y/Z position values update
7. Confirm the machine status changes when the controller state changes

## Home Assistant entities

The bridge publishes MQTT discovery entities for the Ruida Bridge device, including machine status, position, jog buttons, Z buttons, rotary controls, preview image, and controller attributes.

Exact entity names may vary depending on Home Assistant entity registry history.

## Web dashboard

The web dashboard provides RD file preview, machine information, XY jog controls, Z controls, file list/actions, download/preview workflow, and controller state display.

## File and preview storage

Downloaded RD files and preview images are stored inside the Home Assistant-accessible web path:

    /homeassistant/www/ruida_bridge/

The current preview image is published as:

    /homeassistant/www/ruida_bridge/latest.png

Downloaded RD files are stored under:

    /homeassistant/www/ruida_bridge/downloads/

## Safety notes

This bridge can send real movement commands to a physical laser controller.

Before beta testing movement commands:

- remove material from the bed
- keep the lid open if appropriate for your machine safety workflow
- keep a hand near the emergency stop
- verify the active X/Y/Z travel limits
- test jog buttons at a small step size first
- confirm jog direction before using larger moves
- do not run unattended tests

## Known limitations

- Intended for trusted local Home Assistant users
- No per-user operator lock yet
- Preview rendering is useful but not a full LightBurn-equivalent renderer
- Advanced RD geometry support is still incomplete
- File upload/send-to-controller workflow is still experimental
- Controller behavior may vary by Ruida model and firmware

## Troubleshooting

### Add-on starts but no Home Assistant entities appear

Check that MQTT is running, credentials are correct, the Home Assistant MQTT integration is enabled, and the MQTT discovery prefix matches Home Assistant. The default discovery prefix is usually `homeassistant`.

### Dashboard loads but machine state does not update

Check the Ruida controller IP address, UDP port, network reachability from Home Assistant, controller power, and firewall rules.

### Preview image does not update

Check that `/homeassistant/www/ruida_bridge/latest.png` exists, the add-on has written a new preview, the browser is not showing a cached image, and `/local/ruida_bridge/latest.png` is reachable from Home Assistant.

## Beta testing checklist

Before reporting a bug, capture the Ruida Bridge version, Home Assistant Core version, Supervisor version, Ruida controller model, relevant add-on log lines, dashboard screenshot if UI-related, MQTT result payload if command-related, and RD file if preview/render-related.
