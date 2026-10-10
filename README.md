# Better-Walls

A powerful multi-monitor wallpaper manager for Windows that lets you choose and set wallpapers better than the default Windows personalization settings. Perfect for multi-monitor setups with real-time preview.

### Features

- Easily choose and set wallpapers across multiple monitors
- Crop wallpapers to fit your screens
- Save custom wallpaper setups for future use
- Intuitive UI to manage wallpapers better than default settings

- **Automatic monitor detection** - Detects all connected monitors and their positions
- **Visual monitor layout** - See your monitor setup in a scaled preview
- **Per-monitor customization** - Set different images for each monitor
- Continuous development with new features planned

### How to Use

1. **Launch the app** - It will automatically detect your monitors
2. **Click any monitor** - Select an image and crop it to fit perfectly
3. **See instant results** - Your wallpaper updates immediately
4. **Repeat for other monitors** - Each monitor can have its own image
5. **Save when ready** - Use "Assemble Wallpaper" to save a permanent version

### Image Handling

- **Real-time cropping** - Interactive image cropper with pan, zoom, and precise selection
- **Smart image processing** - Handles RGBA/transparency automatically
- **Format support** - Works with JPEG, PNG, and other common formats
- **High-quality resizing** - Uses LANCZOS resampling for crisp results

### Real-Time Experience

- **Instant preview** - See wallpaper changes immediately as you crop
- **Caching** - Remembers your last selections between app sessions
- **Persistent sessions** - Your monitor configurations are saved automatically
- **Silent operation** - No annoying popups, just smooth workflow

### User Experience

- **Dynamic sizing** - Automatically fits your monitor layout
- **Click-to-change** - Click any monitor to instantly change its wallpaper
- **One-click assembly** - Generate final wallpaper with all your selections

### The code

#### Prerequisites

- Python 3.7+ installed
- Windows 10/11 (uses Windows-specific APIs)

#### Installation

```bash
# Clone the repository
git clone https://github.com/snoxlax/Better-Walls
cd Better-Walls

# Install dependencies
pip install pillow

# Run the app
python wallApp.py
```

#### Creating an Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed wallApp.py

# Run the generated .exe
cd dist
wallApp.exe
```

#### Architecture

- **Main app**: `wallApp.py` - Orchestrates the entire application
- **Monitor detection**: `screenInfo.py` - Uses Windows APIs to enumerate displays
- **Image cropping**: `imageCrop.py` - Interactive cropping with pan/zoom
- **Caching system**: Automatic persistence in `%LOCALAPPDATA%\Better-Walls\cache`

#### Key Features

- **Virtual desktop mapping** - Handles negative coordinates and mixed DPI
- **Atomic file operations** - Prevents corrupted cache files
- **Registry integration** - Sets proper Windows wallpaper styles
- **Error handling** - Graceful fallbacks for edge cases

#### Project Structure

```
Better-Walls/
├── wallApp.py          # Main application
├── imageCrop.py        # Image cropping widget
├── screenInfo.py       # Monitor detection
├── README.md           # This file
├── horizon.ico         # App icon
└── horizon.svg         # App icon source
```

#### Requirements

- Python 3.7+
- Pillow (PIL)
- tkinter (included with Python)
- Windows 10/11

#### Key Dependencies

```python
from PIL import Image, ImageTk
import tkinter as tk
import ctypes
import winreg
```

### Use Cases

- **Gaming setups** - Different wallpapers for gaming monitors
- **Workstations** - Professional wallpapers for productivity
- **Art displays** - Showcase different artwork across screens
- **Content creation** - Visual inspiration across multiple displays

### Contributing

Feel free to fork this repository and make your own improvements! Pull requests are welcome.

### Development Ideas

- Preset wallpaper collections
- more...

### 📄 License

This project is licensed under the MIT License.

---

**Better-Walls** - Because your multi-monitor setup deserves better wallpaper management! 🎨
