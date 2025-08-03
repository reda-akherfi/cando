#!/usr/bin/env python3
"""
Build script for creating a lightweight Windows executable of the Cando application.

This script uses PyInstaller with optimizations to create a minimal executable.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build():
    """Clean previous build artifacts."""
    print("🧹 Cleaning previous build artifacts...")

    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")

    # Clean .spec files (but keep Cando.spec)
    for spec_file in Path(".").glob("*.spec"):
        if spec_file.name != "Cando.spec":
            spec_file.unlink()
            print(f"   Removed {spec_file}")


def check_upx():
    """Check if UPX is available for additional compression."""
    upx_path = shutil.which("upx")
    if upx_path:
        print(f"✅ UPX found at: {upx_path}")
        print("   Will use UPX compression for smaller executable size")
        return True
    else:
        print("⚠️  UPX not found in PATH")
        print("   Executable will be larger but will still work")
        print("   To install UPX: download from https://upx.github.io/")
        return False


def install_dependencies():
    """Install required build dependencies."""
    print("📦 Installing build dependencies...")

    dependencies = ["pyinstaller>=5.13.0", "pyinstaller-hooks-contrib>=2023.0"]

    for dep in dependencies:
        print(f"   Installing {dep}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"   Warning: Failed to install {dep}: {e}")
            print("   Continuing anyway...")


def create_executable():
    """Create the executable using PyInstaller."""
    print("🔨 Creating executable...")

    # Use the spec file for more reliable builds
    cmd = [
        "pyinstaller",
        "Cando.spec",
        "--clean",  # Clean cache before building
    ]

    print("   Running PyInstaller...")
    print(f"   Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Executable created successfully!")
        print(f"📁 Location: dist/Cando.exe")

        # Get file size
        exe_path = Path("dist/Cando.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📏 Size: {size_mb:.1f} MB")

            if size_mb > 50:
                print("⚠️  Executable is quite large. Consider:")
                print("   - Installing UPX for compression")
                print("   - Using --onedir instead of --onefile")
        else:
            print("❌ Executable not found in dist/")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print("❌ Failed to create executable")
        print(f"Error: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        sys.exit(1)


def create_installer():
    """Create an MSI installer using WiX Toolset (optional)."""
    print("📦 Creating MSI installer...")

    # This would require WiX Toolset to be installed
    # For now, we'll just create a simple batch installer
    create_batch_installer()


def create_batch_installer():
    """Create a simple batch file installer."""
    print("📦 Creating batch installer...")

    installer_content = """@echo off
echo Installing Cando...
echo.

REM Create installation directory
set INSTALL_DIR=%PROGRAMFILES%\\Cando
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy executable
copy "Cando.exe" "%INSTALL_DIR%\\Cando.exe"

REM Create desktop shortcut
set DESKTOP=%USERPROFILE%\\Desktop
echo @echo off > "%DESKTOP%\\Cando.bat"
echo cd /d "%INSTALL_DIR%" >> "%DESKTOP%\\Cando.bat"
echo start Cando.exe >> "%DESKTOP%\\Cando.bat"

echo.
echo Installation complete!
echo You can now run Cando from your desktop or start menu.
pause
"""

    with open("install.bat", "w") as f:
        f.write(installer_content)

    print("   Created install.bat")


def main():
    """Main build process."""
    print("🚀 Starting Cando build process...")
    print("=" * 50)

    try:
        # Step 1: Clean previous builds
        clean_build()
        print()

        # Step 2: Check UPX availability
        check_upx()
        print()

        # Step 3: Install dependencies
        install_dependencies()
        print()

        # Step 4: Create executable
        create_executable()
        print()

        # Step 5: Create installer
        create_installer()
        print()

        print("🎉 Build completed successfully!")
        print("=" * 50)
        print("📁 Files created:")
        print("   - dist/Cando.exe (main executable)")
        print("   - install.bat (simple installer)")
        print()
        print("💡 To install:")
        print("   1. Copy Cando.exe to your desired location")
        print("   2. Or run install.bat as administrator")
        print()
        print("🔧 Troubleshooting:")
        print("   - If executable is too large: install UPX")
        print("   - If it doesn't run: check Windows Event Viewer")
        print("   - For debugging: remove --windowed from spec file")

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
