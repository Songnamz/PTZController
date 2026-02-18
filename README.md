# PTZ Camera Controller — Modern Edition

A professional desktop application for controlling multiple PTZ (Pan-Tilt-Zoom) cameras simultaneously using the VISCA over IP protocol. Features a modern dark-themed interface with live video preview from up to 8 cameras.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.12-green)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey)

## 🎯 Features

### Camera Control
- **Multi-Camera Support**: Control up to 8 PTZ cameras simultaneously
- **VISCA over IP Protocol**: Industry-standard camera control protocol
- **Real-time Control**: Pan, tilt, and zoom with keyboard shortcuts
- **Variable Speed**: Adjustable movement speed (1-24) via slider
- **Quick Switching**: Instantly switch between cameras using F1-F8 keys

### Video Display
- **Live Streaming**: RTSP video streams with automatic aspect ratio preservation
- **8-Camera Grid**: 2x4 grid layout optimized for 1920x1080 displays
- **Fixed Containers**: 465x430 pixel containers prevent layout shifting
- **Dynamic Scaling**: Automatic video scaling while maintaining aspect ratio
- **Active Camera Indicator**: Green border highlights currently controlled camera

### User Interface
- **Modern Dark Theme**: Professional color scheme with accent colors
- **Full Screen Launch**: Automatically maximizes on startup
- **Custom Icon**: Branded application icon in all sizes
- **Responsive Layout**: Resizable window with stable grid
- **Status Indicators**: Real-time connection and control status

### Advanced Features
- **Tracking Mode UI**: Interface for camera tracking features (requires web interface for most cameras)
- **Configuration Dialog**: Separate window for camera setup
- **Keyboard Hotkeys**: Global keyboard hooks for seamless control
- **Multi-threaded Video**: Independent capture threads for each camera
- **TCP Streaming**: Forced TCP mode for reliable RTSP connections

## 📋 Requirements

### Python Dependencies
```
tkinter (included with Python)
keyboard>=0.13.5
visca-over-ip>=0.5.1
opencv-python>=4.8.0
Pillow>=10.0.0
```

### System Requirements
- **OS**: Windows 10/11
- **Python**: 3.12 or higher
- **Display**: 1920x1080 recommended (1880x980 minimum)
- **Network**: Stable connection to PTZ cameras

### Camera Requirements
- VISCA over IP support (default port: 52381)
- RTSP streaming capability (default port: 554)
- Compatible with Sony, Canon, PTZOptics, and other VISCA cameras

## 🚀 Installation

### Option 1: Run Pre-built Executable (Recommended)
1. Download `PTZController.exe` from the `dist` folder
2. Ensure `PTZController.ico` is in the same directory (optional)
3. Double-click to run

### Option 2: Run from Source
1. Install Python 3.12 or higher
2. Install dependencies:
```bash
pip install keyboard visca-over-ip opencv-python pillow
```
3. Run the application:
```bash
python PTZController.py
```

### Option 3: Build Your Own Executable
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=PTZController.ico PTZController.py
```
The executable will be created in the `dist` folder.

## ⚙️ Configuration

### First-Time Setup
1. Launch the application
2. Go to **Settings → Configure Cameras**
3. For each camera you want to control:
   - **IP Address**: Camera's IP address for VISCA control (e.g., `192.168.1.100`)
   - **RTSP URL**: Full RTSP stream URL (e.g., `rtsp://admin:password@192.168.1.100:554/stream1`)
4. Click **⚡ CONNECT & START**

### Camera Configuration Example
```
Camera 1 (F1):
  IP Address: 192.168.1.101
  RTSP URL: rtsp://admin:admin123@192.168.1.101:554/stream1

Camera 2 (F2):
  IP Address: 192.168.1.102
  RTSP URL: rtsp://admin:admin123@192.168.1.102:554/stream1
```

### Common RTSP URL Formats
- Generic: `rtsp://username:password@ip:port/stream`
- Sony: `rtsp://admin:password@ip:554/image`
- PTZOptics: `rtsp://admin:admin@ip:554/stream1`
- ONVIF: `rtsp://username:password@ip:554/onvif1`

### Port Information
Most PTZ cameras use these standard ports:
- **VISCA Control**: Port 52381 (or 1259)
- **RTSP Streaming**: Port 554
- **Web Interface**: Port 80
- **HTTPS**: Port 443
- **ONVIF**: Port 2000

## 🎮 Controls

### Movement Controls
| Key | Action |
|-----|--------|
| `↑` | Tilt Up |
| `↓` | Tilt Down |
| `←` | Pan Left |
| `→` | Pan Right |
| `+` or `=` | Zoom In |
| `-` | Zoom Out |

### Camera Selection
| Key | Camera |
|-----|--------|
| `F1` | Control Camera 1 |
| `F2` | Control Camera 2 |
| `F3` | Control Camera 3 |
| `F4` | Control Camera 4 |
| `F5` | Control Camera 5 |
| `F6` | Control Camera 6 |
| `F7` | Control Camera 7 |
| `F8` | Control Camera 8 |

