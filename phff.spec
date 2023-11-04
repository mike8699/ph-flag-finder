# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

dll_file = next(Path.cwd().rglob('openh*-win64.dll'))

a = Analysis(
    ['phff.py'],
    pathex=[],
    binaries=[],
    datas=[(dll_file, dll_file.name)],
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
