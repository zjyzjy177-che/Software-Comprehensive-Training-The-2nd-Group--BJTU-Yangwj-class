# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['matplotlib.backends.backend_tkagg', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'peak_shift', 'road_network', 'strategies']
hiddenimports += collect_submodules('assets')


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/campus_map.png', 'assets'), ('assets/SHIJIZHONG_BJTU.jpg', 'assets'), ('campus_bounds.json', '.'), ('assets/picture1.png', 'assets'), ('assets/picture2.png', 'assets'), ('assets/picture3.png', 'assets'), ('assets/picture4.png', 'assets'), ('assets/school_logo.png', 'assets'), ('assets/_cat_gif.py', 'assets'), ('assets/_gif2_data.py', 'assets'), ('assets/_heart_data.py', 'assets'), ('C:/Windows/Fonts/msyh.ttc', '.')],
    hiddenimports=hiddenimports,
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
    name='BJTUCanteenSimulation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icon.ico'],
)
