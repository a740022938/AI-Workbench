# AI Vision Data & Training Workbench

A comprehensive desktop application for AI vision projects, covering data annotation, model training, data quality inspection, dataset export, closed-loop correction, and AI-assisted collaboration workflows.

## Project Status

**Current Version**: v1.0.0-stage (Technical Preview / Stage Release)

**⚠️ Important Notice**: This is a **Technical Preview** (Stage Public Development Release), NOT a stable production-ready version.

### 🎯 Target Audience
This release is primarily intended for:
- **Developers** who can handle dependency installation and debugging
- **Collaborators** interested in contributing to the project architecture
- **Architecture reviewers** evaluating the code structure and design patterns
- **AI/ML practitioners** comfortable with Python environment setup

### 📦 What's Ready
- ✅ **Complete 6-Center Architecture**: All major functional centers implemented
- ✅ **Core Business Logic**: Training, inspection, dataset, and collaboration systems fully functional
- ✅ **Professional UI System**: Three visual themes with bilingual support
- ✅ **AI Collaboration Framework**: OpenClaw integration with 32 structured actions
- ✅ **Extensible Architecture**: Plugin system and clear extension points

### 🔧 What's Being Optimized
- 🔄 **Dependency Management**: Installation process and environment setup
- 🔄 **GUI Launch Experience**: Ensuring smooth startup across different systems
- 🔄 **UI Polish**: Theme switching details and visual consistency
- 🔄 **Documentation**: Installation guides and troubleshooting resources

### 📝 Release Philosophy
This is a **stage release** meaning:
- Core architecture and business logic are complete and stable
- The codebase is ready for public collaboration and feedback
- Installation and runtime experience are still being optimized
- Expect refinements based on community feedback
- NOT yet a "plug-and-play" solution for end-users

## Core Modules

1. **Main Window / Dashboard** - Central hub with six major center entries
2. **Annotation Workbench** - Image labeling, bounding box editing, category management
3. **Training Center** - Multi-trainer support, experiment comparison, result analysis (14-phase complete feature matrix)
4. **Quality Inspection Center** - Annotation anomaly detection, batch repair, manual processing (11-phase complete workflow)
5. **Dataset Production Center** - Dataset splitting, distribution statistics, pre-check, YOLO format export
6. **Closed-Loop Correction Center** - Bad case collection, low-performance category feedback, problem state tracking
7. **AI Collaboration OS** - Unified action system, state snapshots, action receipts, OpenClaw integration
8. **UI Style & Language System** - Win11/Apple/ChatGPT themes, bilingual support, real-time switching

## Project Structure

```
AI_Workbench_MASTER/
├── app/                    # Application packaging and distribution
├── assets/                 # Static resources (icons, fonts, CSS)
├── config/                 # Configuration files (UI, language, training)
├── core/                   # Core business logic (all data and service layers)
│   ├── ui_style_manager.py     # UI theme manager (3 styles + callback system)
│   ├── language_manager.py     # Bilingual manager (200+ text resources)
│   ├── action_system.py        # AI collaboration action system (32 actions)
│   ├── training_center_manager.py  # Training center core (14-phase features)
│   ├── data_health_manager.py  # Quality inspection manager
│   ├── dataset_exporter.py     # Dataset export manager
│   └── closed_loop_manager.py  # Closed-loop correction manager
├── ui/                     # User interface layer (all windows and panels)
│   ├── main_window.py          # Main application window
│   ├── canvas_panel.py         # Annotation canvas
│   ├── training_center_window.py  # Training center UI
│   ├── data_health_window.py   # Quality inspection UI
│   ├── dataset_export_window.py # Dataset export UI
│   ├── closed_loop_window.py   # Closed-loop correction UI
│   └── settings_window.py      # Settings window (theme/language切换)
├── utils/                  # Utility functions
├── scripts/               # Maintenance and utility scripts
├── tests/                 # Test scripts and examples
├── docs/                  # Documentation
└── plugins/               # Plugin system (extensible)
```

## Environment Requirements

