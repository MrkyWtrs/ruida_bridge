## 0.8.4

- Added root-level `icon.png` and `logo.png` so Supervisor recognizes Ruida Bridge add-on artwork.
- Confirmed Supervisor reports `icon: true` and `logo: true`.
- Confirmed the add-on icon endpoint returns the package PNG.
- Left `panel_icon: mdi:bridge` in config.yaml, but Home Assistant still does not expose `panel_icon` through installed local add-on metadata.
- Kept backend and frontend behavior unchanged from 0.8.3.

## 0.8.3

- Marked the current dashboard work as the 0.8.3 UI Preview Checkpoint.
- Replaced the lower-left placeholder card with:
  - Laser 1 Enable and Laser 2 Enable read-only status switches.
  - A scrollable Machine Settings list for passively used controller settings.
- Added themed scrollbars for dashboard scrollable areas.
- Added Preview mode switching:
  - EXTENTS keeps the zoomed design preview.
  - BED VIEW renders the design on the full workbed.
- Updated preview rulers:
  - EXTENTS now shows the design's actual bed-coordinate range.
  - BED VIEW shows the full X/Y travel range.
- Updated bed preview rendering to use the configured bed aspect ratio.
- Added a visible bed boundary rectangle in BED VIEW.
- Moved preview dimensions next to the file name.
- Tuned the XY pad scale and position inside the existing jog block.
- Kept backend Ruida command behavior unchanged from the 0.8.2 baseline.

## 0.8.2

- Marked the Machine Info card polish as the 0.8.2 checkpoint.
- Changed the Machine section label to Status.
- Added grouped X/Y/Z position spans so coordinate spacing is controlled by CSS.
- Reworked the Rotary/Diameter area into a shared label row above the controls.
- Matched ON/OFF, diameter value, and SET button typography.
- Kept the rotary switch in the blue/gray theme instead of green when enabled.
- Consolidated iterative Machine Info CSS patches into one final checkpoint block.
- Kept backend Ruida command behavior unchanged from the 0.8.1 baseline.

## 0.8.1

- Marked the current dashboard layout as the 0.8.1 UI Layout Checkpoint.
- Restored the layout with Machine Info and placeholder swapped so Machine Info sits under the jog controls.
- Moved file controls into the Files card:
  - Get Files and Refresh are side-by-side.
  - Preview File Path is below the buttons.
  - Removed the separate Actions box/title.
- Changed Preview File Path from a single-line input to a compact multiline textarea.
- Removed the top-right dashboard Refresh button and guarded the frontend code so the missing button does not break UI updates.
- Tuned desktop column sizing and row alignment so the lowest boxes align cleanly across columns.
- Adjusted the middle column split so the jog box is shorter and Machine Info takes the remaining vertical space.
- Kept backend Ruida command behavior unchanged from the 0.8.0 baseline.

## 0.8.0

- Marked the current web dashboard work as the 0.8.0 checkpoint.
- Added rotary controls directly to the Machine Info card:
  - Rotary enable/disable switch.
  - Rotary diameter number input.
  - Set button for writing rotary diameter.
- Added rotary UI state feedback:
  - Diameter input and Set button are disabled when rotary is OFF.
  - Set button turns green when the input matches the machine-read diameter.
  - Set button turns yellow when the input differs from the machine-read diameter.
  - Rotary diameter input uses two-decimal display and 0.01 mm steps.
- Polished Machine Info layout:
  - Increased Machine state font size.
  - Cleaned up nested divider lines after adding rotary controls.
  - Right-aligned rotary diameter input text.
  - Removed number input spinner arrows.
- Added dismiss support for the setup warning:
  - Users can preview the UI without configuring a laser.
  - Safety lock remains active until setup is actually complete.
- Changed Preview File Path behavior:
  - Startup no longer auto-fills the preview path from the first file.
  - Clicking a file still fills the path and renders/downloads as before.
