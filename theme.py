"""Shared look for Better-Walls: the dusk palette from the horizon icon."""
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageDraw

# Palette (derived from horizon.svg)
BG = '#0F1419'          # window ground (icon backdrop navy)
DESK = '#0B0F13'        # monitor map surface, a step darker than the window
PANEL = '#161E27'       # raised surfaces: empty monitor panes, bars
PANEL_HOVER = '#1B2531'
LINE = '#263241'        # hairlines and borders
LINE_STRONG = '#3A4A5E'
TEXT = '#E8ECF1'
TEXT_DIM = '#8C98A9'
ACCENT = '#F28C5B'      # sunset: primary action, hover, focus
ACCENT_HOVER = '#F6A47C'
ACCENT_PRESSED = '#D9774A'
ON_ACCENT = '#14100D'
SUN = '#FFD27A'         # sun gold: primary-display mark only

FONT = 'Segoe UI'
FONT_SEMI = 'Segoe UI Semibold'


def apply_theme(root: tk.Tk | tk.Toplevel) -> ttk.Style:
    """Configure ttk styles once for the whole app"""
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use('clam')

    style.configure('.', background=BG, foreground=TEXT, font=(FONT, 10),
                    bordercolor=LINE, lightcolor=BG, darkcolor=BG,
                    focuscolor=ACCENT, troughcolor=PANEL)
    style.configure('TFrame', background=BG)
    style.configure('Bar.TFrame', background=PANEL)
    style.configure('TLabel', background=BG, foreground=TEXT)
    style.configure('Title.TLabel', font=(FONT_SEMI, 15))
    style.configure('Dim.TLabel', foreground=TEXT_DIM)
    style.configure('Bar.TLabel', background=PANEL, foreground=TEXT)
    style.configure('BarDim.TLabel', background=PANEL, foreground=TEXT_DIM)
    style.configure('BarTitle.TLabel', background=PANEL, foreground=TEXT,
                    font=(FONT_SEMI, 11))

    # Buttons: flat fills, no bevels; clam draws the border from these colors
    button_font = (FONT_SEMI, 10)
    button_padding = (16, 7)
    style.configure('Primary.TButton', background=ACCENT, foreground=ON_ACCENT,
                    bordercolor=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT,
                    focuscolor=ON_ACCENT, borderwidth=1, relief='flat',
                    padding=button_padding, font=button_font, focusthickness=1)
    style.map('Primary.TButton',
              background=[('pressed', ACCENT_PRESSED), ('active', ACCENT_HOVER),
                          ('disabled', LINE)],
              bordercolor=[('pressed', ACCENT_PRESSED), ('active', ACCENT_HOVER),
                           ('disabled', LINE)],
              lightcolor=[('pressed', ACCENT_PRESSED), ('active', ACCENT_HOVER),
                          ('disabled', LINE)],
              darkcolor=[('pressed', ACCENT_PRESSED), ('active', ACCENT_HOVER),
                         ('disabled', LINE)],
              foreground=[('disabled', TEXT_DIM)])

    for name, ground in (('Ghost.TButton', BG), ('BarGhost.TButton', PANEL)):
        style.configure(name, background=ground, foreground=TEXT,
                        bordercolor=LINE_STRONG, lightcolor=ground,
                        darkcolor=ground, borderwidth=1, relief='solid',
                        padding=button_padding, font=button_font,
                        focusthickness=1)
        style.map(name,
                  background=[('pressed', LINE), ('active', PANEL_HOVER)],
                  lightcolor=[('pressed', LINE), ('active', PANEL_HOVER)],
                  darkcolor=[('pressed', LINE), ('active', PANEL_HOVER)],
                  bordercolor=[('focus', ACCENT), ('active', TEXT_DIM)])
    style.map('Primary.TButton', focuscolor=[('focus', ON_ACCENT)])
    return style


def round_rect_points(x1, y1, x2, y2, r):
    """Point list for a smooth-polygon rounded rectangle on a tk.Canvas"""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]


def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r=8, **kw):
    return canvas.create_polygon(round_rect_points(x1, y1, x2, y2, r),
                                 smooth=True, **kw)


def rounded_image(image: Image.Image, radius: int, ground: str) -> Image.Image:
    """Round an image's corners, flattening the cut corners onto `ground`"""
    image = image.convert('RGB')
    scale = 4  # supersample the mask for smooth corners
    w, h = image.size
    mask = Image.new('L', (w * scale, h * scale), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, w * scale - 1, h * scale - 1), radius * scale, fill=255)
    mask = mask.resize((w, h), Image.Resampling.LANCZOS)
    out = Image.new('RGB', (w, h), ground)
    out.paste(image, (0, 0), mask)
    return out
