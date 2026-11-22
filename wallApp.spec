# PyInstaller build spec. Analysis, PYZ and EXE are provided by PyInstaller.
# ruff: noqa: F821
# pyright: reportUndefinedVariable=false
import os
import re

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

# Version shown in the exe's Properties > Details. The release workflow sets
# BW_VERSION from the git tag (v1.2 -> 1.2); local builds fall back to 0.0.
_parts = [int(n) for n in re.findall(r'\d+', os.environ.get('BW_VERSION', '0.0'))]
_parts = (_parts + [0, 0, 0, 0])[:4]
_version = '.'.join(str(n) for n in _parts)

# Real version metadata makes the exe look less like anonymous malware to
# antivirus heuristics.
version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=tuple(_parts), prodvers=tuple(_parts)),
    kids=[
        StringFileInfo([StringTable('040904B0', [
            StringStruct('CompanyName', 'snoxlax'),
            StringStruct('FileDescription', 'Better-Walls multi-monitor wallpaper setter'),
            StringStruct('FileVersion', _version),
            StringStruct('InternalName', 'Better-Walls'),
            StringStruct('LegalCopyright', 'MIT License'),
            StringStruct('OriginalFilename', 'Better-Walls.exe'),
            StringStruct('ProductName', 'Better-Walls'),
            StringStruct('ProductVersion', _version),
        ])]),
        VarFileInfo([VarStruct('Translation', [0x0409, 0x04B0])]),
    ],
)

a = Analysis(
    ['wallApp.py'],
    pathex=[],
    binaries=[],
    datas=[('horizon.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Better-Walls',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX-packed exes are a classic malware trait and get flagged far more often.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['horizon.ico'],
    version=version_info,
)
