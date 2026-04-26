# PTZ Camera Controller — Modern Edition

A professional desktop application for controlling multiple PTZ (Pan-Tilt-Zoom) cameras
simultaneously using the VISCA over IP protocol. Features a modern dark-themed interface
with live video preview for up to 8 cameras.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.12%2B-green)
![Windows](https://img.shields.io/badge/platform-windows-0078D4?logo=windows)
![Linux](https://img.shields.io/badge/platform-linux-FCC624?logo=linux&logoColor=black)

---

## 📁 Repository Structure

```
PTZController/
├── windows/
│   ├── PTZController.py   ← Windows version
│   └── PTZController.ico  ← Application icon
├── linux/
│   ├── PTZController.py   ← Linux version
│   ├── install.sh         ← One-command installer
│   └── uninstall.sh       ← One-command uninstaller
├── LICENSE
└── README.md
```

---

## 🎯 Features

- Control up to **8 PTZ cameras** simultaneously via VISCA over IP
- Live **RTSP video streams** — 2×4 grid layout (465×430 px per cell)
- **Pan / Tilt / Zoom** with keyboard shortcuts
- Variable **movement speed** slider (1–24)
- Instant **camera switching** with F1–F8
- Modern **dark theme** UI
- Active camera highlighted with a **green border**
- Multi-threaded video capture — each camera runs independently
- Forced **TCP mode** for reliable RTSP connections

---

## 🚀 Installation

### Windows

**Option 1 — Run from source**
1. Install Python 3.12 or higher
2. Install dependencies:
```bash
pip install keyboard visca-over-ip opencv-python pillow
```
3. Run:
```bash
cd windows
python PTZController.py
```

**Option 2 — Build a standalone executable**
```bash
pip install pyinstaller
cd windows
pyinstaller --onefile --windowed --icon=PTZController.ico PTZController.py
```
The `.exe` will be created in the `dist/` folder.

---

### Linux (Ubuntu 22.04 LTS or newer)

One-command install — handles all dependencies and registers the app in your application menu:

```bash
cd linux
chmod +x install.sh
./install.sh
```

After installation, launch from:
- **Application menu** → search "PTZ Camera Controller"
- **Terminal** → `ptzcontroller`

To uninstall:
```bash
./uninstall.sh
```

> **Wayland note:** Keyboard shortcuts require the app window to be in focus.
> If running a pure Wayland session, log in with **Ubuntu on Xorg** for best compatibility.

---

## ⚙️ First-Time Setup

1. Launch the application
2. Go to **Settings → Configure Cameras**
3. For each camera, fill in:
   - **IP Address** — used for VISCA PTZ control (e.g. `192.168.1.101`)
   - **RTSP URL** — full stream URL (e.g. `rtsp://admin:pass@192.168.1.101:554/stream1`)
4. Click **⚡ CONNECT & START**

### Camera Configuration Example

```
Camera 1 (F1):
  IP Address: 192.168.1.101
  RTSP URL:   rtsp://admin:admin123@192.168.1.101:554/stream1

Camera 2 (F2):
  IP Address: 192.168.1.102
  RTSP URL:   rtsp://admin:admin123@192.168.1.102:554/stream1
```

### Common RTSP URL Formats

| Camera Brand | URL Format |
|---|---|
| Generic | `rtsp://user:pass@ip:554/stream` |
| Sony | `rtsp://admin:pass@ip:554/image` |
| PTZOptics | `rtsp://admin:admin@ip:554/stream1` |
| ONVIF | `rtsp://user:pass@ip:554/onvif1` |

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `↑` `↓` `←` `→` | Pan / Tilt |
| `+` or `=` | Zoom In |
| `-` | Zoom Out |
| `F1` – `F8` | Switch active camera |
| Speed slider | Adjust movement speed (1–24) |

---

## 📋 Requirements

### Camera requirements
- VISCA over IP support (default port: **52381**, some cameras use **1259**)
- RTSP streaming capability (default port: **554**)
- Compatible with Sony, Canon, PTZOptics, and other VISCA-capable cameras

### Port reference

| Protocol | Default port |
|---|---|
| VISCA control | 52381 (or 1259) |
| RTSP streaming | 554 |
| Camera web UI | 80 / 443 |
| ONVIF | 2000 |

### Platform differences

| | Windows | Linux |
|---|---|---|
| Python | 3.12+ | 3.12+ (installer uses 3.13) |
| Keyboard hooks | Global (works unfocused) | App-window focus required |
| Installation | `pip install` | `./install.sh` |
| App icon | `.ico` | PNG (auto-generated) |

---

## 🔧 Technical Details

### Architecture
```
PTZController
├── Main UI Thread (Tkinter)
├── Video Capture Threads (8 independent daemon threads)
├── Keyboard Input (keyboard lib on Windows · tkinter bind_all on Linux)
└── VISCA Control (visca_over_ip)
```

### Video pipeline
- Capture: OpenCV with FFMPEG backend, RTSP over TCP
- Buffer: 2 frames (minimal latency)
- Render: ~33 FPS (30 ms update cycle)
- Scaling: dynamic, aspect-ratio preserved

### VISCA commands used
- `pantilt(pan_speed, tilt_speed)` — speed range 1–24
- `zoom(speed)` — speed range -4 to +4 (0 = stop)

---

## 🐛 Troubleshooting

**Video not showing**
- Test the RTSP URL in VLC: Media → Open Network Stream
- Verify camera streaming is enabled
- Check network connectivity

**PTZ not responding**
- Confirm the IP address and VISCA port (52381 or 1259)
- Verify the camera supports VISCA over IP
- Check that no firewall is blocking UDP to the camera

**Keyboard shortcuts not working (Linux)**
- Click the app window to make sure it has focus
- If on Wayland, switch to an Xorg session from the login screen

**Application won't start (Windows)**
- Run as Administrator if keyboard hooks fail
- Reinstall dependencies: `pip install keyboard visca-over-ip opencv-python pillow`

**Application won't start (Linux)**
- Re-run `./install.sh` to repair the installation
- Check Python is available: `python3 --version`

---

## 🔒 Security Notes

- RTSP credentials are held in memory only — never written to disk
- Reconfigure each session as needed
- Use a dedicated camera VLAN or VPN for remote access
- Change default camera passwords before deployment

---

## 📚 Advanced Usage

### Custom VISCA commands
```python
self.active_cam._send_command('command_hex_string')
```

### Preset positions
```python
self.active_cam.preset_save(preset_number)    # save current position
self.active_cam.preset_recall(preset_number)  # move to saved position
```

### Other available VISCA methods
- `set_power(True/False)` — power on/off
- `info_display(True/False)` — toggle OSD

---

## 🔄 Version History

**v2.0** — Modern Edition
- Complete UI overhaul with dark theme
- 8-camera support with 2×4 grid
- Linux support with one-command installer
- Speed control slider
- Zoom controls (+/- keys)
- Full-screen launch
- Fixed-size containers for stable layout

**v1.0** — Original Release
- Basic 4-camera control
- Simple UI
- Pan/tilt/zoom functionality

---

## 📄 License

This application is provided as-is for camera control and monitoring purposes.

---

**Made with ❤️ for professional camera operators**
