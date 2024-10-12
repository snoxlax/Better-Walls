import tkinter as tk
from tkinter import filedialog, messagebox
import ctypes
import winreg
import datetime
from PIL import Image, ImageTk
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
        self.create_widgets()

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
        self.canvas = tk.Canvas(
            self.master,
            width=(self.max_x - self.min_x) * self.scale,
            height=(self.max_y - self.min_y) * self.scale
        )
        self.canvas.pack(padx=20, pady=20)

        for i, monitor in enumerate(self.monitors):
            self.draw_monitor(monitor, i)

        self.assemble_button = tk.Button(

            self.master, text="Assemble Wallpaper", command=self.assemble_wallpaper, bg="lightgreen",
            fg="black",
            font=("Arial", 10))
        self.assemble_button.pack(pady=5, side="left", padx=10)

        self.exit_button = tk.Button(
            self.master, text="Exit", command=self.master.quit, bg="lightgreen",
            fg="black",
            font=("Arial", 10))
        self.exit_button.pack(pady=5, side="right", padx=10)

        self.start_over_button = tk.Button(
            self.master, text="Start Over", command=self.start_over, state=tk.DISABLED, bg="lightgreen",
            fg="black",
            font=("Arial", 10))
        self.start_over_button.pack(pady=5, side="right", padx=10)

    def draw_monitor(self, monitor, index):
        x1 = (monitor['Left'] + self.offset_x) * self.scale
        y1 = (monitor['Top'] + self.offset_y) * self.scale
        x2 = (monitor['Right'] + self.offset_x) * self.scale
        y2 = (monitor['Bottom'] + self.offset_y) * self.scale

        rect = self.canvas.create_rectangle(x1, y1, x2, y2, fill='lightblue')
        self.canvas.tag_bind(rect, '<Button-1>', lambda e,
                             m=monitor: self.open_image_cropper(m))

        self.canvas.create_text((x1+x2)/2, (y1+y2)/2,
                                text=f"Monitor {index+1}")

        if monitor['Handle'] in self.thumbnails:
            self.update_monitor_preview(
                monitor, self.cropped_images[monitor['Handle']])

    def open_image_cropper(self, monitor):
        file_path = filedialog.askopenfilename()
        if file_path:
            cropper_window = tk.Toplevel(self.master)
            target_resolution = (
                monitor['Right'] - monitor['Left'], monitor['Bottom'] - monitor['Top'])
            preview_size = (
                (monitor['Right'] - monitor['Left'])/2, (monitor['Bottom'] - monitor['Top'])/2)
            cropper = ImageCropper(
                cropper_window, target_resolution, preview_size)
            cropper.upload_image(file_path)

            def on_crop():
                cropped_image = cropper.crop_image()
                if cropped_image:
                    self.cropped_images[monitor['Handle']] = cropped_image
                    self.update_monitor_preview(monitor, cropped_image)
                cropper_window.destroy()

            crop_button = tk.Button(
                cropper_window, text="Crop and Set", command=on_crop)
            crop_button.pack(pady=10, padx=5, side="right")

    def update_monitor_preview(self, monitor, image):
        x1 = (monitor['Left'] + self.offset_x) * self.scale
        y1 = (monitor['Top'] + self.offset_y) * self.scale
        x2 = (monitor['Right'] + self.offset_x) * self.scale
        y2 = (monitor['Bottom'] + self.offset_y) * self.scale

        preview = image.copy()
        preview.thumbnail((int(x2-x1), int(y2-y1)))
        photo = ImageTk.PhotoImage(preview)

        if monitor['Handle'] in self.thumbnails:
            self.canvas.delete(self.thumbnails[monitor['Handle']])

        thumbnail = self.canvas.create_image((x1+x2)/2, (y1+y2)/2, image=photo)
        self.thumbnails[monitor['Handle']] = thumbnail
        self.photo_images[monitor['Handle']] = photo

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
                assembled_image.paste(
                    image, (monitor['Left'] - self.min_x, monitor['Top'] - self.min_y))

        current_date_time = datetime.datetime.now().strftime("%d-%m-%y_%H-%M-%S")
        file_name = "Full_Wallpaper"
        file_name_date = f"{file_name}_{current_date_time}.jpg"

        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg", initialfile=file_name_date)
        if save_path:
            assembled_image.save(save_path)
            print(f"Assembled wallpaper saved to: {save_path}")
            self.set_wallpaper(save_path)
            self.start_over_button.config(state=tk.NORMAL)
            self.assemble_button.config(state=tk.DISABLED)

    def set_wallpaper(self, image_path):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "22")
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
        winreg.CloseKey(key)

        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0)
        ctypes.windll.user32.UpdatePerUserSystemParameters(1)

        messagebox.showinfo("Success", "Wallpaper has been set successfully!")

    def start_over(self):
        self.cropped_images.clear()
        self.thumbnails.clear()
        self.photo_images.clear()
        self.canvas.delete("all")
        for i, monitor in enumerate(self.monitors):
            self.draw_monitor(monitor, i)
        self.start_over_button.config(state=tk.DISABLED)
        self.assemble_button.config(state=tk.NORMAL)


def main():
    root = tk.Tk()
    WallpaperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
