import tkinter as tk
from tkinter import messagebox, ttk, Toplevel
import keyboard
from visca_over_ip import Camera
import cv2
from PIL import Image, ImageTk
import threading
import time

class PTZApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PTZ Camera Controller — Modern Edition")
        self.root.geometry("1880x980")
        self.root.resizable(True, True)  # Allow maximize and resize
        
        # Launch in full screen mode
        self.root.state('zoomed')  # Maximized window on Windows
        
        # Set application icon
        try:
            self.root.iconbitmap('PTZController.ico')
        except:
            pass  # Icon file not found, continue without it
        
        # Modern color scheme
        self.colors = {
            'bg_dark': '#1a1a2e',
            'bg_medium': '#16213e',
            'bg_light': '#0f3460',
            'accent': '#e94560',
            'accent_hover': '#c93350',
            'text_primary': '#ffffff',
            'text_secondary': '#b8b8b8',
            'success': '#00d9a3',
            'warning': '#ffa500',
            'border': '#2d2d44'
        }
        
        self.root.configure(bg="#000000")

        self.cameras = {}
        self.video_caps = {}
        self.video_frames = {}
        self.video_labels = {}
        self.camera_name_labels = {}
        self.active_cam = None
        self.active_name = ""

        self.pressed_keys = set()
        self.move_speed = 6
        self.running = False
        self.config_window = None

        # Store camera configuration values
        self.camera_configs = [
            {'ip': '', 'rtsp': ''},
            {'ip': '', 'rtsp': ''},
            {'ip': '', 'rtsp': ''},
            {'ip': '', 'rtsp': ''},
            {'ip': '', 'rtsp': ''},
            {'ip': '', 'rtsp': ''},
            {'ip': '', 'rtsp': ''},
            {'ip': '', 'rtsp': ''}
        ]

        # ================= UI =================
        # Menu bar
        menubar = tk.Menu(root, bg=self.colors['bg_medium'], fg=self.colors['text_primary'])
        root.config(menu=menubar)
        
        config_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_medium'], fg=self.colors['text_primary'])
        menubar.add_cascade(label="Settings", menu=config_menu)
        config_menu.add_command(label="Configure Cameras...", command=self.open_config_window)
        config_menu.add_separator()
        config_menu.add_command(label="Exit", command=root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['bg_medium'], fg=self.colors['text_primary'])
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Controls", command=self.show_controls_help)
        
        # Top control panel
        top_frame = tk.Frame(root, bg=self.colors['bg_medium'], relief=tk.FLAT)
        top_frame.pack(side="top", fill="x", padx=5, pady=5)

        # Header
        header_frame = tk.Frame(top_frame, bg=self.colors['bg_medium'])
        header_frame.pack(pady=(8, 5))
        
        tk.Label(header_frame, 
                text="🎥 PTZ Camera Controller",
                font=('Segoe UI', 14, 'bold'),
                bg=self.colors['bg_medium'],
                fg=self.colors['text_primary']).pack()
        
        tk.Label(header_frame, 
                text="Arrows: Pan/Tilt • +/-: Zoom • F1-F8: Switch cameras • Settings: Configure",
                font=('Segoe UI', 8),
                bg=self.colors['bg_medium'],
                fg=self.colors['text_secondary']).pack(pady=(3, 0))

        # Separator
        separator = tk.Frame(top_frame, height=1, bg=self.colors['border'])
        separator.pack(fill="x", padx=20, pady=5)

        # Status and Control Panel
        control_panel = tk.Frame(top_frame, bg=self.colors['bg_medium'])
        control_panel.pack(pady=(3, 5))
        
        # Status indicator
        status_frame = tk.Frame(control_panel, bg=self.colors['bg_medium'])
        status_frame.pack(side="left", padx=20)
        
        self.status_indicator = tk.Label(status_frame,
                                        text="●",
                                        font=('Segoe UI', 16),
                                        bg=self.colors['bg_medium'],
                                        fg=self.colors['text_secondary'])
        self.status_indicator.pack(side="left", padx=5)
        
        self.status_label = tk.Label(status_frame, 
                                     text="Ready to connect",
                                     font=('Segoe UI', 10),
                                     bg=self.colors['bg_medium'],
                                     fg=self.colors['text_secondary'])
        self.status_label.pack(side="left")
        
        # Speed control
        speed_frame = tk.Frame(top_frame, 
                              bg=self.colors['bg_light'],
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        speed_frame.pack(pady=(5, 8), padx=120, fill="x")
        
        speed_label_frame = tk.Frame(speed_frame, bg=self.colors['bg_light'])
        speed_label_frame.pack(pady=(6, 3))
        
        tk.Label(speed_label_frame,
                text="⚡ Movement Speed:",
                font=('Segoe UI', 9, 'bold'),
                bg=self.colors['bg_light'],
                fg=self.colors['text_primary']).pack(side="left", padx=5)
        
        self.speed_value_label = tk.Label(speed_label_frame,
                                          text=f"{self.move_speed}",
                                          font=('Segoe UI', 9, 'bold'),
                                          bg=self.colors['accent'],
                                          fg=self.colors['text_primary'],
                                          padx=6,
                                          pady=1)
        self.speed_value_label.pack(side="left", padx=5)
        
        # Speed slider
        slider_container = tk.Frame(speed_frame, bg=self.colors['bg_light'])
        slider_container.pack(pady=(0, 6), padx=20, fill="x")
        
        tk.Label(slider_container,
                text="Slow",
                font=('Segoe UI', 8),
                bg=self.colors['bg_light'],
                fg=self.colors['text_secondary']).pack(side="left", padx=5)
        
        self.speed_slider = tk.Scale(slider_container,
                                     from_=1,
                                     to=24,
                                     orient=tk.HORIZONTAL,
                                     bg=self.colors['bg_dark'],
                                     fg=self.colors['text_primary'],
                                     troughcolor=self.colors['bg_medium'],
                                     highlightthickness=0,
                                     activebackground=self.colors['accent'],
                                     sliderrelief=tk.FLAT,
                                     showvalue=0,
                                     command=self.update_speed)
        self.speed_slider.set(self.move_speed)
        self.speed_slider.pack(side="left", fill="x", expand=True, padx=10)
        
        tk.Label(slider_container,
                text="Fast",
                font=('Segoe UI', 8),
                bg=self.colors['bg_light'],
                fg=self.colors['text_secondary']).pack(side="left", padx=5)

        # ================= VIDEO GRID =================
        video_container = tk.Frame(root, bg="#000000")
        video_container.pack(fill="both", expand=True, padx=1, pady=1)
        
        self.video_frame = tk.Frame(video_container, bg="#000000")
        self.video_frame.pack(fill="both", expand=True)

        for i in range(8):
            # Container for each camera view - FIXED SIZE
            cam_container = tk.Frame(self.video_frame, 
                                    bg="#000000",
                                    highlightbackground="#ffffff",
                                    highlightthickness=1,
                                    width=465,
                                    height=430)
            cam_container.grid(row=i//4, column=i%4, padx=0, pady=0, sticky="nsew")
            cam_container.grid_propagate(False)  # Prevent container from resizing to contents
            
            # Video display label (no separate name label)
            lbl = tk.Label(cam_container, 
                          bg="#000000",
                          text=f"F{i+1}\nNo Signal",
                          font=('Segoe UI', 10),
                          fg="#666666",
                          bd=0,
                          padx=0,
                          pady=0,
                          highlightthickness=0)
            lbl.pack(fill="both", expand=True, padx=0, pady=0)
            self.video_labels[f"F{i+1}"] = lbl
            
            # Store label reference for active camera highlighting (optional)
            self.camera_name_labels[f"F{i+1}"] = lbl
        
        # Make video grid with FIXED equal cells (no fighting)
        for i in range(2):
            self.video_frame.grid_rowconfigure(i, weight=0, minsize=430)
        for i in range(4):
            self.video_frame.grid_columnconfigure(i, weight=0, minsize=465)
        
        # Force widget size calculation
        self.root.update()

    # ================= CONFIGURATION WINDOW =================
    
    def open_config_window(self):
        """Open the camera configuration dialog"""
        if self.config_window is not None and tk.Toplevel.winfo_exists(self.config_window):
            self.config_window.lift()
            self.config_window.focus()
            return
        
        self.config_window = Toplevel(self.root)
        self.config_window.title("Camera Configuration")
        self.config_window.geometry("1000x900")
        self.config_window.configure(bg=self.colors['bg_dark'])
        
        # Make it modal
        self.config_window.transient(self.root)
        self.config_window.grab_set()
        
        # Header
        header_frame = tk.Frame(self.config_window, bg=self.colors['bg_medium'])
        header_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(header_frame,
                text="📹 Camera Configuration",
                font=('Segoe UI', 14, 'bold'),
                bg=self.colors['bg_medium'],
                fg=self.colors['text_primary']).pack(pady=15)
        
        tk.Label(header_frame,
                text="Configure IP addresses for PTZ control and RTSP URLs for video streams (8 cameras supported)",
                font=('Segoe UI', 9),
                bg=self.colors['bg_medium'],
                fg=self.colors['text_secondary']).pack(pady=(0, 15))
        
        # Configuration container
        config_container = tk.Frame(self.config_window, bg=self.colors['bg_dark'])
        config_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Store entry widgets temporarily
        ip_entries = []
        rtsp_entries = []
        
        # Camera configuration grid
        for i in range(8):
            cam_frame = tk.Frame(config_container,
                                bg=self.colors['bg_light'],
                                relief=tk.FLAT,
                                highlightbackground=self.colors['border'],
                                highlightthickness=1)
            cam_frame.pack(pady=6, fill="x")
            
            # Camera number badge
            badge = tk.Label(cam_frame,
                           text=f"CAM {i+1}",
                           font=('Segoe UI', 9, 'bold'),
                           bg=self.colors['accent'],
                           fg=self.colors['text_primary'],
                           padx=10,
                           pady=2)
            badge.grid(row=0, column=0, rowspan=2, padx=(10, 15), pady=10, sticky="ns")
            
            # IP Configuration
            tk.Label(cam_frame,
                    text="IP Address:",
                    font=('Segoe UI', 9),
                    bg=self.colors['bg_light'],
                    fg=self.colors['text_secondary'],
                    anchor="w").grid(row=0, column=1, sticky="w", padx=5, pady=(10, 2))
            
            ip_ent = tk.Entry(cam_frame,
                            width=20,
                            font=('Consolas', 9),
                            bg=self.colors['bg_dark'],
                            fg=self.colors['text_primary'],
                            insertbackground=self.colors['text_primary'],
                            relief=tk.FLAT,
                            highlightbackground=self.colors['border'],
                            highlightthickness=1)
            ip_ent.insert(0, self.camera_configs[i]['ip'])
            ip_ent.grid(row=0, column=2, padx=5, pady=(10, 2), sticky="w")
            ip_entries.append(ip_ent)
            
            # RTSP Configuration
            tk.Label(cam_frame,
                    text="RTSP URL:",
                    font=('Segoe UI', 9),
                    bg=self.colors['bg_light'],
                    fg=self.colors['text_secondary'],
                    anchor="w").grid(row=1, column=1, sticky="w", padx=5, pady=(2, 10))
            
            rtsp_ent = tk.Entry(cam_frame,
                               width=55,
                               font=('Consolas', 9),
                               bg=self.colors['bg_dark'],
                               fg=self.colors['text_primary'],
                               insertbackground=self.colors['text_primary'],
                               relief=tk.FLAT,
                               highlightbackground=self.colors['border'],
                               highlightthickness=1)
            rtsp_ent.insert(0, self.camera_configs[i]['rtsp'])
            rtsp_ent.grid(row=1, column=2, padx=5, pady=(2, 10), sticky="w")
            rtsp_entries.append(rtsp_ent)
        
        # Button frame
        button_frame = tk.Frame(self.config_window, bg=self.colors['bg_dark'])
        button_frame.pack(pady=20)
        
        # Connect button
        connect_btn = tk.Button(button_frame,
                               text="⚡ CONNECT & START",
                               command=lambda: self.connect_and_close(ip_entries, rtsp_entries),
                               bg=self.colors['accent'],
                               fg=self.colors['text_primary'],
                               font=('Segoe UI', 11, 'bold'),
                               relief=tk.FLAT,
                               cursor="hand2",
                               padx=30,
                               pady=12)
        connect_btn.pack(side="left", padx=10)
        
        # Close button
        close_btn = tk.Button(button_frame,
                             text="Cancel",
                             command=self.config_window.destroy,
                             bg=self.colors['bg_light'],
                             fg=self.colors['text_primary'],
                             font=('Segoe UI', 10),
                             relief=tk.FLAT,
                             cursor="hand2",
                             padx=30,
                             pady=12)
        close_btn.pack(side="left", padx=10)
    
    def connect_and_close(self, ip_entries, rtsp_entries):
        """Save configuration, connect cameras and close configuration window"""
        # Save the configuration
        for i in range(8):
            self.camera_configs[i]['ip'] = ip_entries[i].get().strip()
            self.camera_configs[i]['rtsp'] = rtsp_entries[i].get().strip()
        
        self.connect_cameras()
        if self.config_window:
            self.config_window.destroy()
    
    def show_controls_help(self):
        """Show help dialog with control instructions"""
        help_text = (
            "PTZ Camera Controller - Controls\n\n"
            "Movement:\n"
            "• Arrow Keys: Control camera pan/tilt\n"
            "• + / =: Zoom in\n"
            "• - : Zoom out\n"
            "• Speed Slider: Adjust movement speed\n\n"
            "Camera Selection:\n"
            "• F1-F8: Control Camera 1-8\n\n"
            "Configuration:\n"
            "• Settings → Configure Cameras: Set IP and RTSP URLs"
        )
        messagebox.showinfo("Controls Help", help_text)

    # ================= CONNECT =================

    def connect_cameras(self):

        keyboard.unhook_all()
        self.running = False
        time.sleep(0.3)

        for cap in self.video_caps.values():
            cap.release()

        self.cameras.clear()
        self.video_caps.clear()
        self.video_frames.clear()

        for i in range(8):

            ip = self.camera_configs[i]['ip']
            rtsp = self.camera_configs[i]['rtsp']

            cam_key = f"F{i+1}"

            if ip:
                try:
                    self.cameras[cam_key] = Camera(ip)
                except:
                    pass

            if rtsp:
                cap = cv2.VideoCapture(rtsp, cv2.CAP_FFMPEG)

                # Force TCP
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)

                if not cap.isOpened():
                    print(f"{cam_key} failed to open stream")
                else:
                    print(f"{cam_key} stream connected")

                self.video_caps[cam_key] = cap
                self.video_frames[cam_key] = None

        if not self.cameras:
            messagebox.showwarning("No Cameras", "Please configure at least one camera IP address.\n\nGo to Settings → Configure Cameras to add camera configurations.")
            return

        self.active_name = list(self.cameras.keys())[0]
        self.active_cam = self.cameras[self.active_name]
        
        self.update_active_camera_display()
        self.status_indicator.config(fg=self.colors['success'])
        self.status_label.config(text=f"Connected • Controlling {self.active_name}",
                                 fg=self.colors['success'])

        keyboard.hook(self.on_key_event)

        self.running = True

        # Start capture threads
        for key in self.video_caps:
            threading.Thread(target=self.capture_loop,
                             args=(key,),
                             daemon=True).start()

        self.update_video()

    # ================= CAPTURE THREAD =================

    def capture_loop(self, key):

        cap = self.video_caps[key]

        while self.running:

            if not cap.isOpened():
                time.sleep(1)
                continue

            ret, frame = cap.read()

            if not ret:
                time.sleep(0.2)
                continue

            self.video_frames[key] = frame

            time.sleep(0.01)

    # ================= SPEED CONTROL =================
    
    def update_speed(self, value):
        """Update movement speed from slider"""
        self.move_speed = int(float(value))
        self.speed_value_label.config(text=f"{self.move_speed}")
    
    # ================= UI UPDATE =================
    
    def update_active_camera_display(self):
        """Update the visual indicator for the active camera"""
        for key, label in self.camera_name_labels.items():
            if key == self.active_name:
                # Add a subtle border to indicate active camera
                label.master.config(highlightbackground="#00ff00", highlightthickness=2)
            else:
                # Regular white border
                label.master.config(highlightbackground="#ffffff", highlightthickness=1)

    def update_video(self):

        for key, frame in self.video_frames.items():

            if frame is None:
                continue

            label = self.video_labels[key]

            # Fixed container size
            width = 465
            height = 430

            h, w = frame.shape[:2]

            # Calculate scale to fit within fixed container
            scale = min(width / w, height / h)

            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # Ensure dimensions are valid
            if new_w <= 0 or new_h <= 0:
                continue

            resized = cv2.resize(frame, (new_w, new_h))

            frame_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            label.imgtk = imgtk
            label.configure(image=imgtk, text="")

        self.root.after(30, self.update_video)

    # ================= MOVEMENT =================

    def update_movement(self):

        if not self.active_cam:
            return

        pan = 0
        tilt = 0

        if 'left' in self.pressed_keys:
            pan -= self.move_speed
        if 'right' in self.pressed_keys:
            pan += self.move_speed
        if 'up' in self.pressed_keys:
            tilt -= self.move_speed
        if 'down' in self.pressed_keys:
            tilt += self.move_speed

        self.active_cam.pantilt(pan, tilt)

    # ================= KEYBOARD =================

    def on_key_event(self, e):

        if not self.active_cam:
            return

        if e.event_type == 'down':

            if e.name in ['up', 'down', 'left', 'right']:
                self.pressed_keys.add(e.name)
                self.update_movement()

            # Zoom controls
            elif e.name in ['+', '=', 'add']:
                self.active_cam.zoom(4)  # Zoom in
            elif e.name in ['-', 'subtract']:
                self.active_cam.zoom(-4)  # Zoom out

            elif e.name in ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8']:
                # Extract camera number from f-key name
                cam_num = e.name[1:]  # Get the number part (could be 1 or 2 digits)
                key = f"F{cam_num}"
                if key in self.cameras:
                    self.active_cam = self.cameras[key]
                    self.active_name = key
                    self.update_active_camera_display()
                    self.status_label.config(text=f"Connected • Controlling {key}")

        elif e.event_type == 'up':

            if e.name in ['up', 'down', 'left', 'right']:
                if e.name in self.pressed_keys:
                    self.pressed_keys.remove(e.name)

                if self.pressed_keys:
                    self.update_movement()
                else:
                    self.active_cam.pantilt(0, 0)

            # Stop zoom when key is released
            elif e.name in ['+', '=', 'add', '-', 'subtract']:
                self.active_cam.zoom(0)


# ================= MAIN =================

if __name__ == "__main__":
    root = tk.Tk()
    app = PTZApp(root)
    root.mainloop()
