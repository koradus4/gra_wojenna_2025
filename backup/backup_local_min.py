#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimalny lokalny backup do C:\\Users\\klif\\gra+wojenna15082025
Kopiuje cały katalog projektu (bez .git, __pycache__, *.pyc, logs) do docelowego folderu.
"""
import os, shutil, sys
from pathlib import Path

EXCLUDES = {'.git', '__pycache__', '.vscode', 'logs'}
EXCLUDE_SUFFIX = {'.pyc', '.pyo', '.log', '.tmp'}

def should_skip(p: Path):
    name = p.name
    if name in EXCLUDES: return True
    for suf in EXCLUDE_SUFFIX:
        if name.endswith(suf):
            return True
    return False

def main():
    project_root = Path(__file__).parent.parent
    target_root = Path(r"C:\Users\klif\gra+wojenna15082025")
    target_root.mkdir(parents=True, exist_ok=True)
    print(f"➡️ Kopiuję z {project_root} do {target_root}")
    for src in project_root.rglob('*'):
        rel = src.relative_to(project_root)
        if any(part in EXCLUDES for part in rel.parts):
            continue
        if should_skip(src):
            continue
        dest = target_root / rel
        if src.is_dir():
            dest.mkdir(exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src, dest)
            except Exception as e:
                print(f"⚠️ {rel}: {e}")
    print("✅ Backup lokalny zakończony")

if __name__ == '__main__':
    main()
