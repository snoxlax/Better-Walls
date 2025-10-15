import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes
import winreg
import datetime
import os
from pathlib import Path
from PIL import Image, ImageTk, UnidentifiedImageError
from screenInfo import get_monitor_info
from imageCrop import ImageCropper


class WallpaperApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Better-Walls")
        self.monitors = get_monitor_info()
        self.min_x, self.min_y, self.max_x, self.max_y = self.calculate_bounds()
        self.scale = self.calculate_scale()
        self.offset_x = -self.min_x
        self.offset_y = -self.min_y
        self.canvas = None
        self.cropped_images = {}
        self.thumbnails = {}
        self.photo_images = {}
        self.last_save_dir = None
        self.last_open_dir = None

        self.setup_theme()
        self.create_widgets()
        self.preload_current_crops()
        self.resize_window_to_content()

    def setup_theme(self):
        self.master.configure(bg='#2C2C2C')
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure('TButton', background='#6D2A8D',
                             foreground='white', font=('Segoe UI', 10))
        self.style.map('TButton', background=[('active', '#8B3CB0')])
        self.style.configure('TFrame', background='#2C2C2C')

        self.canvas_bg = '#1E1E1E'
        self.monitor_fill = '#4A148C'
        self.monitor_outline = '#8E24AA'
        self.monitor_text_color = 'white'

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
        return min(800 / width, 600 / height)

    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            main_frame,
            width=(self.max_x - self.min_x) * self.scale,
            height=(self.max_y - self.min_y) * self.scale,
            bg=self.canvas_bg,
            highlightthickness=0
        )
        self.canvas.pack(pady=20)

        for i, monitor in enumerate(self.monitors):
            self.draw_monitor(monitor, i)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.assemble_button = ttk.Button(
            button_frame, text="Assemble Wallpaper", command=self.assemble_wallpaper)
        self.assemble_button.pack(side=tk.LEFT, padx=5)

        self.exit_button = ttk.Button(
            button_frame, text="Exit", command=self.master.quit)
        self.exit_button.pack(side=tk.RIGHT, padx=5)

    def draw_monitor(self, monitor, index):
        padding = 10
        x1 = (monitor['Left'] + self.offset_x) * self.scale + padding
        y1 = (monitor['Top'] + self.offset_y) * self.scale + padding
        x2 = (monitor['Right'] + self.offset_x) * self.scale - padding
        y2 = (monitor['Bottom'] + self.offset_y) * self.scale - padding

        rect = self.canvas.create_rectangle(x1, y1, x2, y2,
                                            fill=self.monitor_fill,
                                            outline=self.monitor_outline,
                                            width=2)
        self.canvas.tag_bind(rect, '<Button-1>', lambda e,
                             m=monitor: self.open_image_cropper(m))

        self.canvas.create_text((x1+x2)/2, (y1+y2)/2,
                                text=f"Monitor {index+1}",
                                fill=self.monitor_text_color,
                                font=('Segoe UI', 12, 'bold'))

        if monitor['Handle'] in self.thumbnails:
            self.update_monitor_preview(
                monitor, self.cropped_images[monitor['Handle']])

    def open_image_cropper(self, monitor):
        file_path = filedialog.askopenfilename(initialdir=self.last_open_dir)
        if file_path:

            self.last_open_dir = os.path.dirname(file_path)
            cropper_window = tk.Toplevel(self.master)
            cropper_window.configure(bg='#2C2C2C')
            target_resolution = (
                monitor['Right'] - monitor['Left'], monitor['Bottom'] - monitor['Top'])
            preview_size = (
                (monitor['Right'] - monitor['Left'])/2, (monitor['Bottom'] - monitor['Top'])/2)
            cropper = ImageCropper(
                cropper_window, target_resolution, preview_size, self.style)
            cropper.upload_image(file_path)

            def on_crop():
                cropped_image = cropper.crop_image()
                if cropped_image:
                    self.cropped_images[monitor['Handle']] = cropped_image
                    self.update_monitor_preview(monitor, cropped_image)
                    self.save_crop_to_cache(monitor, cropped_image)

                    self.create_temp_wallpaper()
                cropper_window.destroy()

            crop_button = ttk.Button(
                cropper_window, text="Crop and Set", command=on_crop)
            crop_button.pack(pady=10, padx=5, side="right")

    def update_monitor_preview(self, monitor, image):
        padding = 10
        x1 = (monitor['Left'] + self.offset_x) * self.scale + padding
        y1 = (monitor['Top'] + self.offset_y) * self.scale + padding
        x2 = (monitor['Right'] + self.offset_x) * self.scale - padding
        y2 = (monitor['Bottom'] + self.offset_y) * self.scale - padding

        preview = image.copy()
        preview.thumbnail((int(x2-x1), int(y2-y1)))
        photo = ImageTk.PhotoImage(preview)

        if monitor['Handle'] in self.thumbnails:
            self.canvas.delete(self.thumbnails[monitor['Handle']])

        thumbnail = self.canvas.create_image((x1+x2)/2, (y1+y2)/2, image=photo)
        self.thumbnails[monitor['Handle']] = thumbnail
        self.photo_images[monitor['Handle']] = photo

        self.canvas.tag_bind(thumbnail, '<Button-1>',
                             lambda e, m=monitor: self.open_image_cropper(m))

        self.canvas.create_rectangle(x1, y1, x2, y2,
                                     outline=self.monitor_outline,
                                     width=2)

    def resize_window_to_content(self):
        """Resize the main window to fit content with padding"""
        # Calculate content size
        canvas_width = (self.max_x - self.min_x) * self.scale
        canvas_height = (self.max_y - self.min_y) * self.scale

        padding = 100
        window_width = int(canvas_width + padding)
        window_height = int(canvas_height + padding)

        window_width = max(window_width, 400)
        window_height = max(window_height, 300)

        self.master.geometry(f"{window_width}x{window_height}")
        self.master.update_idletasks()
        self.master.geometry("")

    def get_cache_dir(self):
        local_appdata = os.environ.get('LOCALAPPDATA')
        if local_appdata:
            base = Path(local_appdata) / "Better-Walls" / "cache"
        else:
            base = Path.cwd() / "cache"
        try:
            base.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Failed to create cache dir: {e}")
        return base

    def _ensure_rgb(self, image):
        if image.mode == 'RGB':
            return image

        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            rgba = image.convert('RGBA')
            background = Image.new('RGB', rgba.size, (0, 0, 0))
            background.paste(rgba, mask=rgba.split()[3])
            return background
        return image.convert('RGB')

    def cache_path_for_monitor(self, monitor):
        left = monitor['Left']
        top = monitor['Top']
        right = monitor['Right']
        bottom = monitor['Bottom']
        filename = f"{left}_{top}_{right}_{bottom}.jpg"
        return self.get_cache_dir() / filename

    def save_crop_to_cache(self, monitor, image):
        try:
            path = self.cache_path_for_monitor(monitor)
            rgb = self._ensure_rgb(image)
            tmp_path = path.with_suffix(path.suffix + ".tmp")

            rgb.save(tmp_path, format='JPEG', quality=90)
            os.replace(tmp_path, path)
        except OSError as e:
            print(f"Failed to save cache image: {e}")

    def create_temp_wallpaper(self):
        """Create a temporary assembled wallpaper with current crops and set it immediately"""
        if not self.cropped_images:
            return

        try:

            assembled_image = Image.new(
                'RGB', (self.max_x - self.min_x, self.max_y - self.min_y))

            for monitor in self.monitors:
                if monitor['Handle'] in self.cropped_images:
                    image = self.cropped_images[monitor['Handle']]
                    if image.mode != 'RGB':
                        image = self._ensure_rgb(image)
                    assembled_image.paste(
                        image, (monitor['Left'] - self.min_x, monitor['Top'] - self.min_y))

            temp_dir = self.get_cache_dir() / "temp"
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / "current_wallpaper.jpg"
            assembled_image.save(temp_path, format='JPEG', quality=90)

            self.set_wallpaper(str(temp_path))
        except (OSError, IOError, ValueError) as e:
            print(f"Failed to create temp wallpaper: {e}")

    def load_crop_from_cache(self, monitor):
        path = self.cache_path_for_monitor(monitor)
        if not path.exists():
            return None
        try:

            with Image.open(path) as img:
                img.load()
                return self._ensure_rgb(img)
        except (OSError, UnidentifiedImageError) as e:
            print(f"Failed to load cache image: {e}")

            try:
                path.unlink(missing_ok=True)
            except OSError as de:
                print(f"Failed to remove corrupted cache file: {de}")
            return None

    def preload_current_crops(self):
        for monitor in self.monitors:
            cached = self.load_crop_from_cache(monitor)
            if cached:
                target_w = monitor['Right'] - monitor['Left']
                target_h = monitor['Bottom'] - monitor['Top']
                if cached.size != (target_w, target_h):
                    try:
                        cached = cached.resize(
                            (target_w, target_h), Image.Resampling.LANCZOS)
                    except OSError as e:
                        print(f"Failed to resize cached image: {e}")
                self.cropped_images[monitor['Handle']] = cached
                self.update_monitor_preview(monitor, cached)

    def assemble_wallpaper(self):
        if not self.cropped_images:
            messagebox.showwarning(
                "No Images", "No images have been set")
            return

        assembled_image = Image.new(
            'RGB', (self.max_x - self.min_x, self.max_y - self.min_y))

        for monitor in self.monitors:
            if monitor['Handle'] in self.cropped_images:
                image = self.cropped_images[monitor['Handle']]
                if image.mode != 'RGB':
                    image = self._ensure_rgb(image)
                assembled_image.paste(
                    image, (monitor['Left'] - self.min_x, monitor['Top'] - self.min_y))

        current_date_time = datetime.datetime.now().strftime("%d-%m-%y_%H-%M-%S")
        file_name = "Full_Wallpaper"
        file_name_date = f"{file_name}_{current_date_time}.jpg"

        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg", initialfile=file_name_date, initialdir=self.last_save_dir)
        if save_path:
            assembled_image.save(save_path)
            print(f"Assembled wallpaper saved to: {save_path}")

            self.last_save_dir = os.path.dirname(save_path)
            self.set_wallpaper(save_path)

    def set_wallpaper(self, image_path):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "22")
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
        winreg.CloseKey(key)

        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)
        ctypes.windll.user32.UpdatePerUserSystemParameters(1)


def main():
    root = tk.Tk()

    WallpaperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
