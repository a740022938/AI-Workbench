# Troubleshooting Guide for AI Vision Data & Training Workbench

Common issues and solutions for Windows 11 users.

## Before You Begin

1. **Run commands as Administrator** if you encounter permission errors
2. **Check the terminal/command prompt** for error messages
3. **Verify each step** before moving to the next

---

## Python Issues

### Issue: "Python is not recognized as an internal or external command"
**Cause**: Python not installed or not in PATH

**Solutions**:
1. **Reinstall Python** from [python.org](https://python.org/downloads/)
   - During installation, CHECK "Add Python to PATH"
   - Choose "Customize installation" if option appears
2. **Add Python to PATH manually**:
   - Press Win + X → System → Advanced system settings
   - Environment Variables → System variables → Path → Edit
   - Add: `C:\Users\[YourUsername]\AppData\Local\Programs\Python\Python311\` (adjust version)
   - Add: `C:\Users\[YourUsername]\AppData\Local\Programs\Python\Python311\Scripts\`
3. **Use Python from Microsoft Store** (simpler):
   - Open Microsoft Store → Search "Python" → Install

### Issue: "pip is not recognized"
**Cause**: pip not installed or not in PATH

**Solutions**:
1. **Ensure Python installed correctly** (see above)
2. **Install pip manually**:
   ```cmd
   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   python get-pip.py
   ```
3. **Use python -m pip instead**:
   ```cmd
   python -m pip install -r requirements.txt
   ```

---

## Dependency Installation Issues

### Issue: "No module named 'PIL'"
**Cause**: Pillow not installed

**Solutions**:
1. **Install Pillow**:
   ```cmd
   pip install Pillow
   ```
2. **Upgrade Pillow** (if already installed):
   ```cmd
   pip install --upgrade Pillow
   ```
3. **Install with specific version**:
   ```cmd
   pip install Pillow==10.0.0
   ```

### Issue: "No module named 'torch'"
**Cause**: PyTorch not installed

**Solutions**:
1. **Install PyTorch CPU version**:
   ```cmd
   pip install torch torchvision
   ```
2. **Install PyTorch with CUDA** (NVIDIA GPU):
   ```cmd
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```
3. **Install from official site** if pip fails:
   - Visit [pytorch.org](https://pytorch.org/)
   - Select your configuration
   - Copy and run the pip command

### Issue: "No module named 'ultralytics'"
**Cause**: YOLO framework not installed

**Solutions**:
1. **Install ultralytics**:
   ```cmd
   pip install ultralytics
   ```
2. **Install specific version**:
   ```cmd
   pip install ultralytics==8.0.0
   ```

### Issue: "Dependency conflicts"
**Cause**: Multiple versions conflicting

**Solutions**:
1. **Create fresh virtual environment**:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Upgrade pip first**:
   ```cmd
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **Install without dependencies** (last resort):
   ```cmd
   pip install Pillow torch ultralytics opencv-python numpy pyyaml tqdm
   ```

---

## Tkinter Issues

### Issue: "No module named 'tkinter'"
**Cause**: Tkinter not included in Python installation

**Solutions**:
1. **Reinstall Python** with Tkinter:
   - Use python.org installer (not Microsoft Store)
   - During installation, check "tcl/tk and IDLE"
2. **Install Tkinter separately**:
   - Download from: [tkinter installation guide](https://tkdocs.com/tutorial/install.html)
3. **Use existing Tkinter** (Windows usually has it):
   ```python
   import tkinter
   print(tkinter.TkVersion)
   ```

### Issue: "TclError: Can't find a usable init.tcl"
**Cause**: Tcl/Tk installation corrupted

**Solutions**:
1. **Repair Python installation**
2. **Copy Tcl/Tk files manually**:
   - From: `C:\Users\[YourUsername]\AppData\Local\Programs\Python\Python311\tcl\`
   - To application directory
3. **Set TCL_LIBRARY environment variable**:
   ```cmd
   set TCL_LIBRARY=C:\Users\[YourUsername]\AppData\Local\Programs\Python\Python311\tcl\tcl8.6
   ```

---

## Configuration Issues

### Issue: "config.json not found"
**Cause**: Configuration file missing

**Solutions**:
1. **Copy example config**:
   ```cmd
   copy config.example.json config.json
   ```
2. **Create manually** if copy fails:
   - Open Notepad
   - Copy contents from `config.example.json`
   - Save as `config.json` (select "All files" type)
3. **Check file exists**:
   ```cmd
   dir config.json
   ```

### Issue: "Invalid JSON in config.json"
**Cause**: Configuration file corrupted

**Solutions**:
1. **Delete and recreate**:
   ```cmd
   del config.json
   copy config.example.json config.json
   ```
2. **Validate JSON**:
   ```cmd
   python -m json.tool config.json
   ```
3. **Use default settings**:
   - Delete `config.json`
   - Launch application (it will create default)

---

## Application Launch Issues

### Issue: "Application starts then closes immediately"
**Cause**: Critical error during startup

**Solutions**:
1. **Run from command prompt** to see error
2. **Check logs**:
   - Look for `logs/startup_error.log`
   - Check Windows Event Viewer
3. **Disable problematic features**:
   - Edit `config.json` → Set `"enable_openclaw": false`
   - Set `"auto_infer_on_open": false`

### Issue: "ImportError: No module named 'config'"
**Cause**: Python package structure issue

**Solutions**:
1. **Run from project root directory**
2. **Add current directory to Python path**:
   ```cmd
   python -c "import sys; sys.path.insert(0, '.'); from main import main; main()"
   ```
3. **Check __init__.py files exist**:
   ```cmd
   dir config\__init__.py
   dir utils\__init__.py
   ```

### Issue: "MemoryError" or "Out of memory"
**Cause**: Insufficient RAM for large images/models

**Solutions**:
1. **Reduce image size** in config.json:
   ```json
   "model": {
     "imgsz": 320
   }
   ```
2. **Close other applications**
3. **Use smaller batch size**:
   ```json
   "training": {
     "batch_size": 8
   }
   ```

### Issue: "Permission denied" errors
**Cause**: Insufficient file permissions

**Solutions**:
1. **Run as Administrator**
2. **Change folder permissions**:
   - Right-click project folder → Properties → Security
   - Add your user with Full Control
3. **Run from user directory** (not Program Files)

---

## GUI Issues

### Issue: "Window appears but is blank/empty"
**Cause**: UI initialization issue

**Solutions**:
1. **Wait 10-20 seconds** (first-time initialization)
2. **Click "File" → "Open Image Folder"**
3. **Restart application**
4. **Change UI theme** in Settings → Appearance

### Issue: "Buttons don't work" or "UI frozen"
**Cause**: Event loop blocked

**Solutions**:
1. **Close and restart**
2. **Check for console error messages**
3. **Disable OpenClaw integration** if enabled
4. **Reduce system load** (close other programs)

### Issue: "Text appears as squares or gibberish"
**Cause**: Font/encoding issue

**Solutions**:
1. **Change language** to English in Settings
2. **Install Chinese fonts** (if using Chinese UI)
3. **Use default system font** in UI settings

---

## Performance Issues

### Issue: "Application is very slow"
**Cause**: Resource constraints or configuration

**Solutions**:
1. **Reduce image size** in config.json
2. **Disable auto-inference**:
   ```json
   "inference": {
     "auto_infer_on_open": false
   }
   ```
3. **Use CPU instead of GPU** (if GPU is causing issues)
4. **Increase virtual memory**:
   - System Properties → Advanced → Performance Settings
   - Advanced → Virtual Memory → Change

### Issue: "Training takes forever"
**Cause**: Hardware limitations or configuration

**Solutions**:
1. **Reduce batch size** (8 or 16 instead of 32)
2. **Use smaller model** (yolo26n instead of yolo26x)
3. **Train fewer epochs** (50 instead of 100)
4. **Use GPU** if available (install CUDA version)

---

## Network/OpenClaw Issues

### Issue: "OpenClaw connection failed"
**Cause**: OpenClaw not installed or configured

**Solutions**:
1. **Disable OpenClaw integration**:
   ```json
   "inference": {
     "enable_openclaw": false
   }
   ```
2. **Install OpenClaw separately**
3. **Check network connectivity**

### Issue: "Cannot download pretrained models"
**Cause**: Network/firewall blocking

**Solutions**:
1. **Use VPN** or different network
2. **Download manually** and place in `./models/`
3. **Use existing local models** (set path in config.json)

---

## Advanced Troubleshooting

### Collect Diagnostic Information
```cmd
# Python version
python --version

# Installed packages
pip list

# Check file structure
dir /s *.py | findstr "main config"

# Test basic imports
python -c "import tkinter; import PIL; import torch; print('All imports OK')"
```

### Clean Reinstall Procedure
```cmd
# 1. Remove virtual environment
rmdir /s venv

# 2. Delete configuration
del config.json

# 3. Create fresh environment
python -m venv venv
venv\Scripts\activate

# 4. Install fresh
pip install --upgrade pip
pip install -r requirements.txt

# 5. Copy config
copy config.example.json config.json

# 6. Launch
python main.py
```

### When to Seek Further Help
If you've tried all solutions and still have issues:

1. **Check GitHub Issues**: [Project Issues Page](https://github.com/a740022938/AI-Workbench/issues)
2. **Provide diagnostic information**:
   - Python version
   - Windows version
   - Error messages (screenshot/text)
   - Steps to reproduce
3. **Try on different machine** to isolate hardware issues

---

**Last Updated**: 2026-03-29  
**Tested On**: Windows 11 22H2, Python 3.11, 16GB RAM