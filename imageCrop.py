import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk


class ImageCropper:
    def __init__(self, master, target_resolution, preview_size, style):
        self.master = master
        self.target_resolution = target_resolution
        self.preview_size = preview_size
        self.style = style
        self.master.title(
            f"Image Cropper - Target: {target_resolution[0]}x{target_resolution[1]}")

        self.original_image = None
        self.preview_image = None
        self.image_item = None
        self.scale_factor = 1
        self.zoom_factor = 1
        self.min_zoom_factor = 1
        self.start_x = 0
        self.start_y = 0
        self.photo = None
        self.setup_ui()

    def setup_ui(self):
        self.master.configure(bg='#2C2C2C')

        self.canvas = tk.Canvas(
            self.master, width=self.preview_size[0], height=self.preview_size[1],
            bg="#1E1E1E", highlightthickness=0)
        self.canvas.pack(pady=10, padx=5)

        self.upload_button = ttk.Button(
            self.master, text="Upload Image", command=self.upload_image)
        self.upload_button.pack(pady=5)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

    def upload_image(self, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename()
        if file_path:
            self.original_image = Image.open(file_path)
            self.create_preview_image()
            self.show_image()

    def create_preview_image(self):
        width_ratio = self.preview_size[0] / self.target_resolution[0]
        height_ratio = self.preview_size[1] / self.target_resolution[1]
        self.scale_factor = min(width_ratio, height_ratio)

        self.min_zoom_factor = self.calculate_min_zoom_factor()

        if self.original_image.width >= self.target_resolution[0] or self.original_image.height >= self.target_resolution[1]:
            self.zoom_factor = self.min_zoom_factor
        else:
            self.zoom_factor = max(self.preview_size[0] / (self.original_image.width * self.scale_factor),
                                   self.preview_size[1] / (self.original_image.height * self.scale_factor))

        self.update_preview_image()

    def calculate_min_zoom_factor(self):
        width_zoom = self.preview_size[0] / \
            (self.original_image.width * self.scale_factor)
        height_zoom = self.preview_size[1] / \
            (self.original_image.height * self.scale_factor)
        return max(width_zoom, height_zoom)

    def update_preview_image(self):
        new_size = (
            int(self.original_image.width * self.scale_factor * self.zoom_factor),
            int(self.original_image.height * self.scale_factor * self.zoom_factor)
        )
        self.preview_image = self.original_image.copy()
        self.preview_image.thumbnail(new_size, Image.Resampling.LANCZOS)
        self.update_photo()

    def update_photo(self):
        self.photo = ImageTk.PhotoImage(self.preview_image)

    def show_image(self):
        if self.image_item:
            self.canvas.delete(self.image_item)

        x = (self.preview_size[0] - self.preview_image.width) // 2
        y = (self.preview_size[1] - self.preview_image.height) // 2
        self.image_item = self.canvas.create_image(
            x, y, image=self.photo, anchor=tk.NW)

        self.canvas.create_rectangle(
            0, 0, self.preview_size[0], self.preview_size[1],
            outline='#8E24AA', width=2
        )

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event):
        if not self.image_item:
            return

        dx = event.x - self.start_x
        dy = event.y - self.start_y

        x, y = self.canvas.coords(self.image_item)

        new_x = x + dx
        new_y = y + dy

        new_x = max(min(new_x, 0),
                    self.preview_size[0] - self.preview_image.width)
        new_y = max(min(new_y, 0),
                    self.preview_size[1] - self.preview_image.height)

        self.canvas.moveto(self.image_item, new_x, new_y)

        self.start_x = event.x
        self.start_y = event.y

    def on_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        self.apply_zoom(1.1)

    def zoom_out(self):
        self.apply_zoom(0.9)

    def apply_zoom(self, factor):
        if not self.original_image:
            return

        new_zoom_factor = self.zoom_factor * factor

        if new_zoom_factor < self.min_zoom_factor:
            new_zoom_factor = self.min_zoom_factor

        if new_zoom_factor != self.zoom_factor:
            self.zoom_factor = new_zoom_factor
            self.update_preview_image()

            x, y = self.canvas.coords(self.image_item)
            center_x = x + self.preview_image.width / 2
            center_y = y + self.preview_image.height / 2

            self.canvas.delete(self.image_item)
            new_x = center_x - self.preview_image.width / 2
            new_y = center_y - self.preview_image.height / 2
            self.image_item = self.canvas.create_image(
                new_x, new_y, image=self.photo, anchor=tk.NW)

            self.constrain_image()

    def constrain_image(self):
        if not self.image_item:
            return

        x, y = self.canvas.coords(self.image_item)

        if self.preview_image.width <= self.preview_size[0]:
            x = (self.preview_size[0] - self.preview_image.width) // 2
        else:
            x = max(min(x, 0), self.preview_size[0] - self.preview_image.width)

        if self.preview_image.height <= self.preview_size[1]:
            y = (self.preview_size[1] - self.preview_image.height) // 2
        else:
            y = max(
                min(y, 0), self.preview_size[1] - self.preview_image.height)

        self.canvas.moveto(self.image_item, x, y)

    def crop_image(self):
        if not self.original_image:
            return None

        x, y = self.canvas.coords(self.image_item)
        crop_area = (
            int(-x / (self.scale_factor * self.zoom_factor)),
            int(-y / (self.scale_factor * self.zoom_factor)),
            int((-x + self.preview_size[0]) /
                (self.scale_factor * self.zoom_factor)),
            int((-y + self.preview_size[1]) /
                (self.scale_factor * self.zoom_factor))
        )

        crop_area = (
            max(0, crop_area[0]),
            max(0, crop_area[1]),
            min(self.original_image.width, crop_area[2]),
            min(self.original_image.height, crop_area[3])
        )

        cropped_image = self.original_image.crop(crop_area)
        cropped_image = cropped_image.resize(
            self.target_resolution, Image.Resampling.LANCZOS)

        return cropped_image


def main():
    root = tk.Tk()
    root.configure(bg='#2C2C2C')
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TButton', background='#6D2A8D',
                    foreground='white', font=('Segoe UI', 10))
    style.map('TButton', background=[('active', '#8B3CB0')])

    # Target resolution (e.g., 1920x1080)
    target_resolution = (1080, 1920)
    preview_size = (450, 800)

    ImageCropper(root, target_resolution, preview_size, style)
    root.mainloop()


if __name__ == "__main__":
    main()