- **Python**: 3.8+
- **Operating System**: Windows 10/11, macOS (tested), Linux (theoretically compatible)
- **Dependencies**: See `requirements.txt`

## Installation & Dependencies

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AI-Workbench.git
   cd AI-Workbench
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) For GPU acceleration with YOLO training:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118  # CUDA 11.8
   ```

## Quick Start

### Command Line Launch
```bash
python main.py
```

Or use the launcher script:
```bash
python run.py
```

### First-time Setup
1. Launch the application
2. Open an image folder via `File` → `Open Image Folder`
3. Configure paths in `Settings` → `Paths`
4. Select your preferred UI style and language in `Settings` → `Appearance`

## Configuration

### Configuration Files
- `config.json` - Main application configuration (paths, model settings, behavior)
- `config/ui/ui_config.json` - UI style and language settings (auto-generated)
- `config/language/language_config.json` - Language preference (auto-generated)

### Example Configuration
Create `config.json` with the following structure (or modify the auto-generated one):
```json
{
    "paths": {
        "image_dir": "./images",
        "label_dir": "./labels",
        "bad_cases_dir": "./bad_cases",
        "model_path": "",
        "video_dir": "",
        "output_dataset_dir": "./dataset_output"
    },
    "model": {
        "conf": 0.25,
        "iou": 0.5,
        "imgsz": 640
    },
    "behavior": {
        "auto_save": true,
        "auto_save_on_navigate": true
    },
    "ui": {
        "alpha": 0.98,
        "language": "en_US",
        "style": "win11"
    }
}
```

## Key Features in Detail

### Annotation Workbench
- **Bounding Box Annotation**: Click-and-drag with real-time coordinates
- **Category Management**: Add/edit/delete object categories
- **AI Assistance**: YOLO inference integration for auto-labeling suggestions
- **Keyboard Shortcuts**: Full suite for efficient labeling workflow
- **OpenClaw Integration**: AI-assisted labeling through action system

### Training Center (14-Phase Complete)
1. **Configuration Management**: YAML-based trainer configurations
2. **Pre-training Health Check**: Validate datasets and configurations
3. **Multi-Trainer Support**: Classification, detection, segmentation adapters
4. **Experiment History**: Complete history tracking with sorting/filtering
5. **Configuration Comparison**: Side-by-side diff visualization
6. **Experiment Notes**: Editable annotations for each training run
7. **Tags & Favorites**: Organize experiments with tags and star ratings
8. **Batch Operations**: Mass tagging, archiving, exporting
9. **One-Click Retraining**: Inherit configurations and annotations
10. **Training Monitor**: Real-time metrics during training

### Quality Inspection Center (11-Phase Complete)
1. **Annotation Validation**: 6 types of annotation errors detected
2. **Per-Image Summary**: Group issues by image with statistics
3. **Batch Repair**: Fix all auto-fixable issues in one click
4. **Difference Reports**: Detailed change logs after repairs
5. **Manual Processing Entry**: Direct jump to images needing manual review
6. **Export Reports**: Generate comprehensive quality reports

### Dataset Production Center
- **Smart Splitting**: Train/val/test split with ratio control
- **Category Distribution**: Visual statistics of object categories
- **Pre-export Validation**: Check for common issues before export
- **YOLO Format Export**: Standard YOLO dataset structure
- **Export Reports**: Detailed export summaries

### Closed-Loop Correction Center
- **Bad Case Collection**: Collect low-confidence predictions
- **Problem State Tracking**: Track issues through lifecycle
- **Re-training Recommendations**: Suggest when to retrain models
- **Cross-Module Integration**: Connect with quality inspection and training centers

### AI Collaboration System
- **Unified Action Interface**: 32 high-value actions with structured receipts
- **State Snapshots**: Capture application state for AI context
- **Risk Assessment**: Action risk levels and execution strategies
- **OpenClaw Integration**: Full compatibility with OpenClaw task orchestration

### UI & Internationalization
- **Three Visual Themes**: Win11 (dark), Apple (light gray), ChatGPT (light green)
- **Real-time Switching**: Change themes without restarting
- **Bilingual Support**: English and Chinese (simplified)
- **Consistent Experience**: All 5 core windows fully support theme/language switching

## Development & Extension

### Architecture Philosophy
- **MainWindow Zero-Bloat**: All business logic in separate modules
- **Layered Architecture**: Data layer → Business layer → Interface layer
- **Extension Slots**: Plugin system for adding new trainers, inspectors, exporters
- **Safety-First Culture**: Auto-backup before modifications, comprehensive testing

### Adding New Trainers
1. Create a trainer adapter in `core/trainer_adapters/`
2. Implement the `BaseTrainerAdapter` interface
3. Register in `core/training_center_manager.py`
4. Add UI configuration in `ui/training_center_window.py`

### Adding New Quality Checks
1. Add check logic to `core/data_health_manager.py`
2. Implement fixer in `core/data_health_fixer.py`
3. Add UI integration in `ui/data_health_window.py`

## Current Known Limitations & Technical Constraints

### 🚨 Critical for Technical Preview Users
1. **Dependency Management**: Users must handle Python environment and dependency installation manually
   - `requirements.txt` is provided but may need adjustments for specific systems
   - PIL/Pillow dependency is essential for GUI functionality
   - GPU acceleration (CUDA) requires additional setup

2. **GUI Launch Experience**: Installation and first-run experience is still being optimized
   - Some systems may encounter PIL/Pillow import issues
   - Environment-specific troubleshooting may be required
   - Not yet a "one-click install" solution

3. **Runtime Context Requirements**: Some modules require `WorkbenchContext` parameter
   - `DataHealthManager` needs runtime context for full functionality
   - This is by design for integration but affects isolated testing

### 🔧 Technical Refinements Needed
1. **Real-time Language Refresh**: Some UI labels require window restart for language changes
2. **System Native Dialogs**: File open/save dialogs don't follow application themes (platform limitation)
3. **Advanced AI Review**: AI suggestion system interface ready, but logic implementation pending

### ✨ Enhancement Opportunities
1. **More Trainer History**: Currently only classification trainer has complete history features
2. **Advanced Export Formats**: Currently supports TXT/JSON/CSV (COCO/Pascal VOC planned)
3. **Smoother Animations**: Theme transitions could use animation effects
4. **System Tray Integration**: Background notifications and quick access

### 💡 For Developers & Contributors
- **Architecture is stable**: All extension points and interfaces are defined
- **Code quality is high**: Consistent patterns, comprehensive documentation
- **Testing infrastructure**: Test suite exists but needs expansion
- **Community feedback welcome**: This stage release is specifically for gathering improvement suggestions

## Version History

### v1.0.0-stage (2026-03-29)
- **First public development release**
- Complete 6-center architecture
- Full UI theme and language system
- 14-phase training center
- 11-phase quality inspection center
- AI collaboration action system
- Ready for community collaboration

## Roadmap

### Short-term (v1.1.0)
- More trainer adapters (segmentation, pose estimation)
- Advanced AI-assisted annotation
- Plugin marketplace foundation
- Enhanced export formats (COCO, Pascal VOC)

### Medium-term (v2.0.0)
- Cloud sync and collaboration
- Team project management
- Advanced analytics dashboard
- Mobile companion app

### Long-term Vision
- Full MLOps pipeline integration
- AutoML capabilities
- Enterprise deployment options
- Marketplace for pre-trained models and datasets

## Contributing

We welcome contributions! Please see `CONTRIBUTING.md` (to be created) for guidelines.

## License

MIT License. See `LICENSE` file for details.

## Support & Community

- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: [https://docs.ai-workbench.dev](https://docs.ai-workbench.dev) (to be created)
- **Discord Community**: [https://discord.gg/ai-workbench](https://discord.gg/ai-workbench) (to be created)

## Acknowledgments

- **Ultralytics YOLO**: For the excellent object detection framework
- **OpenClaw**: For AI collaboration infrastructure
- **tkinter**: For the robust GUI framework
- **All Contributors**: Thanks to everyone who has contributed to this project

---

*AI Vision Data & Training Workbench - From annotation to production, all in one desktop application.*