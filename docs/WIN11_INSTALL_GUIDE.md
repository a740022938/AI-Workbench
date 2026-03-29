# Windows 11 Installation Guide for AI Vision Data & Training Workbench

This guide walks you through the complete installation process on Windows 11, from Python installation to launching the application.

## Prerequisites

- Windows 11 (64-bit)
- Administrator privileges (for Python installation)
- At least 4GB RAM (8GB recommended for YOLO training)
- At least 2GB free disk space

## Step 1: Install Python

### Option A: Install Python from Microsoft Store (Recommended for beginners)
1. Open **Microsoft Store** from Start menu
2. Search for "Python"
3. Select **Python 3.11** or **Python 3.12** (choose the latest version)
4. Click "Get" or "Install"
5. Wait for installation to complete

### Option B: Install Python from python.org (For advanced users)
1. Visit [python.org/downloads](https://www.python.org/downloads/)
2. Download the **Windows installer (64-bit)**
3. Run the installer
4. **IMPORTANT**: Check **"Add Python to PATH"** at the bottom
5. Click "Install Now"
6. Wait for installation to complete

### Verify Python Installation
1. Press **Win + R**, type `cmd`, press Enter
2. In the command prompt, type:
   ```cmd
   python --version
   ```
3. You should see something like: `Python 3.11.8`

## Step 2: Open Terminal/Command Prompt

You have several options:

### Option 1: Windows Terminal (Recommended)
- Press **Win + X**, select "Windows Terminal (Admin)" or "Windows Terminal"
- Or search for "Terminal" in Start menu

### Option 2: Command Prompt
- Press **Win + R**, type `cmd`, press Enter

### Option 3: PowerShell
- Press **Win + R**, type `powershell`, press Enter

## Step 3: Navigate to Project Directory

Assuming you've cloned or downloaded the project to `C:\AI_Workbench`:

```cmd
cd C:\AI_Workbench
```

If you placed it elsewhere, adjust the path accordingly:
```cmd
cd "C:\Users\YourName\Downloads\AI-Workbench"
```

## Step 4: Create Virtual Environment (Optional but Recommended)

### Why use a virtual environment?
- Keeps project dependencies isolated
- Prevents conflicts with other Python projects
- Easier to manage and clean up

### Create and activate virtual environment:
```cmd
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate
```

You should see `(venv)` appear at the beginning of your command line.

## Step 5: Install Dependencies

With the virtual environment activated (or from your base Python):

```cmd
pip install -r requirements.txt
```

This will install:
- Pillow (for image processing)
- PyTorch (for deep learning)
- Ultralytics YOLO (for object detection)
- OpenCV (for computer vision)
- And other required libraries

**Note**: The first installation may take 5-15 minutes depending on your internet speed.

### If you have a GPU (NVIDIA):
For better training performance, install PyTorch with CUDA support:
```cmd
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Step 6: Configuration Setup

The application needs a configuration file to run:

1. **Copy the example configuration**:
   ```cmd
   copy config.example.json config.json
   ```

2. **Verify the file was created**:
   ```cmd
   dir config.json
   ```

The `config.json` file contains default paths and settings. You can modify it later in the application's Settings menu.

## Step 7: Launch the Application

You have two options:

### Option A: Using main.py (Recommended)
```cmd
python main.py
```

### Option B: Using the launcher script
```cmd
python run.py
```

Both will start the application. The first launch may take a few seconds.

## Step 8: First-time Setup in Application

1. **Set up image directory**:
   - Click "File" → "Open Image Folder"
   - Navigate to your images folder
   - Click "Select Folder"

2. **Configure settings** (optional):
   - Click "Settings" button (gear icon) or "File" → "Settings"
   - Adjust UI theme (Win11, Apple, ChatGPT)
   - Change language (English/中文)
   - Configure other preferences

3. **Start using the application**:
   - Use the six center buttons for different workflows
   - Annotation: Label images with bounding boxes
   - Training: Train AI models
   - Inspection: Check data quality
   - Dataset: Export datasets
   - Correction: Manage bad cases
   - Collaboration: AI-assisted workflows

## Common First-run Issues & Solutions

### "No module named 'PIL'"
- Make sure Pillow installed: `pip install Pillow`
- Reactivate virtual environment if using one

### "No module named 'torch'"
- PyTorch installation might have failed
- Try: `pip install torch torchvision`

### Application starts but shows empty window
- This is normal for first launch
- Use "File" → "Open Image Folder" to load images

### "config.json not found"
- You forgot to copy the example config
- Run: `copy config.example.json config.json`

### Application closes immediately
- Check for error messages in terminal
- Ensure all dependencies installed
- Try running with administrator privileges

## Next Steps

- Read the [QUICK_START_WIN11.md](QUICK_START_WIN11.md) for faster setup
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Explore the application's features through the six centers

## Need Help?

- Check the troubleshooting guide
- Review the requirements.txt installation notes
- Ensure Python is correctly added to PATH
- Try running commands as Administrator if you encounter permission errors