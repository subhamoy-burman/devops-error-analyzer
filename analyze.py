#!/usr/bin/env python3

"""
Entry point script for DevOps Error Analyzer
"""

import sys
from pathlib import Path

# Add parent directory to sys.path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Import main module
from src.main import main

if __name__ == "__main__":
    sys.exit(main())
