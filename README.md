# Ruida Bridge

Ruida Bridge is a Home Assistant App/add-on for connecting a Ruida laser controller to Home Assistant using MQTT discovery and a local web dashboard.

It exposes machine status, X/Y/Z position, jog controls, rotary controls, saved controller files, RD file downloads, and RD preview rendering directly inside Home Assistant.

> [!WARNING]
> Ruida Bridge can send real movement commands to a physical laser controller.
>
> Use it only on a trusted local Home Assistant system. Do not expose the add-on, MQTT broker, or Ingress UI to the public internet.
>
> Keep a hand near the emergency stop while testing movement commands.

---

<img width="1809" height="892" alt="image" src="https://github.com/user-attachments/assets/9b46a638-471b-4ccc-bd58-8bcf54e0dd75" />

---

## Current version

**0.9.0 Continuous Jog Checkpoint**

This release adds press-and-hold continuous jog support for the dashboard XY and Z controls.

---

## Features

- Home Assistant App/add-on packaging
- Home Assistant Ingress web dashboard
- MQTT discovery for Home Assistant entities
- Machine status polling
- X, Y, and Z position reporting
- XY jog controls
- Z jog controls
- Press-and-hold continuous jog from the dashboard
- Guarded absolute XY movement
- Guarded Go To Z movement
- Rotary enable/disable control
- Rotary diameter read/write support
- Saved file list from the Ruida controller
- Controller file download support
- Local RD, LBRN, and LBRN2 file listing
- RD preview rendering
- Preview image publishing through MQTT
- Bed-view and geometry-view preview modes
- Laser 1 and Laser 2 enable-state reporting
- Machine setting attributes for useful controller values

---




```text
docs/screenshots/dashboard.png
docs/screenshots/home-assistant-device.png
