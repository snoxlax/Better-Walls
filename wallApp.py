import ctypes
import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Any

from PIL import Image, ImageTk

import theme
from imageCrop import IMAGE_FILETYPES, ImageCropper
from screenInfo import get_monitor_info
from wallpaperService import WallpaperService

APP_ICON = 'horizon.ico'

MAP_MAX_W, MAP_MAX_H = 820, 520   # largest size of the monitor map
MAP_PAD = 24                      # desk margin around the monitors
GAP = 5                           # inset per monitor edge, so adjacent screens separate
RADIUS = 8


class WallpaperApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Better-Walls")
        self.monitors = get_monitor_info()
        self.bounds = self.calculate_bounds()
        self.min_x, self.min_y, self.max_x, self.max_y = self.bounds
        self.scale = self.calculate_scale()
        self.offset_x = -self.min_x
        self.offset_y = -self.min_y

        self.ui: dict[str, Any] = {
            'canvas': None,
            'last_open_dir': None,
            'hover': None,
        }
        self.images = {
            'cropped': {},
            'photo_images': {}
        }

        self.wallpaper_service = WallpaperService()

        self.style = theme.apply_theme(self.master)
        self.create_widgets()
        self.preload_current_crops()
        self.refresh_status()
        self.master.resizable(False, False)
        primary = next((m for m in self.monitors if m.get('IsPrimary') == 'Yes'),
                       self.monitors[0])
        x1, y1, x2, y2 = primary['Work']
        self.place_window(self.master, (x1 + x2) / 2, (y1 + y2) / 2)

    def place_window(self, win, center_x, center_y):
        """Center `win` on a point, kept inside the work area of the monitor
        that point is on (windows otherwise open at Windows' default spot)"""
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        work = next((m['Work'] for m in self.monitors
                     if m['Left'] <= center_x < m['Right']
                     and m['Top'] <= center_y < m['Bottom']),
                    self.monitors[0]['Work'])
        x = int(center_x - w / 2)
        y = int(center_y - h / 2)
        # Clamp; the title bar sits above the client area, so keep ~40px for it
        x = max(work[0], min(x, work[2] - w))
        y = max(work[1] + 40, min(y, work[3] - h))
        win.geometry(f"+{x}+{y}")

    def calculate_bounds(self):
        all_coords = [(m['Left'], m['Top'], m['Right'], m['Bottom'])
                      for m in self.monitors]
        return (
            min(coord[0] for coord in all_coords),
            min(coord[1] for coord in all_coords),
            max(coord[2] for coord in all_coords),
            max(coord[3] for coord in all_coords)
        )

    def calculate_scale(self):
        width = self.max_x - self.min_x
        height = self.max_y - self.min_y
        return min(MAP_MAX_W / width, MAP_MAX_H / height)

    # ---------- layout ----------

    def create_widgets(self):
        self.master.configure(bg=theme.DESK)

        # Toolbar: what to do on the left; progress and actions on the right
        toolbar = ttk.Frame(self.master, style='Bar.TFrame', padding=(20, 11))
        toolbar.pack(fill=tk.X)
        count = len(self.monitors)
        intro = ttk.Frame(toolbar, style='Bar.TFrame')
        intro.pack(side=tk.LEFT)
        ttk.Label(intro, style='BarTitle.TLabel',
                  text=f"{count} display{'s' if count != 1 else ''} found").pack(anchor='w')
        ttk.Label(intro, style='BarDim.TLabel',
                  text="Click a screen to choose its wallpaper").pack(anchor='w')

        self.assemble_button = ttk.Button(
            toolbar, text="Export wallpaper…", style='Primary.TButton',
            command=self.assemble_wallpaper)
        self.assemble_button.pack(side=tk.RIGHT)
        self.exit_button = ttk.Button(
            toolbar, text="Quit", style='BarGhost.TButton', command=self.master.quit)
        self.exit_button.pack(side=tk.RIGHT, padx=(0, 10))
        self.status_label = ttk.Label(toolbar, style='BarDim.TLabel')
        self.status_label.pack(side=tk.RIGHT, padx=(0, 16))
        tk.Frame(self.master, height=1, bg=theme.LINE).pack(fill=tk.X)

        # Monitor map fills the rest of the window
        map_w = (self.max_x - self.min_x) * self.scale + MAP_PAD * 2
        map_h = (self.max_y - self.min_y) * self.scale + MAP_PAD * 2
        canvas = tk.Canvas(self.master, width=map_w, height=map_h,
                           bg=theme.DESK, highlightthickness=0)
        canvas.pack(padx=12, pady=12)
        self.ui['canvas'] = canvas

        for i, monitor in enumerate(self.monitors):
            self.draw_monitor(monitor, i)

        # Hit-test by geometry on the canvas itself rather than per-item
        # bindings: redrawing items under the pointer re-fires Enter/Leave
        # and can loop, and empty-fill shapes only react on their outline.
        canvas.bind('<Motion>', self.on_map_motion)
        canvas.bind('<Leave>', lambda e: self.set_hover(None))
        canvas.bind('<Button-1>', self.on_map_click)

    def refresh_status(self):
        total = len(self.monitors)
        done = sum(1 for m in self.monitors
                   if m['Handle'] in self.images['cropped'])
        if done == 0:
            text = "No wallpapers set yet"
        elif done == total:
            text = f"All {total} displays set"
        else:
            text = f"{done} of {total} displays set"
        self.status_label.configure(text=text)
        self.assemble_button.state(['!disabled'] if done else ['disabled'])

    # ---------- monitor map ----------

    def monitor_box(self, monitor):
        x1 = (monitor['Left'] + self.offset_x) * self.scale + MAP_PAD + GAP
        y1 = (monitor['Top'] + self.offset_y) * self.scale + MAP_PAD + GAP
        x2 = (monitor['Right'] + self.offset_x) * self.scale + MAP_PAD - GAP
        y2 = (monitor['Bottom'] + self.offset_y) * self.scale + MAP_PAD - GAP
        return x1, y1, x2, y2

    def draw_monitor(self, monitor, index):
        """(Re)draw one monitor pane in its current state"""
        canvas = self.ui['canvas']
        tag = f"mon{index}"
        canvas.delete(tag)
        x1, y1, x2, y2 = self.monitor_box(monitor)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        hovered = self.ui['hover'] == index
        image = self.images['cropped'].get(monitor['Handle'])
        width = monitor['Right'] - monitor['Left']
        height = monitor['Bottom'] - monitor['Top']
        primary = monitor.get('IsPrimary') == 'Yes'

        if image is not None:
            w, h = max(1, int(x2 - x1)), max(1, int(y2 - y1))
            preview = theme.rounded_image(
                image.resize((w, h), Image.Resampling.LANCZOS), RADIUS, theme.DESK)
            photo = ImageTk.PhotoImage(preview)
            self.images['photo_images'][monitor['Handle']] = photo
            canvas.create_image(x1, y1, image=photo, anchor='nw', tags=tag)
            theme.round_rect(canvas, x1, y1, x2, y2, RADIUS, fill='',
                             outline=theme.ACCENT if hovered else theme.LINE_STRONG,
                             width=2 if hovered else 1, tags=tag)
            # Number badge so set screens stay identifiable
            self.draw_pill(x1 + 8, y1 + 8, str(index + 1), tag, anchor='nw',
                           dot=theme.SUN if primary else None)
        else:
            fill = theme.PANEL_HOVER if hovered else theme.PANEL
            theme.round_rect(canvas, x1, y1, x2, y2, RADIUS, fill=fill,
                             outline=theme.ACCENT if hovered else theme.LINE_STRONG,
                             width=2 if hovered else 1,
                             dash=() if hovered else (4, 4), tags=tag)
            plus = theme.ACCENT if hovered else theme.TEXT_DIM
            room = y2 - y1
            if room >= 90:
                arm = 9
                py = cy - 22
                canvas.create_line(cx - arm, py, cx + arm, py, fill=plus,
                                   width=2, capstyle='round', tags=tag)
                canvas.create_line(cx, py - arm, cx, py + arm, fill=plus,
                                   width=2, capstyle='round', tags=tag)
                ty = cy + 6
            else:
                ty = cy - 8
            canvas.create_text(cx, ty, text=f"Display {index + 1}",
                               fill=theme.TEXT, font=(theme.FONT_SEMI, 11),
                               tags=tag)
            detail = f"{width} × {height}" + ("  ·  Primary" if primary else "")
            canvas.create_text(cx, ty + 19, text=detail, fill=theme.TEXT_DIM,
                               font=(theme.FONT, 9), tags=tag)


    def draw_pill(self, x, y, text, tag, anchor='nw', color=theme.TEXT, dot=None):
        """Small dark label that stays readable on top of any image"""
        canvas = self.ui['canvas']
        font = (theme.FONT_SEMI, 9)
        probe = canvas.create_text(0, 0, text=text, font=font, anchor='nw')
        bx1, by1, bx2, by2 = canvas.bbox(probe)
        canvas.delete(probe)
        tw, th = bx2 - bx1, by2 - by1
        dot_w = 12 if dot else 0
        w, h = tw + 16 + dot_w, th + 6
        if anchor == 's':
            x1, y1 = x - w / 2, y - h
        else:
            x1, y1 = x, y
        theme.round_rect(canvas, x1, y1, x1 + w, y1 + h, h / 2,
                         fill=theme.BG, outline='', tags=tag)
        if dot:
            canvas.create_oval(x1 + 8, y1 + h / 2 - 3, x1 + 14, y1 + h / 2 + 3,
                               fill=dot, outline='', tags=tag)
        canvas.create_text(x1 + 8 + dot_w, y1 + h / 2, text=text, fill=color,
                           font=font, anchor='w', tags=tag)

    def monitor_at(self, x, y):
        for i, monitor in enumerate(self.monitors):
            x1, y1, x2, y2 = self.monitor_box(monitor)
            if x1 <= x <= x2 and y1 <= y <= y2:
                return i
        return None

    def on_map_motion(self, event):
        self.set_hover(self.monitor_at(event.x, event.y))

    def on_map_click(self, event):
        index = self.monitor_at(event.x, event.y)
        if index is not None:
            self.set_hover(None)
            self.open_image_cropper(self.monitors[index], index)

    def set_hover(self, index):
        previous = self.ui['hover']
        if previous == index:
            return
        self.ui['hover'] = index
        self.ui['canvas'].configure(cursor='' if index is None else 'hand2')
        if previous is not None:
            self.draw_monitor(self.monitors[previous], previous)
        if index is not None:
            self.draw_monitor(self.monitors[index], index)

    # ---------- cropping ----------

    def open_image_cropper(self, monitor, index):
        file_path = filedialog.askopenfilename(
            parent=self.master, initialdir=self.ui['last_open_dir'],
            filetypes=IMAGE_FILETYPES)
        if not file_path:
            return

        self.ui['last_open_dir'] = os.path.dirname(file_path)
        target_w = monitor['Right'] - monitor['Left']
        target_h = monitor['Bottom'] - monitor['Top']
        target_resolution = (target_w, target_h)
        # Half the monitor size, but small enough to fit on screen
        preview_scale = min(0.5, 1100 / target_w, 680 / target_h)
        preview_size = (int(target_w * preview_scale),
                        int(target_h * preview_scale))

        cropper_window = tk.Toplevel(self.master)
        cropper_window.withdraw()  # hidden until placed, so it doesn't flash at the corner
        cropper_window.transient(self.master)
        cropper = ImageCropper(cropper_window, target_resolution, preview_size,
                               self.style, display_name=f"Display {index + 1}")
        if not cropper.upload_image(file_path):
            cropper_window.destroy()
            return

        def on_crop(_event=None):
            cropped_image = cropper.crop_image()
            if cropped_image:
                self.images['cropped'][monitor['Handle']] = cropped_image
                self.draw_monitor(monitor, index)
                self.refresh_status()
                self.wallpaper_service.save_crop_to_cache(monitor, cropped_image)
                self.wallpaper_service.create_temp_wallpaper(
                    self.monitors, self.images['cropped'], self.bounds)
            cropper_window.destroy()

        set_button = ttk.Button(cropper.actions, text="Set wallpaper",
                                style='Primary.TButton', command=on_crop)
        set_button.pack(side=tk.RIGHT)
        ttk.Button(cropper.actions, text="Cancel", style='BarGhost.TButton',
                   command=cropper_window.destroy).pack(side=tk.RIGHT, padx=(0, 10))
        cropper_window.bind('<Return>', on_crop)
        cropper_window.bind('<Escape>', lambda e: cropper_window.destroy())
        # Open centered over the main window rather than at the screen corner
        self.master.update_idletasks()
        self.place_window(
            cropper_window,
            self.master.winfo_rootx() + self.master.winfo_width() / 2,
            self.master.winfo_rooty() + self.master.winfo_height() / 2)
        cropper_window.deiconify()
        cropper_window.focus_set()

    def preload_current_crops(self):
        for i, monitor in enumerate(self.monitors):
            cached = self.wallpaper_service.load_crop_from_cache(monitor)
            if cached:
                target_w = monitor['Right'] - monitor['Left']
                target_h = monitor['Bottom'] - monitor['Top']
                if cached.size != (target_w, target_h):
                    try:
                        cached = cached.resize(
                            (target_w, target_h), Image.Resampling.LANCZOS)
                    except OSError as e:
                        print(f"Failed to resize cached image: {e}")
                self.images['cropped'][monitor['Handle']] = cached
                self.draw_monitor(monitor, i)

    def assemble_wallpaper(self):
        if not self.images['cropped']:
            return

        file_name_date = self.wallpaper_service.generate_filename()
        save_path = filedialog.asksaveasfilename(
            parent=self.master, title="Export wallpaper",
            defaultextension=".jpg", initialfile=file_name_date,
            initialdir=self.wallpaper_service.last_save_dir)

        if save_path:
            self.wallpaper_service.assemble_wallpaper(
                self.monitors, self.images['cropped'], self.bounds, save_path)
            self.status_label.configure(
                text=f"Saved {os.path.basename(save_path)}")


def enable_dpi_awareness():
    """Make Windows report real pixel coordinates instead of DPI-scaled ones.
    Must run before any window is created."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor aware (Win 8.1+)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def resource_path(name):
    """Path to a bundled file, both from source and inside a PyInstaller exe"""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def set_app_icon(root):
    """Use our icon for all windows and give the app its own taskbar entry
    (otherwise Windows groups it under python.exe's icon)"""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "BetterWalls.App")
    except (AttributeError, OSError):
        pass
    try:
        root.iconbitmap(default=resource_path(APP_ICON))
    except tk.TclError:
        pass


def main():
    enable_dpi_awareness()
    root = tk.Tk()
    root.withdraw()  # hidden until built and centered
    set_app_icon(root)

    WallpaperApp(root)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