### Speed Control
- Use the **Movement Speed Slider** in the top panel to adjust speed (1-24)
- Higher values = faster movement
- Recommended: 6-12 for smooth control, 18-24 for quick positioning

### Menu Options
- **Settings → Configure Cameras**: Open configuration dialog
- **Settings → Exit**: Close application
- **Help → Controls**: Show keyboard shortcuts

## 🔧 Technical Details

### Architecture
```
PTZController
├── Main UI Thread (Tkinter)
├── Video Capture Threads (8 independent threads)
├── Global Keyboard Hook (keyboard library)
└── VISCA Control (visca_over_ip)
```

### Color Scheme
- **Background Dark**: #1a1a2e
- **Background Medium**: #16213e
- **Background Light**: #0f3460
- **Accent**: #e94560
- **Success**: #00d9a3
- **Warning**: #ffa500

### Video Processing
- **Capture Method**: OpenCV with FFMPEG backend
- **Protocol**: RTSP over TCP (forced)
- **Buffer Size**: 2 frames (minimal latency)
- **Update Rate**: 30ms (~33 FPS)
- **Scaling**: Dynamic with aspect ratio preservation

### VISCA Commands
- **Pan/Tilt**: `pantilt(pan_speed, tilt_speed)`
- **Zoom**: `zoom(speed)` where speed is -4 to +4
- **Speed Range**: 1-24 (VISCA standard)

## 🐛 Troubleshooting

### Video Not Showing
- Verify RTSP URL is correct
- Test stream in VLC: `Media → Open Network Stream`
- Check camera streaming is enabled
- Ensure network connectivity to camera
- Try reducing buffer size or changing ports

### Camera Not Responding to Controls
- Verify IP address is correct
- Check VISCA port (usually 52381, some cameras use 1259)
- Confirm camera supports VISCA over IP
- Test with camera's web interface
- Verify firewall isn't blocking UDP traffic

### Wrong Camera Responding
- Check that only one camera is on each IP address
- Verify camera IP configuration
- Press correct F-key (F1-F8) to switch cameras
- Look for green border indicating active camera

### Tracking Not Working
Most cameras don't expose tracking through VISCA protocol. To use tracking:
1. Open camera's web interface (`http://camera_ip`)
2. Navigate to tracking settings (usually under Setup → PTZ)
3. Enable and configure tracking there
4. Or consult your camera's manual for tracking commands

### Application Won't Start
- Install all required dependencies: `pip install keyboard visca-over-ip opencv-python pillow`
- Ensure Python 3.12+ is installed
- Run as administrator if keyboard hooks fail
- Check Windows permissions for network access

### Performance Issues
- Reduce number of active cameras
- Use lower resolution RTSP streams
- Close other network-intensive applications
- Upgrade network infrastructure
- Use wired ethernet instead of WiFi

## 📚 Advanced Usage

### Custom VISCA Commands
The application uses the `visca_over_ip` library. You can extend functionality by accessing:
```python
self.active_cam._send_command('command_hex_string')
```

### Preset Positions
To add preset positions, implement:
```python
# Save preset
self.active_cam.preset_save(preset_number)

# Recall preset
self.active_cam.preset_recall(preset_number)
```

### Additional Camera Settings
Available methods from visca_over_ip:
- `set_power(True/False)` - Power on/off
- `info_display(True/False)` - Toggle OSD
- `preset_save(num)` - Save preset position
- `preset_recall(num)` - Recall preset position

## 📝 Notes

- **Global Hotkeys**: The application uses global keyboard hooks, so controls work even when the window is not in focus
- **Multi-Camera Control**: Only one camera can be controlled at a time, but all cameras stream video simultaneously
- **Network Performance**: Each RTSP stream consumes bandwidth; ensure adequate network capacity
- **Camera Compatibility**: Tested with VISCA-compatible PTZ cameras; some features may vary by manufacturer

## 🔒 Security Considerations

- RTSP credentials are stored in memory during runtime
- No credential persistence (configure each session)
- Use secure network or VPN for remote access
- Change default camera passwords
- Implement network segmentation for camera VLAN

## 📄 License

This application is provided as-is for camera control and monitoring purposes.

## 🤝 Support

For issues or questions:
1. Check camera's VISCA documentation
2. Verify network connectivity
3. Test RTSP streams independently (VLC)
4. Consult camera manufacturer's support

## 🔄 Version History

**v2.0** - Modern Edition
- Complete UI overhaul with dark theme
- 8-camera support with 2x4 grid
- Fixed-size containers for stable layout
- Speed control slider
- Zoom controls (+/- keys)
- Full screen launch
- Custom application icon
- Tracking mode UI (web interface required)
- Improved video scaling

**v1.0** - Original Release
- Basic 4-camera control
- Simple UI
- Pan/tilt/zoom functionality

---

**Made with ❤️ for professional camera operators**
