#!/usr/bin/env python3
"""
Launcher script for the Cando application.
This script ensures proper module imports by running from the project root.
"""

import sys
import os
from app.main import main
# Add the current directory to Python path BEFORE importing app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



if __name__ == "__main__":
    main()
