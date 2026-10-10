import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageOps, ImageTk

IMAGE_FILETYPES = [
    ("Images", "*.jpg *.jpeg *.png *.bmp *.gif *.webp *.tif *.tiff"),
    ("All files", "*.*"),
]


def load_image(file_path):
    """Open an image fully into memory (so the file isn't locked), applying EXIF rotation"""
    with Image.open(file_path) as img:
        image = ImageOps.exif_transpose(img)
        image.load()
    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGBA')
    return image


class ImageCropper:
    def __init__(self, master, target_resolution, preview_size, style):
        self.master = master
        self.target_resolution = target_resolution
        self.preview_size = (int(preview_size[0]), int(preview_size[1]))
        self.style = style
        self.master.title(
            f"Image Cropper - Target: {target_resolution[0]}x{target_resolution[1]}")

        self.original_image = None
        self.image_item = None
        self.scale_factor = 1
        self.zoom_factor = 1
        self.min_zoom_factor = 1
        # Position of the (virtually) scaled image's top-left corner on the canvas
        self.offset_x = 0
        self.offset_y = 0
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
        """Load an image into the cropper. Returns True on success."""
        if not file_path:
            file_path = filedialog.askopenfilename(
                parent=self.master, filetypes=IMAGE_FILETYPES)
        if not file_path:
            return False
        try:
            self.original_image = load_image(file_path)
        except (OSError, Image.DecompressionBombError) as e:
            messagebox.showerror(
                "Can't open image", f"{file_path}\n\n{e}", parent=self.master)
            return False
        self.create_preview_image()
        return True

    def create_preview_image(self):
        width_ratio = self.preview_size[0] / self.target_resolution[0]
        height_ratio = self.preview_size[1] / self.target_resolution[1]
        self.scale_factor = min(width_ratio, height_ratio)

        self.min_zoom_factor = self.calculate_min_zoom_factor()
        self.zoom_factor = self.min_zoom_factor

        # Center the image in the preview
        width, height = self.scaled_size()
        self.offset_x = (self.preview_size[0] - width) / 2
        self.offset_y = (self.preview_size[1] - height) / 2
        self.render()

    def calculate_min_zoom_factor(self):
        width_zoom = self.preview_size[0] / \
            (self.original_image.width * self.scale_factor)
        height_zoom = self.preview_size[1] / \
            (self.original_image.height * self.scale_factor)
        return max(width_zoom, height_zoom)

    def effective_scale(self):
        return self.scale_factor * self.zoom_factor

    def scaled_size(self):
        scale = self.effective_scale()
        return self.original_image.width * scale, self.original_image.height * scale

    def visible_box(self):
        """Region of the original image currently shown in the preview"""
        scale = self.effective_scale()
        left = -self.offset_x / scale
        top = -self.offset_y / scale
        right = min(left + self.preview_size[0] / scale, self.original_image.width)
        bottom = min(top + self.preview_size[1] / scale, self.original_image.height)
        return (max(0, left), max(0, top), right, bottom)

    def render(self):
        """Draw only the visible part of the image, scaled to the preview size"""
        preview = self.original_image.resize(
            self.preview_size, Image.Resampling.LANCZOS,
            box=self.visible_box(), reducing_gap=2.0)
        self.photo = ImageTk.PhotoImage(preview)

        if self.image_item:
            self.canvas.itemconfigure(self.image_item, image=self.photo)
        else:
            self.image_item = self.canvas.create_image(
                0, 0, image=self.photo, anchor=tk.NW)
            self.canvas.create_rectangle(
                0, 0, self.preview_size[0], self.preview_size[1],
                outline='#8E24AA', width=2
            )

    def constrain_offset(self):
        """Keep the image covering the whole preview"""
        width, height = self.scaled_size()
        self.offset_x = max(min(self.offset_x, 0), self.preview_size[0] - width)
        self.offset_y = max(min(self.offset_y, 0), self.preview_size[1] - height)

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event):
        if not self.original_image:
            return

        self.offset_x += event.x - self.start_x
        self.offset_y += event.y - self.start_y
        self.constrain_offset()
        self.render()

        self.start_x = event.x
        self.start_y = event.y

    def on_mousewheel(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.apply_zoom(factor, event.x, event.y)

    def zoom_in(self):
        self.apply_zoom(1.1)

    def zoom_out(self):
        self.apply_zoom(0.9)

    def apply_zoom(self, factor, anchor_x=None, anchor_y=None):
        """Zoom keeping the point under (anchor_x, anchor_y) fixed; defaults to preview center"""
        if not self.original_image:
            return

        new_zoom_factor = max(self.zoom_factor * factor, self.min_zoom_factor)
        if new_zoom_factor == self.zoom_factor:
            return

        if anchor_x is None:
            anchor_x = self.preview_size[0] / 2
        if anchor_y is None:
            anchor_y = self.preview_size[1] / 2

        old_scale = self.effective_scale()
        image_x = (anchor_x - self.offset_x) / old_scale
        image_y = (anchor_y - self.offset_y) / old_scale

        self.zoom_factor = new_zoom_factor
        new_scale = self.effective_scale()
        self.offset_x = anchor_x - image_x * new_scale
        self.offset_y = anchor_y - image_y * new_scale

        self.constrain_offset()
        self.render()

    def crop_image(self):
        if not self.original_image:
            return None

        return self.original_image.resize(
            self.target_resolution, Image.Resampling.LANCZOS, box=self.visible_box())


def main():
    root = tk.Tk()
    root.configure(bg='#2C2C2C')
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TButton', background='#6D2A8D',
                    foreground='white', font=('Segoe UI', 10))
    style.map('TButton', background=[('active', '#8B3CB0')])

    target_resolution = (1080, 1920)
    preview_size = (450, 800)

    ImageCropper(root, target_resolution, preview_size, style)
    root.mainloop()


if __name__ == "__main__":
    main()