- Confirmed preview line width is controlled by the add-on Configuration option `preview_line_width`.
- Preserved backend Ruida command behavior from 0.7.7.
- Removed stale version suffix from the default MQTT client ID.
- Changed fresh-install X/Y travel defaults to `0` so users must enter real machine limits.
- Updated setup validation so zero or non-positive travel limits are treated as incomplete configuration.
- Updated README example configuration to match the safer fresh-install defaults.

## 0.7.7

- Added first-run/setup warning support in the web UI.
- Default Ruida controller IP changed to `0.0.0.0` so new installs clearly require configuration.
- Added backend guard to prevent UDP polling/commands when the controller IP is not configured.
- Setup warning now lists missing configuration items and disables dashboard controls until setup is complete.
- Fixed top status badge so unconfigured JSON status displays as `Needs setup` instead of raw JSON.
- Cleared stale retained machine attributes when the bridge is not configured.
- File list now merges controller files with local `.rd`, `.lbrn`, and `.lbrn2` files in the downloads folder.
- Local-only files can now be selected and rendered directly without attempting controller download.
- Controller files still download missing local copies into `/homeassistant/www/ruida_bridge/downloads/`.
- Kept version as a pre-beta working checkpoint; no beta package designation yet.

# Changelog
## 0.7.6

- Fixed large controller file downloads that stopped after block 127
- Changed controller download block requests to encode block numbers as Ruida/u35 base-128 values
- Confirmed block 128 now requests as `00 00 00 01 00` instead of the failing raw `00 00 00 00 80`
- Raised maximum controller download block limit from 256 to 1024
- Confirmed large controller files download fully
- Confirmed a large downloaded file now renders completely instead of stopping at the first partial section
- Removed temporary `probe_download_blocks` diagnostic command after confirming the fix

## 0.7.5

- Marked current work as the 0.7.5 Download/Preview Checkpoint
- Fixed controller-downloaded RD file corruption:
  - Identified extra 2-byte transfer data inserted at controller download block boundaries
  - Strips the transfer bytes from each downloaded block before saving the RD file
  - Preserves original wire payload length so full blocks do not falsely terminate downloads
  - Trims long raw 0x00 controller padding at the end of downloaded files
- Confirmed downloaded fill/scan files now render correctly after re-download
- Improved RD preview handling:
  - Keeps isolated junk cluster cleanup
  - Keeps impossible long-jump path splitting
  - Keeps scan/fill rendering improvements
  - Keeps scan-heavy parser branch for 0xAA/0x8A-heavy files
  - Keeps detected scan Y interval for row cleanup instead of assuming fixed row spacing
  - Keeps diagonal transition artifact filtering in scan/fill cleanup
- Confirmed representative fill/scan downloaded files now preview correctly after the download boundary fix
- Known limitation:
  - One remaining file still has preview/render issues and needs separate investigation

## 0.7.4
- 0.7.3 responsive UI baseline retained
- Files list internal scroll fix retained
- Controller file sync/download restored
- Get Files now runs sync_files
- File row click downloads/refetches selected controller file
- Preview File Path points to /homeassistant/www/ruida_bridge/downloads/<file>.rd
- Selected downloaded RD file renders automatically




## 0.7.3
- Marked patched 0.7.2 UI work as the 0.7.3 checkpoint
- Kept backend behavior unchanged
- Kept MQTT command flow unchanged
- Kept RD preview rendering backend unchanged
- Kept Home Assistant discovery behavior unchanged
- Frontend/UI changes:
  - Fixed full-screen Z button layout
  - Made Z buttons narrower and taller
  - Increased spacing between Z Up and Z Down
  - Restored combined Machine Info Position row
  - Shows X, Y, and Z together in one line
  - Keeps numeric position values white
  - Keeps x/y/z axis labels blue and slightly smaller than the numbers
  - Adjusted preview panel to use a 5:3 display ratio
  - Starts the UI with no preview image loaded
  - Starts with an empty Preview File Path
  - Removed the fallback “IMAGE PREVIEW SENSOR” placeholder text

Changelog
## 0.7.2

