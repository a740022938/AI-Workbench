#!/usr/bin/env python3
"""
Launcher script for AI Vision Data & Training Workbench.
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from main import main
    main()