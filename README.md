# Ruida Bridge

Home Assistant add-on for connecting a Ruida laser controller to Home Assistant with MQTT discovery, machine status, jog controls, rotary controls, saved file listing, and RD preview rendering.

> [!WARNING]
> Ruida Bridge can send real movement commands to a physical laser controller.  
> Use it only on a trusted local Home Assistant system. Do **not** expose the add-on, MQTT broker, or Ingress UI to the public internet.

---

## Features

- Home Assistant Ingress web dashboard
- MQTT discovery for Home Assistant entities
- Machine status and X/Y/Z position reporting
- XY jog controls
- Z jog controls
- Rotary enable and rotary diameter controls
- Laser enable status display
- Saved controller file list
- Controller file download support
- RD file preview rendering
- Preview modes:
  - **EXTENTS**
  - **BED VIEW**
<img width="1839" height="917" alt="image" src="https://github.com/user-attachments/assets/22d009bf-7d4f-41aa-9195-8fa0e57b48bd" />

---

## Requirements

Before installing, make sure you have:

- Home Assistant OS or another Supervisor-based Home Assistant install
- MQTT broker available to Home Assistant
- MQTT integration enabled in Home Assistant
- MQTT discovery enabled
- Ruida controller connected to the same network
- Ruida controller reachable from Home Assistant
- Ruida controller UDP port `50200` available
- Your machine X/Y travel limits in millimeters

---

## Repository Layout

This repository is structured as a Home Assistant add-on repository.

```text
ruida_bridge/
├── repository.yaml
├── README.md
├── LICENSE
└── ruida_bridge/
    ├── app.py
    ├── CHANGELOG.md
    ├── config.yaml
    ├── Dockerfile
    ├── DOCS.md
    ├── icon.png
    ├── logo.png
    ├── README.md
    ├── requirements.txt
    ├── run.sh
    ├── web.py
    ├── static/
    │   ├── app.js
    │   ├── index.html
    │   ├── ruida_bridge_icon.png
    │   └── style.css
    └── translations/
        └── en.yaml
```

---

## Installation Option A: Add This Repository to Home Assistant

In Home Assistant, go to:

```text
Settings → Add-ons → Add-on Store
```

Then:

1. Open the three-dot menu in the upper-right corner.
2. Select **Repositories**.
3. Paste this repository URL:

   ```text
   https://github.com/MrkyWtrs/ruida_bridge
   ```

4. Select **Add**.
5. Close the repositories dialog.
6. Reload the Add-on Store if needed.
7. Find **Ruida Bridge** under available add-ons.
8. Open **Ruida Bridge**.
9. Select **Install**.

Do not start it until configuration is complete.

---

## Installation Option B: Manual Local Add-on Install

Download or clone this repository.

Copy the full add-on folder:

```text
ruida_bridge/
```

into your Home Assistant local add-ons directory:

```text
/addons/ruida_bridge
```

For example, using the Home Assistant terminal:

```bash
cp -a /path/to/ruida_bridge /addons/ruida_bridge
```

Or copy it through Samba/SMB into the `addons` share.

Then reload local add-ons:

```text
Settings → Add-ons → Add-on Store → ⋮ → Reload
```

Open **Ruida Bridge** and select **Install**.

---

## Configuration

Open the **Configuration** tab before starting the add-on.

At minimum, configure these values:

```yaml
mqtt_host: core-mosquitto
mqtt_port: 1883
mqtt_user: ""
mqtt_pass: ""
mqtt_topic_prefix: ruida
mqtt_client_id: ruida-ha-bridge
ha_discovery_prefix: homeassistant

ruida_ip: 0.0.0.0
ruida_port: 50200
ruida_local_port: 50201

ruida_max_x_mm: 0
ruida_max_y_mm: 0
ruida_z_button_step_mm: 1
```

Update these for your machine:

| Option | Description |
|---|---|
| `mqtt_host` | MQTT broker hostname or IP address |
| `mqtt_user` | MQTT username, if required |
| `mqtt_pass` | MQTT password, if required |
| `ruida_ip` | IP address of the Ruida controller |
| `ruida_port` | Ruida UDP port, usually `50200` |
| `ruida_max_x_mm` | Maximum X travel in millimeters |
| `ruida_max_y_mm` | Maximum Y travel in millimeters |
| `ruida_z_button_step_mm` | Z jog distance per button press |

> [!IMPORTANT]
> The add-on intentionally ships with:
>
> ```yaml
> ruida_ip: 0.0.0.0
> ruida_max_x_mm: 0
> ruida_max_y_mm: 0
> ```
>
> This prevents movement commands from being used until the controller IP and machine travel limits are configured.

