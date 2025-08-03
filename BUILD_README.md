# Building Cando Windows Executable

This guide explains how to create a lightweight Windows executable (.exe) for the Cando application.

## Quick Start

### Option 1: Automatic Build (Recommended)
```bash
# Windows
build.bat

# Or manually
python build.py
```

### Option 2: Manual Build
```bash
# Install build dependencies
pip install -r requirements_build.txt

# Build using PyInstaller spec file
pyinstaller Cando.spec

# Or build using command line
pyinstaller --onefile --windowed --name=Cando --strip --optimize=2 run.py
```

## Build Features

### 🎯 **Lightweight Optimization**
- **Single executable file** (no installation required)
- **Aggressive module exclusion** (removes unused Python modules)
- **UPX compression** (additional size reduction)
- **Debug symbol stripping** (removes debug information)
- **Python optimization level 2** (removes assertions and docstrings)

### 📦 **What's Included**
- PySide6 Qt framework (GUI)
- Matplotlib (charts and graphs)
- SQLAlchemy (database)
- All application code and assets

### 🚫 **What's Excluded**
- Test modules and documentation
- Unused Python standard library modules
- Development tools and debuggers
- Windows API modules not used by the app

## Expected Results

### File Size
- **Typical size**: 15-25 MB
- **Optimized size**: 10-15 MB (with UPX)
- **Minimal size**: 8-12 MB (with aggressive optimization)

### Performance
- **Startup time**: 2-5 seconds
- **Memory usage**: 50-100 MB
- **CPU usage**: Minimal

## Build Artifacts

After successful build, you'll find:
```
dist/
├── Cando.exe          # Main executable
└── install.bat        # Simple installer script

build/                 # Build cache (can be deleted)
├── Cando/
└── ...

*.spec                 # PyInstaller specification files
```

## Installation Options

### Option 1: Portable
Simply copy `Cando.exe` to any location and run it.

### Option 2: System Installation
Run `install.bat` as administrator to install to Program Files.

### Option 3: Custom Location
Copy `Cando.exe` to your desired folder and create shortcuts.

## Troubleshooting

### Common Issues

#### 1. "Python not found"
- Install Python 3.8+ and add to PATH
- Or use full path: `C:\Python39\python.exe build.py`

#### 2. "PyInstaller not found"
```bash
pip install pyinstaller
```

#### 3. "Missing modules"
```bash
pip install -r requirements.txt
pip install -r requirements_build.txt
```

#### 4. "Large executable size"
- Check if UPX is installed for additional compression
- Review excluded modules in `Cando.spec`
- Consider using `--onedir` instead of `--onefile` for faster startup

#### 5. "Application crashes on startup"
- Check Windows Event Viewer for error details
- Try running with console: remove `--windowed` flag
- Verify all dependencies are included

### Performance Optimization

#### For Faster Startup:
```bash
pyinstaller --onedir --windowed --name=Cando run.py
```

#### For Smaller Size:
```bash
pyinstaller --onefile --windowed --strip --upx-dir=/path/to/upx run.py
```

#### For Debugging:
```bash
pyinstaller --onefile --name=Cando run.py  # Keep console window
```

## Advanced Configuration

### Custom Icon
Place your icon at `app/ui/assets/icon.ico` or modify the spec file.

### Additional Assets
Add to the `datas` section in `Cando.spec`:
```python
datas=[
    ('app/ui/assets', 'app/ui/assets'),
    ('config', 'config'),
    ('data', 'data'),
],
```

### Environment Variables
Set before building:
```bash
set PYTHONOPTIMIZE=2
set PYTHONDONTWRITEBYTECODE=1
```

## Distribution

### For End Users
1. **Portable**: Just the `.exe` file
2. **Installer**: Use `install.bat` or create an MSI
3. **Zipped**: Package with any additional files needed

### For Developers
- Include source code and build scripts
- Document any special requirements
- Provide troubleshooting guide

## Build Environment

### Recommended Setup
- **OS**: Windows 10/11
- **Python**: 3.8-3.11
- **PyInstaller**: 5.13+
- **UPX**: 4.0+ (optional, for compression)

### Dependencies
See `requirements_build.txt` for build-specific dependencies.

## License

This build system is part of the Cando application and follows the same license terms. 