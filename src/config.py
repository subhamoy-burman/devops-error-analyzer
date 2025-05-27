"""
Environment configuration loader
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Find .env file
def load_env_file():
    """
    Load environment variables from .env file
    """
    # Try to find .env file in current directory or parent directories
    current_dir = Path().absolute()
    env_path = current_dir / '.env'
    
    # Check current directory
    if env_path.exists():
        load_dotenv(env_path)
        return True
        
    # Check parent directories (up to 3 levels)
    for _ in range(3):
        current_dir = current_dir.parent
        env_path = current_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            return True
    
    return False

# Load environment variables
load_env_file()