---

## First Start

After saving your configuration:

1. Start the add-on.
2. Open the **Log** tab.
3. Confirm MQTT connects successfully.
4. Confirm no setup warnings remain.
5. Open the Web UI from the add-on page.
6. Confirm machine status updates.
7. Confirm X/Y/Z position values update.
8. Test only small jog movements first.

---

## Verifying MQTT Discovery

After the add-on starts, Home Assistant should discover a Ruida Bridge device with entities such as:

- Machine status
- X Axis
- Y Axis
- Z Axis
- Current Location
- Jog buttons
- Rotary controls
- Laser enable status
- Preview image
- Saved file list

Exact entity IDs may vary depending on your Home Assistant entity registry history.

Default examples:

```text
sensor.ruida_status
sensor.ruida_x_axis
sensor.ruida_y_axis
sensor.ruida_z_axis
sensor.ruida_xy_location
button.ruida_home_machine
button.ruida_jog_left
button.ruida_jog_right
button.ruida_jog_up
button.ruida_jog_down
button.ruida_jog_z_up
button.ruida_jog_z_down
switch.ruida_rotary_enable
number.ruida_rotary_diameter_setpoint
image.ruida_preview_image
```

---

## Web Dashboard

The add-on includes a Home Assistant Ingress dashboard.

The dashboard provides:

- Machine status
- X/Y/Z position display
- XY jog controls
- Z jog controls
- Rotary enable and diameter controls
- Laser enable status display
- Saved controller file list
- RD file preview rendering
- Preview mode toggle:
  - **EXTENTS**
  - **BED VIEW**

Open it from the Ruida Bridge add-on page using **Open Web UI**.

---

## File and Preview Storage

Downloaded controller files and preview images are stored under:

```text
/homeassistant/www/ruida_bridge/
```

Downloaded RD files are stored in:

```text
/homeassistant/www/ruida_bridge/downloads/
```

The latest preview image is written to:

```text
/homeassistant/www/ruida_bridge/latest.png
```

Home Assistant can access the latest preview at:

```text
/local/ruida_bridge/latest.png
```

---

## Updating

To update a local add-on install:

1. Stop the Ruida Bridge add-on.
2. Back up the current folder:

   ```bash
   cp -a /addons/ruida_bridge /addons/ruida_bridge.backup_$(date +%Y%m%d_%H%M%S)
   ```

3. Replace the files in:

   ```text
   /addons/ruida_bridge
   ```

4. Reload local add-ons from the Add-on Store.
5. Rebuild the add-on.
6. Start the add-on.
7. Check the log.
8. Hard refresh the Web UI.

---

## Troubleshooting

### Add-on does not appear

Confirm the folder exists here:

```text
/addons/ruida_bridge
```

Confirm `config.yaml` is directly inside that folder:

```text
/addons/ruida_bridge/config.yaml
```

Then reload local add-ons from:

```text
Settings → Add-ons → Add-on Store → ⋮ → Reload
```

### Add-on starts but no entities appear

Check:

- MQTT broker is running
- MQTT username/password are correct
- MQTT integration is enabled in Home Assistant
- MQTT discovery is enabled
- `ha_discovery_prefix` matches your Home Assistant MQTT discovery prefix

Default:

```yaml
ha_discovery_prefix: homeassistant
```

### Dashboard loads but machine data does not update

Check:

- Ruida controller is powered on
- Controller IP address is correct
- Home Assistant can reach the controller network
- UDP port `50200` is not blocked
- X/Y travel limits are greater than `0`

### Preview image does not update

Check that this file exists:

```text
/homeassistant/www/ruida_bridge/latest.png
```

Then try opening:

```text
/local/ruida_bridge/latest.png
```

If the file exists but the browser still shows the old image, hard refresh the dashboard.

---

## Known Limitations

- Intended for trusted local Home Assistant users
- No per-user operator lock yet
- Preview rendering is useful for placement but is not a full LightBurn-equivalent renderer
- Advanced RD geometry support is incomplete
- Circles, arcs, curves, fills, scan/hatch data, and compound shapes may not always render accurately
- Controller behavior may vary by Ruida model and firmware
- File upload/send-to-controller workflow is experimental

---

## Beta Testing Notes

Before reporting a bug, capture:

- Ruida Bridge version
- Home Assistant Core version
- Supervisor version
- Ruida controller model
- Relevant add-on log lines
- Dashboard screenshot, if UI-related
- MQTT result payload, if command-related
- RD file, if preview/render-related

---

## License

MIT License
