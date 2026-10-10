import ctypes
import datetime
import os
import threading
import winreg
from pathlib import Path

from PIL import Image, UnidentifiedImageError


class WallpaperService:
    def __init__(self):
        self.last_save_dir = None
        self.last_open_dir = None

    def _ensure_rgb(self, image):
        """Convert image to RGB format if needed"""
        if image.mode == 'RGB':
            return image

        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            rgba = image.convert('RGBA')
            background = Image.new('RGB', rgba.size, (0, 0, 0))
            background.paste(rgba, mask=rgba.split()[3])
            return background
        return image.convert('RGB')

    def get_cache_dir(self):
        """Get the cache directory for storing temporary files"""
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

    def cache_path_for_monitor(self, monitor):
        """Get cache file path for a specific monitor"""
        left = monitor['Left']
        top = monitor['Top']
        right = monitor['Right']
        bottom = monitor['Bottom']
        filename = f"{left}_{top}_{right}_{bottom}.jpg"
        return self.get_cache_dir() / filename

    def save_crop_to_cache(self, monitor, image):
        """Save cropped image to cache"""
        try:
            path = self.cache_path_for_monitor(monitor)
            rgb = self._ensure_rgb(image)
            tmp_path = path.with_suffix(path.suffix + ".tmp")

            rgb.save(tmp_path, format='JPEG', quality=90)
            os.replace(tmp_path, path)
        except OSError as e:
            print(f"Failed to save cache image: {e}")

    def load_crop_from_cache(self, monitor):
        """Load cropped image from cache"""
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

    def create_temp_wallpaper(self, monitors, cropped_images, bounds):
        """Create a temporary assembled wallpaper with current crops and set it immediately"""
        if not cropped_images:
            return

        try:
            min_x, min_y, max_x, max_y = bounds
            assembled_image = Image.new('RGB', (max_x - min_x, max_y - min_y))

            for monitor in monitors:
                if monitor['Handle'] in cropped_images:
                    image = cropped_images[monitor['Handle']]
                    if image.mode != 'RGB':
                        image = self._ensure_rgb(image)
                    assembled_image.paste(
                        image, (monitor['Left'] - min_x, monitor['Top'] - min_y))

            temp_dir = self.get_cache_dir() / "temp"
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / "current_wallpaper.jpg"
            assembled_image.save(temp_path, format='JPEG', quality=90)

            self.set_wallpaper_async(str(temp_path))
        except (OSError, ValueError) as e:
            print(f"Failed to create temp wallpaper: {e}")

    def assemble_wallpaper(self, monitors, cropped_images, bounds, save_path=None):
        """Assemble the final wallpaper and optionally save it"""
        if not cropped_images:
            return None

        min_x, min_y, max_x, max_y = bounds
        assembled_image = Image.new('RGB', (max_x - min_x, max_y - min_y))

        for monitor in monitors:
            if monitor['Handle'] in cropped_images:
                image = cropped_images[monitor['Handle']]
                if image.mode != 'RGB':
                    image = self._ensure_rgb(image)
                assembled_image.paste(
                    image, (monitor['Left'] - min_x, monitor['Top'] - min_y))

        # Always create a temp file and set as wallpaper
        temp_dir = self.get_cache_dir() / "temp"
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / "assembled_wallpaper.jpg"
        assembled_image.save(temp_path, format='JPEG', quality=90)
        self.set_wallpaper_async(str(temp_path))

        # If user chose a save path, also save there
        if save_path:
            assembled_image.save(save_path)
            print(f"Assembled wallpaper saved to: {save_path}")
            self.last_save_dir = os.path.dirname(save_path)

        return assembled_image

    def set_wallpaper(self, image_path):
        """Set the wallpaper using Windows registry and system parameters"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "22")
            winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
            winreg.CloseKey(key)

            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
            ctypes.windll.user32.UpdatePerUserSystemParameters(1)
        except (OSError, PermissionError, FileNotFoundError) as e:
            print(f"Failed to set wallpaper: {e}")

    def set_wallpaper_async(self, image_path):
        """Run wallpaper change in a background thread"""
        def set_wallpaper_with_delay():
            import time
            time.sleep(0.1)  # Small delay to ensure file is fully written
            self.set_wallpaper(image_path)

        thread = threading.Thread(target=set_wallpaper_with_delay, daemon=True)
        thread.start()

    def generate_filename(self):
        """Generate a filename with current date and time"""
        current_date_time = datetime.datetime.now().strftime("%d-%m-%y_%H-%M-%S")
        file_name = "Full_Wallpaper"
        return f"{file_name}_{current_date_time}.jpg"
