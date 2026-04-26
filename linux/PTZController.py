import tkinter as tk
from tkinter import messagebox, Toplevel
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
        self.root.resizable(True, True)

        # Linux-compatible maximize
        self.root.attributes('-zoomed', True)

        # Linux icon (PNG; .ico not supported by tkinter on Linux)
        try:
            icon = tk.PhotoImage(file='PTZController.png')
            self.root.iconphoto(True, icon)
        except Exception:
            pass

        self.colors = {
            'bg_dark':        '#1a1a2e',
            'bg_medium':      '#16213e',
            'bg_light':       '#0f3460',
            'accent':         '#e94560',
            'accent_hover':   '#c93350',
            'text_primary':   '#ffffff',
            'text_secondary': '#b8b8b8',
            'success':        '#00d9a3',
            'warning':        '#ffa500',
            'border':         '#2d2d44',
        }

        self.root.configure(bg='#000000')

        self.cameras = {}
        self.video_caps = {}
        self.video_frames = {}
        self.video_labels = {}
        self.camera_name_labels = {}
        self.active_cam = None
        self.active_name = ''

        self.pressed_keys = set()
        self.move_speed = 6
        self.running = False
        self.config_window = None

        self.camera_configs = [{'ip': '', 'rtsp': ''} for _ in range(8)]

        # ── Global keyboard bindings (tkinter bind_all — no external libs) ──
        # Works for all widgets in the window; no compilation or root needed.
        self.root.bind_all('<KeyPress>',   self._on_key_press)
        self.root.bind_all('<KeyRelease>', self._on_key_release)

        # ── Menu bar ──────────────────────────────────────────────────────
        menubar = tk.Menu(root,
                          bg=self.colors['bg_medium'],
                          fg=self.colors['text_primary'])
        root.config(menu=menubar)

        config_menu = tk.Menu(menubar, tearoff=0,
                              bg=self.colors['bg_medium'],
                              fg=self.colors['text_primary'])
        menubar.add_cascade(label='Settings', menu=config_menu)
        config_menu.add_command(label='Configure Cameras...',
                                command=self.open_config_window)
        config_menu.add_separator()
        config_menu.add_command(label='Exit', command=root.quit)

        help_menu = tk.Menu(menubar, tearoff=0,
                            bg=self.colors['bg_medium'],
                            fg=self.colors['text_primary'])
        menubar.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='Controls', command=self.show_controls_help)

        # ── Top panel ────────────────────────────────────────────────────
        top_frame = tk.Frame(root, bg=self.colors['bg_medium'], relief=tk.FLAT)
        top_frame.pack(side='top', fill='x', padx=5, pady=5)

        header_frame = tk.Frame(top_frame, bg=self.colors['bg_medium'])
        header_frame.pack(pady=(8, 5))

        tk.Label(header_frame,
                 text='🎥 PTZ Camera Controller',
                 font=('Ubuntu', 14, 'bold'),
                 bg=self.colors['bg_medium'],
                 fg=self.colors['text_primary']).pack()

        tk.Label(header_frame,
                 text='Arrows: Pan/Tilt  •  +/-: Zoom  •  F1-F8: Switch cameras  •  Settings: Configure',
                 font=('Ubuntu', 8),
                 bg=self.colors['bg_medium'],
                 fg=self.colors['text_secondary']).pack(pady=(3, 0))

        separator = tk.Frame(top_frame, height=1, bg=self.colors['border'])
        separator.pack(fill='x', padx=20, pady=5)

        control_panel = tk.Frame(top_frame, bg=self.colors['bg_medium'])
        control_panel.pack(pady=(3, 5))

        status_frame = tk.Frame(control_panel, bg=self.colors['bg_medium'])
        status_frame.pack(side='left', padx=20)

        self.status_indicator = tk.Label(status_frame,
                                         text='●',
                                         font=('Ubuntu', 16),
                                         bg=self.colors['bg_medium'],
                                         fg=self.colors['text_secondary'])
        self.status_indicator.pack(side='left', padx=5)

        self.status_label = tk.Label(status_frame,
                                     text='Ready to connect',
                                     font=('Ubuntu', 10),
                                     bg=self.colors['bg_medium'],
                                     fg=self.colors['text_secondary'])
        self.status_label.pack(side='left')

        # Speed control
        speed_frame = tk.Frame(top_frame,
                               bg=self.colors['bg_light'],
                               highlightbackground=self.colors['border'],
                               highlightthickness=1)
        speed_frame.pack(pady=(5, 8), padx=120, fill='x')

        speed_label_frame = tk.Frame(speed_frame, bg=self.colors['bg_light'])
        speed_label_frame.pack(pady=(6, 3))

        tk.Label(speed_label_frame,
                 text='⚡ Movement Speed:',
                 font=('Ubuntu', 9, 'bold'),
                 bg=self.colors['bg_light'],
                 fg=self.colors['text_primary']).pack(side='left', padx=5)

        self.speed_value_label = tk.Label(speed_label_frame,
                                          text=str(self.move_speed),
                                          font=('Ubuntu', 9, 'bold'),
                                          bg=self.colors['accent'],
                                          fg=self.colors['text_primary'],
                                          padx=6, pady=1)
        self.speed_value_label.pack(side='left', padx=5)

        slider_container = tk.Frame(speed_frame, bg=self.colors['bg_light'])
        slider_container.pack(pady=(0, 6), padx=20, fill='x')

        tk.Label(slider_container, text='Slow',
                 font=('Ubuntu', 8),
                 bg=self.colors['bg_light'],
                 fg=self.colors['text_secondary']).pack(side='left', padx=5)

        self.speed_slider = tk.Scale(slider_container,
                                     from_=1, to=24,
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
        self.speed_slider.pack(side='left', fill='x', expand=True, padx=10)

        tk.Label(slider_container, text='Fast',
                 font=('Ubuntu', 8),
                 bg=self.colors['bg_light'],
                 fg=self.colors['text_secondary']).pack(side='left', padx=5)

        # ── Video grid ───────────────────────────────────────────────────
        video_container = tk.Frame(root, bg='#000000')
        video_container.pack(fill='both', expand=True, padx=1, pady=1)

        self.video_frame = tk.Frame(video_container, bg='#000000')
        self.video_frame.pack(fill='both', expand=True)

        for i in range(8):
            cam_container = tk.Frame(self.video_frame,
                                     bg='#000000',
                                     highlightbackground='#ffffff',
                                     highlightthickness=1,
                                     width=465, height=430)
            cam_container.grid(row=i // 4, column=i % 4,
                               padx=0, pady=0, sticky='nsew')
            cam_container.grid_propagate(False)

            lbl = tk.Label(cam_container,
                           bg='#000000',
                           text=f'F{i + 1}\nNo Signal',
                           font=('Ubuntu', 10),
                           fg='#666666',
                           bd=0, padx=0, pady=0,
                           highlightthickness=0)
            lbl.pack(fill='both', expand=True)
            self.video_labels[f'F{i + 1}'] = lbl
            self.camera_name_labels[f'F{i + 1}'] = lbl

        for i in range(2):
            self.video_frame.grid_rowconfigure(i, weight=0, minsize=430)
        for i in range(4):
            self.video_frame.grid_columnconfigure(i, weight=0, minsize=465)

        self.root.update()

    # ── Configuration window ─────────────────────────────────────────────

    def open_config_window(self):
        if self.config_window is not None and tk.Toplevel.winfo_exists(self.config_window):
            self.config_window.lift()
            self.config_window.focus()
            return

        self.config_window = Toplevel(self.root)
        self.config_window.title('Camera Configuration')
        self.config_window.geometry('1000x900')
        self.config_window.configure(bg=self.colors['bg_dark'])
        self.config_window.transient(self.root)
        self.config_window.grab_set()

        header_frame = tk.Frame(self.config_window, bg=self.colors['bg_medium'])
        header_frame.pack(fill='x', padx=10, pady=10)

        tk.Label(header_frame,
                 text='📹 Camera Configuration',
                 font=('Ubuntu', 14, 'bold'),
                 bg=self.colors['bg_medium'],
                 fg=self.colors['text_primary']).pack(pady=15)

        tk.Label(header_frame,
                 text='Configure IP addresses for PTZ control and RTSP URLs for video streams (8 cameras supported)',
                 font=('Ubuntu', 9),
                 bg=self.colors['bg_medium'],
                 fg=self.colors['text_secondary']).pack(pady=(0, 15))

        config_container = tk.Frame(self.config_window, bg=self.colors['bg_dark'])
        config_container.pack(fill='both', expand=True, padx=20, pady=10)

        ip_entries = []
        rtsp_entries = []

        for i in range(8):
            cam_frame = tk.Frame(config_container,
                                 bg=self.colors['bg_light'],
                                 relief=tk.FLAT,
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=1)
            cam_frame.pack(pady=6, fill='x')

            tk.Label(cam_frame,
                     text=f'CAM {i + 1}',
                     font=('Ubuntu', 9, 'bold'),
                     bg=self.colors['accent'],
                     fg=self.colors['text_primary'],
                     padx=10, pady=2).grid(row=0, column=0, rowspan=2,
                                           padx=(10, 15), pady=10, sticky='ns')

            tk.Label(cam_frame, text='IP Address:',
                     font=('Ubuntu', 9),
                     bg=self.colors['bg_light'],
                     fg=self.colors['text_secondary'],
                     anchor='w').grid(row=0, column=1, sticky='w', padx=5, pady=(10, 2))

            ip_ent = tk.Entry(cam_frame, width=20,
                              font=('Ubuntu Mono', 9),
                              bg=self.colors['bg_dark'],
                              fg=self.colors['text_primary'],
                              insertbackground=self.colors['text_primary'],
                              relief=tk.FLAT,
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
            ip_ent.insert(0, self.camera_configs[i]['ip'])
            ip_ent.grid(row=0, column=2, padx=5, pady=(10, 2), sticky='w')
            ip_entries.append(ip_ent)

            tk.Label(cam_frame, text='RTSP URL:',
                     font=('Ubuntu', 9),
                     bg=self.colors['bg_light'],
                     fg=self.colors['text_secondary'],
                     anchor='w').grid(row=1, column=1, sticky='w', padx=5, pady=(2, 10))

            rtsp_ent = tk.Entry(cam_frame, width=55,
                                font=('Ubuntu Mono', 9),
                                bg=self.colors['bg_dark'],
                                fg=self.colors['text_primary'],
                                insertbackground=self.colors['text_primary'],
                                relief=tk.FLAT,
                                highlightbackground=self.colors['border'],
                                highlightthickness=1)
            rtsp_ent.insert(0, self.camera_configs[i]['rtsp'])
            rtsp_ent.grid(row=1, column=2, padx=5, pady=(2, 10), sticky='w')
            rtsp_entries.append(rtsp_ent)

        button_frame = tk.Frame(self.config_window, bg=self.colors['bg_dark'])
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                  text='⚡ CONNECT & START',
                  command=lambda: self.connect_and_close(ip_entries, rtsp_entries),
                  bg=self.colors['accent'],
                  fg=self.colors['text_primary'],
                  font=('Ubuntu', 11, 'bold'),
                  relief=tk.FLAT, cursor='hand2',
                  padx=30, pady=12).pack(side='left', padx=10)

        tk.Button(button_frame,
                  text='Cancel',
                  command=self.config_window.destroy,
                  bg=self.colors['bg_light'],
                  fg=self.colors['text_primary'],
                  font=('Ubuntu', 10),
                  relief=tk.FLAT, cursor='hand2',
                  padx=30, pady=12).pack(side='left', padx=10)

    def connect_and_close(self, ip_entries, rtsp_entries):
        for i in range(8):
            self.camera_configs[i]['ip'] = ip_entries[i].get().strip()
            self.camera_configs[i]['rtsp'] = rtsp_entries[i].get().strip()
        self.connect_cameras()
        if self.config_window:
            self.config_window.destroy()

    def show_controls_help(self):
        messagebox.showinfo('Controls Help',
            'PTZ Camera Controller - Controls\n\n'
            'Movement:\n'
            '• Arrow Keys: Control camera pan/tilt\n'
            '• + / =: Zoom in\n'
            '• - : Zoom out\n'
            '• Speed Slider: Adjust movement speed\n\n'
            'Camera Selection:\n'
            '• F1-F8: Control Camera 1-8\n\n'
            'Configuration:\n'
            '• Settings → Configure Cameras: Set IP and RTSP URLs')

    # ── Connect ───────────────────────────────────────────────────────────

    def connect_cameras(self):
        self.running = False
        time.sleep(0.3)

        for cap in self.video_caps.values():
            cap.release()

        self.cameras.clear()
        self.video_caps.clear()
        self.video_frames.clear()
        self.pressed_keys.clear()

        for i in range(8):
            ip   = self.camera_configs[i]['ip']
            rtsp = self.camera_configs[i]['rtsp']
            key  = f'F{i + 1}'

            if ip:
                try:
                    self.cameras[key] = Camera(ip)
                except Exception:
                    pass

            if rtsp:
                cap = cv2.VideoCapture(rtsp, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
                if not cap.isOpened():
                    print(f'{key} failed to open stream')
                else:
                    print(f'{key} stream connected')
                self.video_caps[key] = cap
                self.video_frames[key] = None

        if not self.cameras:
            messagebox.showwarning('No Cameras',
                'Please configure at least one camera IP address.\n\n'
                'Go to Settings → Configure Cameras to add camera configurations.')
            return

        self.active_name = list(self.cameras.keys())[0]
        self.active_cam  = self.cameras[self.active_name]

        self.update_active_camera_display()
        self.status_indicator.config(fg=self.colors['success'])
        self.status_label.config(
            text=f'Connected • Controlling {self.active_name}',
            fg=self.colors['success'])

        self.running = True

        for key in self.video_caps:
            threading.Thread(target=self.capture_loop,
                             args=(key,), daemon=True).start()

        self.update_video()

        # Return focus to the main window so keyboard bindings fire immediately
        self.root.focus_set()

    # ── Keyboard (tkinter bind_all — no external libs, no compilation) ────
    # Captures all keypresses inside the app window regardless of which
    # widget is focused. Arrow keys / F1-F8 / +/- all work here.

    # Tkinter keysym → normalised name used by movement logic
    _KEYSYM_MAP = {
        'Up':          'up',
        'Down':        'down',
        'Left':        'left',
        'Right':       'right',
        'F1':          'f1',
        'F2':          'f2',
        'F3':          'f3',
        'F4':          'f4',
        'F5':          'f5',
        'F6':          'f6',
        'F7':          'f7',
        'F8':          'f8',
        'plus':        'zoom_in',
        'equal':       'zoom_in',   # '=' is the same physical key as '+' (unshifted)
        'KP_Add':      'zoom_in',   # numpad +
        'minus':       'zoom_out',
        'KP_Subtract': 'zoom_out',  # numpad -
    }

    def _on_key_press(self, event):
        if not self.active_cam:
            return
        name = self._KEYSYM_MAP.get(event.keysym)
        if name is None:
            return

        if name in ('up', 'down', 'left', 'right'):
            if name not in self.pressed_keys:
                self.pressed_keys.add(name)
                self.update_movement()

        elif name == 'zoom_in':
            if 'zoom_in' not in self.pressed_keys:
                self.pressed_keys.add('zoom_in')
                self.active_cam.zoom(4)

        elif name == 'zoom_out':
            if 'zoom_out' not in self.pressed_keys:
                self.pressed_keys.add('zoom_out')
                self.active_cam.zoom(-4)

        elif name.startswith('f'):
            cam_key = f'F{name[1:]}'
            if cam_key in self.cameras:
                self.active_cam  = self.cameras[cam_key]
                self.active_name = cam_key
                self.update_active_camera_display()
                self.status_label.config(text=f'Connected • Controlling {cam_key}')

    def _on_key_release(self, event):
        if not self.active_cam:
            return
        name = self._KEYSYM_MAP.get(event.keysym)
        if name is None:
            return

        if name in ('up', 'down', 'left', 'right'):
            self.pressed_keys.discard(name)
            if self.pressed_keys - {'zoom_in', 'zoom_out'}:
                self.update_movement()
            else:
                self.active_cam.pantilt(0, 0)

        elif name in ('zoom_in', 'zoom_out'):
            self.pressed_keys.discard(name)
            self.active_cam.zoom(0)

    # ── Video capture ─────────────────────────────────────────────────────

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

    # ── Speed ─────────────────────────────────────────────────────────────

    def update_speed(self, value):
        self.move_speed = int(float(value))
        self.speed_value_label.config(text=str(self.move_speed))

    # ── UI helpers ────────────────────────────────────────────────────────

    def update_active_camera_display(self):
        for key, label in self.camera_name_labels.items():
            color     = '#00ff00' if key == self.active_name else '#ffffff'
            thickness = 2         if key == self.active_name else 1
            label.master.config(highlightbackground=color,
                                 highlightthickness=thickness)

    def update_video(self):
        for key, frame in self.video_frames.items():
            if frame is None:
                continue
            label            = self.video_labels[key]
            width, height    = 465, 430
            h, w             = frame.shape[:2]
            scale            = min(width / w, height / h)
            new_w, new_h     = int(w * scale), int(h * scale)
            if new_w <= 0 or new_h <= 0:
                continue
            resized   = cv2.resize(frame, (new_w, new_h))
            frame_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img       = Image.fromarray(frame_rgb)
            imgtk     = ImageTk.PhotoImage(image=img)
            label.imgtk = imgtk
            label.configure(image=imgtk, text='')
        self.root.after(30, self.update_video)

    # ── Movement ──────────────────────────────────────────────────────────

    def update_movement(self):
        if not self.active_cam:
            return
        pan  = 0
        tilt = 0
        if 'left'  in self.pressed_keys: pan  -= self.move_speed
        if 'right' in self.pressed_keys: pan  += self.move_speed
        if 'up'    in self.pressed_keys: tilt -= self.move_speed
        if 'down'  in self.pressed_keys: tilt += self.move_speed
        self.active_cam.pantilt(pan, tilt)


# ── Entry point ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    root = tk.Tk()
    app  = PTZApp(root)
    root.mainloop()
