#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil


def install_deps():
    print("Installing dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True
    )
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)


def clean():
    print("Cleaning previous builds...")
    for dir_name in ["build", "dist", "__pycache__"]:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)


def build():
    print("Building executable...")
    subprocess.run(["pyinstaller", "Cando.spec", "--clean"], check=True)
    print("✅ Build complete! Check dist/Cando.exe")


if __name__ == "__main__":
    try:
        clean()
        install_deps()
        build()
    except Exception as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)
