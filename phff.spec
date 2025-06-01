# -*- mode: python ; coding: utf-8 -*-

import os
import site
from pathlib import Path

datas = []
binaries = []

shared_lib = 'libdesmume.' 
if os.name == 'nt':
    shared_lib += 'dll'
elif os.name == 'posix':
    shared_lib += 'so'
else:
    raise RuntimeError(f'Unsupported OS: {os.name}')

# For some reason, pyinstaller doesn't pick up one of the DLLs
# needed for py-desmume, so we manually bundle it here
site_packages_dir = Path(site.getsitepackages()[0])
desmume_dll_file = next(site_packages_dir.rglob(shared_lib))
binaries += [
    (desmume_dll_file, 'desmume')
]

# Bundle external dll needed for opencv-python.
# Only needed on Windows
if os.name == 'nt':
    openh_dll_file = next(Path.cwd().rglob('openh*-win64.dll'))
    datas += [
        (openh_dll_file, '.'),
    ]

a = Analysis(
    ['phff.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='phff',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
