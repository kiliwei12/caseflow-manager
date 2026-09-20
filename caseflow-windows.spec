# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "desktop_launcher.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / "templates"), "templates")],
    hiddenimports=["waitress", "flask", "jinja2", "werkzeug", "sqlite3"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "setuptools", "pip"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CaseFlow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ROOT / "build_assets" / "CaseFlow.ico"),
)