- Changed the Ingress frontend to normal responsive\/reflow layout behavior
- Kept the current three-column dashboard feel on wide desktop\/laptop windows
- Added a medium-width layout that keeps Preview\/Actions and XY\/Machine Info side-by-side, with Files below
- Added a narrow\/mobile layout that stacks cards vertically for usable scrolling
- Removed the fixed-canvas\/no-auto-window-layout experiment from this package
- Removed whole-dashboard scaling behavior from this package
- Kept normal browser zoom and pinch behavior
- Preserved backend behavior:
  - Existing MQTT command flow unchanged
  - Existing RD preview rendering flow unchanged
  - Existing Home Assistant discovery behavior unchanged

## 0.7.1

- Marked 0.7.1 as the current working baseline
- Updated the Home Assistant Ingress UI layout:
  - Moved Actions under Preview in the left column
  - Moved XY/Z jog controls to the middle column above Machine Info
  - Changed the main layout to equal-width three-column sizing
- Simplified Machine Info:
  - Kept Machine, XY, Z, and Rotary
  - Removed Paths
  - Removed Points
  - Removed Debug Result from the center column
- Cleaned up preview display:
  - Removed the checkerboard background behind PNG previews
  - Kept the preview frame background simple and transparent-friendly
- Cleaned up jog controls:
  - Removed the Z Jog label above the Z Up/Z Down buttons
  - Kept Z Up and Z Down controls in the combined jog card
- Updated frontend compatibility:
  - Kept hidden `selectedFileName` for existing `app.js` compatibility
  - Updated `app.js` so missing Debug Result markup does not break command handling
- Preserved backend behavior:
  - Existing MQTT command flow unchanged
  - Existing RD preview rendering flow unchanged
  - Existing Home Assistant discovery behavior unchanged
## 0.7.0

- Continued polishing the Home Assistant Ingress web UI layout
- Changed the frontend from a quadrant/two-column layout into a three-column layout:
  - Left column: preview image and jog controls
  - Center column: actions and machine info
  - Right column: saved controller files
- Moved Machine Info out of the preview panel and into the center column
- Moved Actions into the center column above Machine Info
- Moved Get Files into the Files card at the bottom
- Removed the visible Selected File footer from the Files card
- Renamed Use Selected to Render Image
- Changed Render Image behavior so it renders the current Preview File Path
- Removed separate Refresh Preview and Render Preview buttons
- Kept preview image refresh handled automatically by the frontend
- Fixed Preview File Path being overwritten every few seconds during file-list refreshes
- Added/kept version display next to the Ruida Bridge title
- Adjusted XY/Z jog layout:
  - Combined XY jog and Z jog into one control card
  - Enlarged jog controls
  - Left-justified the XY pad while keeping it vertically centered
- Added transparent preview image support:
  - `preview_background: "transparent"` now renders RGBA PNG output
  - Transparent previews display over a checkerboard-style UI background
- Added support for hiding preview render boxes:
  - `preview_show_bounds: false` hides the geometry bounds box
  - Optional app.py cleanup can remove the outer plot frame if desired
- Updated Preview File Path label for clarity
- Moved debug/result output into the bottom of the Machine Info card
- Preserved existing backend MQTT command flow:
  - UI controls still publish through the existing command topic
  - Get Files still uses `file_list`
  - Render Image still uses `render_rd`
0.6.0
Added first-pass Home Assistant Ingress web frontend:
- Enables Open Web UI from the Ruida Bridge app page
- Adds Flask-based web server on port 8099
- Adds static frontend files under /static
- Adds large RD preview panel
- Adds jog controls for Home, Left, Right, Up, Down, Z Up, and Z Down
- Adds Get Files and Render buttons
- Adds live status readout using existing MQTT topics
- Sends all UI control actions through the existing MQTT command topic
- Keeps app.py backend logic unchanged from the 0.5.2 baseline

