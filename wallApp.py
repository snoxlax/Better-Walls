import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ctypes
import os
from PIL import Image, ImageTk
from screenInfo import get_monitor_info
from imageCrop import ImageCropper, IMAGE_FILETYPES
from wallpaperService import WallpaperService


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

        # Group related attributes
        self.ui = {
            'canvas': None,
            'last_open_dir': None
        }
        self.images = {
            'cropped': {},
            'thumbnails': {},
            'photo_images': {}
        }

        # Initialize wallpaper service
        self.wallpaper_service = WallpaperService()

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

        self.ui['canvas'] = tk.Canvas(
            main_frame,
            width=(self.max_x - self.min_x) * self.scale,
            height=(self.max_y - self.min_y) * self.scale,
            bg=self.canvas_bg,
            highlightthickness=0
        )
        self.ui['canvas'].pack(pady=20)

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

        rect = self.ui['canvas'].create_rectangle(x1, y1, x2, y2,
                                                  fill=self.monitor_fill,
                                                  outline=self.monitor_outline,
                                                  width=2)
        self.ui['canvas'].tag_bind(rect, '<Button-1>', lambda e,
                                   m=monitor: self.open_image_cropper(m))

        self.ui['canvas'].create_text((x1+x2)/2, (y1+y2)/2,
                                      text=f"Monitor {index+1}",
                                      fill=self.monitor_text_color,
                                      font=('Segoe UI', 12, 'bold'))

        if monitor['Handle'] in self.images['thumbnails']:
            self.update_monitor_preview(
                monitor, self.images['cropped'][monitor['Handle']])

    def open_image_cropper(self, monitor):
        file_path = filedialog.askopenfilename(
            initialdir=self.ui['last_open_dir'], filetypes=IMAGE_FILETYPES)
        if file_path:

            self.ui['last_open_dir'] = os.path.dirname(file_path)
            cropper_window = tk.Toplevel(self.master)
            cropper_window.configure(bg='#2C2C2C')
            target_w = monitor['Right'] - monitor['Left']
            target_h = monitor['Bottom'] - monitor['Top']
            target_resolution = (target_w, target_h)
            # Half the monitor size, but small enough to fit on screen
            preview_scale = min(0.5, 1200 / target_w, 750 / target_h)
            preview_size = (int(target_w * preview_scale),
                            int(target_h * preview_scale))
            cropper = ImageCropper(
                cropper_window, target_resolution, preview_size, self.style)
            if not cropper.upload_image(file_path):
                cropper_window.destroy()
                return

            def on_crop():
                cropped_image = cropper.crop_image()
                if cropped_image:
                    self.images['cropped'][monitor['Handle']] = cropped_image
                    self.update_monitor_preview(monitor, cropped_image)
                    self.wallpaper_service.save_crop_to_cache(
                        monitor, cropped_image)

                    self.wallpaper_service.create_temp_wallpaper(
                        self.monitors, self.images['cropped'], (self.min_x, self.min_y, self.max_x, self.max_y))
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

        if monitor['Handle'] in self.images['thumbnails']:
            self.ui['canvas'].delete(
                self.images['thumbnails'][monitor['Handle']])

        thumbnail = self.ui['canvas'].create_image(
            (x1+x2)/2, (y1+y2)/2, image=photo)
        self.images['thumbnails'][monitor['Handle']] = thumbnail
        self.images['photo_images'][monitor['Handle']] = photo

        self.ui['canvas'].tag_bind(thumbnail, '<Button-1>',
                                   lambda e, m=monitor: self.open_image_cropper(m))

        self.ui['canvas'].create_rectangle(x1, y1, x2, y2,
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

    def preload_current_crops(self):
        for monitor in self.monitors:
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
                self.update_monitor_preview(monitor, cached)

    def assemble_wallpaper(self):
        if not self.images['cropped']:
            messagebox.showwarning(
                "No Images", "No images have been set")
            return

        file_name_date = self.wallpaper_service.generate_filename()
        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg", initialfile=file_name_date, initialdir=self.wallpaper_service.last_save_dir)

        if save_path:
            self.wallpaper_service.assemble_wallpaper(
                self.monitors, self.images['cropped'], (self.min_x, self.min_y, self.max_x, self.max_y), save_path)


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


def main():
    enable_dpi_awareness()
    root = tk.Tk()

    WallpaperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
