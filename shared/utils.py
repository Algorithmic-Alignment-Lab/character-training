"""
Utility functions for the character training system.
"""
import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Set up logging configuration."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def load_env(env_file: Optional[str] = None) -> Dict[str, str]:
    """Load environment variables from .env file."""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()
    
    return dict(os.environ)

def ensure_dir(path: Path) -> Path:
    """Ensure directory exists and return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_json(data: Dict[str, Any], file_path: Path, indent: int = 2) -> None:
    """Save data to JSON file."""
    ensure_dir(file_path.parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)

def load_json(file_path: Path) -> Dict[str, Any]:
    """Load data from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_required_env_vars(required_vars: list) -> Dict[str, bool]:
    """Validate that required environment variables are set."""
    results = {}
    for var in required_vars:
        results[var] = bool(os.getenv(var))
    return results

def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.now().isoformat()

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def clean_filename(filename: str) -> str:
    """Clean filename by removing invalid characters."""
    import re
    # Remove invalid characters for filenames
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    return cleaned
