# Better-Walls

I created a wallpaper app that lets you choose and set wallpapers better than the Windows personalization settings. It allows you to crop and set wallpapers, and it's mainly aimed at multi-monitor setups. You can even save configurations for later use. I plan to implement more features and refine the app further. I originally made this app for personal use, and I think it’s way better.

## Features

- Easily choose and set wallpapers across multiple monitors
- Crop wallpapers to fit your screens
- Save custom wallpaper setups for future use
- Intuitive UI to manage wallpapers better than default settings
- Continuous development with new features planned

## Installation

### Prerequisites

Before you can run WallApp, ensure that you have Python installed. If you haven't installed Python yet, download it from [python.org](https://www.python.org/downloads/). Ensure `pip` is installed and updated:

```bash
python -m ensurepip --upgrade
```

### Running the App

To run the app from the source code, clone this repository and install any dependencies (if required):

```bash
git clone https://github.com/snoxlax/Better-Walls
cd Better-Walls
```

Then, run the app using Python:

```bash
python wallApp.py
```

### Creating an Executable (Windows)

To turn `wallApp.py` into an executable for easy distribution, follow these steps using `PyInstaller`:

1. First, install `PyInstaller` if you don't have it:

```bash
pip install pyinstaller
```

2. Once installed, navigate to the directory where `wallApp.py` is located and run the following command:

```bash
pyinstaller --onefile --windowed wallApp.py
```

This command will package your app into a single executable file without the console window popping up. The executable will be located in the `dist` folder.

3. To run the generated `.exe`, navigate to the `dist` folder:

```bash
cd dist
wallApp.exe
```

Now, you can distribute the executable file without requiring users to install Python.

## Future Plans

- soon

## Contributing

Feel free to fork this repository and make your own improvements. Pull requests are welcome!

## License

This project is licensed under the MIT License.
