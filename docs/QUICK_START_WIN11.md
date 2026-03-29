# Quick Start Guide for Windows 11

This guide assumes you already have Python installed and are comfortable with basic command line usage.

## Prerequisites Checklist

- ✅ Python 3.8+ installed and in PATH
- ✅ Git installed (for cloning) or project downloaded as ZIP
- ✅ Command prompt/PowerShell access

## Fastest Path to Launch

### 1. Get the Code

**Option A: Clone with Git**
```cmd
git clone https://github.com/a740022938/AI-Workbench.git
cd AI-Workbench
```

**Option B: Download ZIP**
1. Download ZIP from GitHub
2. Extract to a folder (e.g., `C:\AI_Workbench`)
3. Open terminal in that folder

### 2. Install Dependencies (One Command)

```cmd
pip install -r requirements.txt
```

**Optional GPU support** (if you have NVIDIA GPU):
```cmd
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 3. Create Configuration File

```cmd
copy config.example.json config.json
```

### 4. Launch Application

**Recommended method** (use this):
```cmd
python main.py
```

**Alternative method**:
```cmd
python run.py
```

## What to Expect

### First Launch (30-60 seconds)
- Application window appears with six center buttons
- Training center registers 4 trainers (you'll see console messages)
- Default Win11 dark theme is applied
- English language is selected by default

### First Actions
1. **Load images**: Click "File" → "Open Image Folder" or use the folder icon
2. **Explore centers**: Click any of the six center buttons
3. **Change settings**: Gear icon → "Settings"

## Quick Configuration Tips

### Essential Settings to Change
1. **Image/Label directories**: Settings → Paths → Set your dataset folders
2. **UI Theme**: Settings → Appearance → Style (Win11, Apple, ChatGPT)
3. **Language**: Settings → Appearance → Language (English/中文)

### Optional Settings
- Enable/disable auto-save
- Adjust inference confidence threshold
- Configure OpenClaw integration (if you use OpenClaw)

## Recommended Workflow Order

For new users, we recommend this sequence:

1. **Annotation Center** → Load images and label a few examples
2. **Dataset Center** → Split your data into train/val/test
3. **Training Center** → Train a simple classification model
4. **Inspection Center** → Check annotation quality
5. **Correction Center** → Fix bad cases
6. **Collaboration Center** → Explore AI-assisted workflows

## Troubleshooting Quick Fixes

### Issue: "ModuleNotFoundError"
```cmd
# Reinstall missing packages
pip install Pillow torch ultralytics opencv-python pyyaml tqdm
```

### Issue: Application closes immediately
- Run from command prompt to see error messages
- Check `config.json` exists
- Ensure no Python syntax errors

### Issue: Slow performance
- Close other applications
- Reduce batch size in training settings
- Use CPU if GPU memory is limited

## Advanced Quick Start

### Using Virtual Environment (Recommended for multiple projects)
```cmd
# Create and activate
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch
python main.py
```

### Silent Mode (for testing)
```cmd
python -c "import sys; sys.path.insert(0, '.'); from main import main; main()"
```

## Next Steps After Launch

1. **Try annotation**: Load an image folder and draw bounding boxes
2. **Run training**: Use the training center with sample data
3. **Export dataset**: Create YOLO-format dataset from your annotations
4. **Enable AI collaboration**: Connect OpenClaw for assisted workflows

## Need Faster Help?

- **Immediate issues**: Check terminal error messages
- **Configuration**: Verify `config.json` exists and is valid JSON
- **Dependencies**: Run `pip list` to see installed packages
- **Application logs**: Check `./logs/startup_error.log` if created

---

**Time to first launch**: 5-10 minutes (including dependency installation)  
**Time to productive use**: 15-30 minutes (after loading first dataset)