# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the no-RAG build.

    pyinstaller build.spec --noconfirm

Produces:
    Windows  dist/wx-assist_no_rag.exe
    macOS    dist/wx-assist_no_rag.app
    Linux    dist/wx-assist_no_rag
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(SPECPATH)))

from packaging.pyi_common import collect

plan = collect(SPECPATH, with_rag=False, exe_name="wx-assist_no_rag")
_analysis = plan["analysis"]
_exe = plan["exe"]

a = Analysis(
    _analysis["scripts"],
    pathex=_analysis["pathex"],
    binaries=_analysis["binaries"],
    datas=_analysis["datas"],
    hiddenimports=_analysis["hiddenimports"],
    hookspath=_analysis["hookspath"],
    hooksconfig=_analysis["hooksconfig"],
    runtime_hooks=_analysis["runtime_hooks"],
    excludes=_analysis["excludes"],
    win_no_prefer_redirects=_analysis["win_no_prefer_redirects"],
    win_private_assemblies=_analysis["win_private_assemblies"],
    cipher=_analysis["cipher"],
    noarchive=_analysis["noarchive"],
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    **_exe,
)

if plan["bundle"]:
    app = BUNDLE(exe, **plan["bundle"])
