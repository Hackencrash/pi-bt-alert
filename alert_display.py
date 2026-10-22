import tkinter as tk
import sys
import os
import time
from datetime import datetime
from picamera2 import Picamera2
from PIL import Image, ImageTk

STATE_FILE = "/tmp/alert_state"

# Args: message, level, duration
msg = sys.argv[1] if len(sys.argv) > 1 else "MESSAGE"
level = sys.argv[2] if len(sys.argv) > 2 else "info"
duration = int(sys.argv[3]) if len(sys.argv) > 3 else 5
camera_time = int(sys.argv[4]) if len(sys.argv) > 4 else 0

styles = {
    "info":     {"bg": "#1e1e1e", "fg": "white", "icon": "ℹ️"},
    "warning":  {"bg": "#ff9800", "fg": "black", "icon": "⚠️"},
    "critical": {"bg": "#d32f2f", "fg": "white", "icon": "🚨"},
}

style = styles.get(level, styles["info"])
is_time_mode = (level == "time")

root = tk.Tk()
root.attributes("-fullscreen", True)
root.configure(bg=style["bg"] if not is_time_mode else "#000000")
root.config(cursor="none")

frame = tk.Frame(root, bg=style["bg"] if not is_time_mode else "#000000")
frame.pack(expand=True, fill="both")

# Time mode is separate: no icon, no grow/shrink animation
if is_time_mode:
    clock = tk.Label(
        frame,
        text="",
        font=("Arial", 360),
        bg="#000000",
        fg="mediumaquamarine"
    )
    clock.place(relx=0.5, rely=0.5, anchor="center")

    def update_time():
        now = time.localtime()

        hours = now.tm_hour
        minutes = now.tm_min

        if int(time.time() * 2) % 2 == 0:
            time_str = f"{hours:02d}:{minutes:02d}"
        else:
            time_str = f"{hours:02d} {minutes:02d}"

        clock.config(text=time_str)

        delay = 500 - (int(time.time() * 1000) % 500)
        root.after(delay, update_time)

    def close():
        try:
            os.remove(STATE_FILE)
        except FileNotFoundError:
            pass
        os.system("/home/emotion/screen.sh off")
        root.destroy()

    update_time()
    root.after(duration * 1000, close)
    root.mainloop()
    raise SystemExit

inner = tk.Frame(frame, bg=style["bg"])
inner.place(relx=0.5, rely=0.5, anchor="center")

icon = tk.Label(
    inner,
    text=style["icon"],
    font=("Noto Color Emoji", 10),
    bg=style["bg"]
)
icon.pack(pady=10)

screen_width = root.winfo_screenwidth()

if len(msg) < 20:
    target_size = 150
elif len(msg) < 40:
    target_size = 105
else:
    target_size = 75

current_size = 1

label = tk.Label(
    inner,
    text=msg,
    font=("Arial", current_size),
    bg=style["bg"],
    fg=style["fg"],
    wraplength=screen_width - 100,
    justify="center"
)
label.pack(pady=10)

grow_speed = 20
shrink_speed = 30
frame_delay = 16

def grow():
    global current_size

    current_size += (target_size - current_size) * 0.25

    if abs(target_size - current_size) < 0.5:
        current_size = target_size

    icon.config(font=("Noto Color Emoji", int(current_size * 0.66)))

    base_font_size = target_size  # or whatever your "final" size is
    wraplength = (screen_width - 100) * (current_size / base_font_size)

    label.config(
        font=("Arial", int(current_size)),
        wraplength=wraplength
    )

    if current_size < target_size:
        root.after(frame_delay, grow)
    else:
        hold_time = max(500, (duration * 1000) - 1000)
        root.after(hold_time, shrink)

base_font_size = target_size  # same reference as in grow()

def shrink():
    global current_size
    if current_size > 1:
        current_size = max(1, current_size - shrink_speed)

        scale = current_size / base_font_size
        wraplength = (screen_width - 100) * scale

        icon.config(font=("Noto Color Emoji", max(1, int(current_size * 0.66))))

        label.config(
            font=("Arial", max(1, int(current_size))),
            wraplength=wraplength
        )

        root.after(frame_delay, shrink)
    else:
        if camera_time > 0:
            show_camera()
        else:
            close()

def show_camera():
    for widget in frame.winfo_children():
        widget.destroy()

    cam_label = tk.Label(frame, bg="black")
    cam_label.pack(fill="both", expand=True)

    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (1280, 720), "format": "RGB888"}
    )
    picam2.configure(config)
    picam2.start()

    start_time = time.time()

    def update_frame():
        frame_array = picam2.capture_array()
        image = Image.fromarray(frame_array).rotate(180)

        imgtk = ImageTk.PhotoImage(image=image)
        cam_label.imgtk = imgtk
        cam_label.config(image=imgtk)

        if time.time() - start_time < camera_time:
            root.after(30, update_frame)
        else:
            picam2.stop()
            picam2.close()
            close()

    update_frame()

def close():
    try:
        os.remove(STATE_FILE)
    except FileNotFoundError:
        pass
    os.system("/home/emotion/screen.sh off")
    root.destroy()

root.after(150, grow)
root.mainloop()