0.5.2
Fixed RD preview parsing for dense fill/scanline files
Added command-by-command parsing for Ruida motion/cut records:
0x88 move absolute
0x89 move relative
0x8A move horizontal
0x8B move vertical
0xA8 cut absolute
0xA9 cut relative
0xAA cut horizontal
0xAB cut vertical
Stopped interpreting parameter bytes inside fill data as fake 0x88/0xA8 commands
Greatly improves preview accuracy for engraved/fill-style RD files
0.5.1
Improved RD preview image rendering:
- Removed automatic fake path closing so the renderer no longer invents lines that are not in the parsed RD data
- Increased preview output to 1200x900
- Added anti-aliased rendering by drawing oversized and downsampling
- Added configurable preview fit mode:
  - geometry
  - bed
- Added optional preview grid
- Added optional parsed point markers
- Added optional geometry bounds box
- Added optional footer label with file name, size, path count, and fit mode
- Added configurable preview line width
- Added configurable preview foreground/background colors
- Added preview render settings to preview metadata
- Republishes the retained MQTT preview image on reconnect if latest.png exists
Updated Home Assistant app packaging:
- Bumped config.yaml version to 0.5.1
- Added preview rendering options to config.yaml
- Added preview rendering options to run.sh exports
- Added translation labels for new preview options

0.5.0
Added configurable Home Assistant identity options:
device_id
device_name
entity_prefix
Updated app startup to read device identity from environment variables
Updated MQTT discovery device name to use configured device_name
Updated MQTT discovery unique IDs and default entity IDs to use configured entity_prefix
Improved portability for other Home Assistant instances and multi-device installs
Maintained existing entity names when using default values:
device_id: ruida_bridge
device_name: Ruida Bridge
entity_prefix: ruida
0.4.5
Added grouped laser status entities:
binary_sensor.ruida_laser_1_enabled
binary_sensor.ruida_laser_2_enabled
Moved laser settings into attributes:
frequency
minimum power
maximum power
raw enable value
Removed individual laser setting sensors (frequency/min/max)
Moved controller IP and bridge status into sensor.ruida_status attributes
Corrected laser enable bitmask (0x4000 → 0x2000)
Fixed RD preview rendering:
added support for 0x88, 0xA8, 0xA9 records
separated paths to prevent cross-shape connections
Changed preview image naming:
filename.rd → filename.png (no more timestamp buildup)
Added automatic file list refresh on startup
0.4.2
Fixed Rotary Enable MQTT switch command template
Changed boolean output from Python-style True / False to valid JSON true / false
Confirmed switch.ruida_rotary_enable publishes valid set_rotary_enabled commands
Maintains 0.4.1 rotary switch behavior as baseline
0.4.0
Added Home Assistant preview image (/config/www/ruida_bridge/latest.png)
Added unique timestamped archive PNGs
Added MQTT preview image topic and camera discovery
Linked preview image to Ruida device in HA
Cleaned up temporary debug logging
0.3.1
Removed temporary debug logging from preview troubleshooting
Standardized RD file path handling (/addon_configs/... → /config/...)
Kept preview output under /config/images
Switched to timestamped PNG archive files
Added image_file to render_rd result payload
Maintained MediumBlue + white preview styling
Added map: addon_config for shared file access
0.3.0
Added RD file preview rendering
Added MQTT render_rd command for .rd files
Added preview metadata on ruida/bridge/preview
Implemented initial RD geometry parsing (A8-based)
Updated preview styling (MediumBlue + white geometry)
Removed footer text from preview images
0.2.0
Added saved file list retrieval from controller
Decoded runtime into runtime_ms and runtime_text
Published file list over MQTT
Added Home Assistant “Get File List” button
Added MQTT discovery sensor with file list attributes
0.1.1
Fixed Home Assistant app startup (init: false)
Fixed environment handling in run.sh
Fixed Docker build compatibility
Retained XY jog controls (Home, Left, Right, Up, Down)
Added Z jog buttons
Added MQTT JSON rel_xy support
Added MQTT JSON abs_xy support
Added XY bounds checking with result feedback
0.1.0
Initial development build
Implemented Ruida MQTT bridge backend
Added XY and Z movement support
Added Home Assistant MQTT discovery
