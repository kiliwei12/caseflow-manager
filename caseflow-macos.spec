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
    [],
    exclude_binaries=True,
    name="CaseFlow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(ROOT / "build_assets" / "CaseFlow.icns"),
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="CaseFlow")
app = BUNDLE(
    coll,
    name="CaseFlow.app",
    icon=str(ROOT / "build_assets" / "CaseFlow.icns"),
    bundle_identifier="com.caseflow.manager",
    info_plist={
        "CFBundleDisplayName": "CaseFlow",
        "CFBundleShortVersionString": "1.1.0",
        "CFBundleVersion": "1.1.0",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
    },
)
