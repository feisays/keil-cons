#!/usr/bin/env python3
"""Keil uVision 命令行工具构建脚本 — 一键生成可执行文件。

用法:
    python build.py
"""

import os
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SPEC_FILE = os.path.join(SCRIPT_DIR, "keil_cons.spec")
ENTRY_FILE = os.path.join(SCRIPT_DIR, "keil_cons.py")
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")
DIST_DIR = os.path.join(SCRIPT_DIR, "dist")


def check_pyinstaller():
    """检查 PyInstaller 是否可用，不可用则提示安装并退出。"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"[检查] PyInstaller {result.stdout.strip()}")
            return
    except Exception:
        pass
    print("[错误] 未找到 PyInstaller。")
    print("请运行: pip install pyinstaller")
    sys.exit(1)


def clean():
    """清理旧的构建产物。"""
    for d in (BUILD_DIR, DIST_DIR):
        if os.path.isdir(d):
            shutil.rmtree(d)
            print(f"[清理] 已删除 {os.path.relpath(d, SCRIPT_DIR)}/")


def build():
    """调用 PyInstaller 执行构建。"""
    if os.path.isfile(SPEC_FILE):
        print(f"\n[构建] pyinstaller {os.path.relpath(SPEC_FILE, SCRIPT_DIR)}")
        cmd = [sys.executable, "-m", "PyInstaller", SPEC_FILE]
    else:
        if not os.path.isfile(ENTRY_FILE):
            print(f"\n[失败] 未找到构建入口: {ENTRY_FILE}")
            sys.exit(1)
        print("\n[提示] 未找到 keil_cons.spec，改为直接打包 keil_cons.py")
        print(f"[构建] pyinstaller --clean --noconfirm --onefile --name keil_cons {os.path.relpath(ENTRY_FILE, SCRIPT_DIR)}")
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--onefile",
            "--name",
            "keil_cons",
            ENTRY_FILE,
        ]

    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    if result.returncode != 0:
        print(f"\n[失败] PyInstaller 退出码: {result.returncode}")
        sys.exit(result.returncode)


def report():
    """报告构建结果。"""
    exe_name = "keil_cons.exe" if sys.platform == "win32" else "keil_cons"
    exe_path = os.path.join(DIST_DIR, exe_name)

    if not os.path.isfile(exe_path):
        print(f"\n[失败] 未找到构建产物: {exe_path}")
        sys.exit(1)

    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print(f"\n{'=' * 50}")
    print(f"  构建成功!")
    print(f"  产物: {os.path.relpath(exe_path, SCRIPT_DIR)}")
    print(f"  大小: {size_mb:.1f} MB")
    print(f"{'=' * 50}")


def main():
    print("=" * 50)
    print("  Keil uVision 命令行工具 — 构建脚本")
    print("=" * 50)

    check_pyinstaller()
    clean()
    build()
    report()


if __name__ == "__main__":
    main()
