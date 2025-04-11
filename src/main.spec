# -*- mode: python ; coding: utf-8 -*-
import os

# Get the absolute paths
script_path = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.dirname(script_path)
assets_path = os.path.join(script_path, 'assets')

a = Analysis(
    [os.path.join(script_path, 'main.py')],
    pathex=[script_path, project_root],
    binaries=[],
    datas=[
        (os.path.join(assets_path, 'ffmpeg'), 'assets/ffmpeg'),
        (os.path.join(assets_path, 'icon.ico'), 'assets'),
        (os.path.join(assets_path, 'yt-dlp.exe'), 'assets'),
    ],
    hiddenimports=[
        'gui',
        'config',
        'downloader',
        'utils',
        'tkinter',
        'ttkthemes',
        'queue',
        'threading',
        'subprocess',
        'ctypes',
    ],
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
    [],
    exclude_binaries=True,
    name='ADM Video Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Changed from True to False to hide console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(assets_path, 'icon.ico'),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ADM Video Downloader',
)
