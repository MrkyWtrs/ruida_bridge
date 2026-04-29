# Ruida Bridge

Home Assistant add-on for connecting a Ruida laser controller to Home Assistant using MQTT.

Ruida Bridge gives you a mobile-friendly Home Assistant dashboard for monitoring and controlling your Ruida laser from your phone, tablet, or desktop. See the features list below.

> [!WARNING]
> Ruida Bridge can send real movement and job commands to a physical laser controller.
> 
> Use it only on a trusted local Home Assistant system. Do not expose the add-on, MQTT broker, or Ingress UI to the public internet.
>
> Ruida Bridge has only been tested on an RDC6442S-B(EC) controller.

> [!NOTE]
Other Ruida models may work.
>
> If you test another model successfully, please let us know so it can be added to the supported controller list.
<img width="1815" height="908" alt="Ruida Bridge dashboard" src="https://github.com/user-attachments/assets/7ece9bef-f57d-4a74-8ef0-ee4a031b51d7" />

## What it does

Ruida Bridge provides a local Home Assistant dashboard for basic Ruida laser controller interaction.

Current features include:

- Home Assistant add-on packaging with Ingress support
- Mobile-friendly dashboard for phone, tablet, and desktop control
- MQTT connection to Home Assistant / Mosquitto
- MQTT discovery for Ruida Bridge entities
- Machine online/offline status
- Machine status readout
- Current X, Y, and Z position display
- XY jog controls
- Z up, Z down, and Z home controls
- XY home control
- Move-to-position controls for X, Y, and Z
- Laser enable state display
- Machine settings display
- Rotary enable and diameter controls
- Saved controller file list
- Refresh / get files controls
- Run selected file command
- Stop job command
- RD preview rendering to a Home Assistant-accessible image path

## Project status

This project is actively being developed and tested against a real Ruida controller.

It is currently intended for local Home Assistant use by people who understand the risks of sending motion and job commands to laser hardware.

Expect ongoing changes as the add-on is refined.

## Requirements

- Home Assistant with Supervisor
- MQTT broker, such as the Mosquitto add-on
- Ruida laser controller reachable on the local network
- Local network access between Home Assistant and the Ruida controller

## Installation

1. Copy the `ruida_bridge` add-on folder into your Home Assistant add-ons directory.
2. Reload local add-ons in Home Assistant.
3. Install the **Ruida Bridge** add-on.
4. Configure the add-on options.
5. Start the add-on.
6. Open the Ruida Bridge Ingress page.

## Required configuration

At minimum, configure:

- MQTT host
- MQTT username
- MQTT password
- Ruida controller IP address


Example values:

```yaml
mqtt_host: core-mosquitto
mqtt_user: mqtt-user
mqtt_pass: your-password
ruida_ip: 192.168.1.11

