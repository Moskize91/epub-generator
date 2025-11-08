"""Test configuration and shared fixtures."""
import shutil
from pathlib import Path


def setup_module():
    """Clean temp directory before running tests."""
    temp_dir = Path(__file__).parent / "temp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(exist_ok=True)
