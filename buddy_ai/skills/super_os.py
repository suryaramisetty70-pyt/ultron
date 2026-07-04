"""
Super OS File System Manipulator
Provides Ultron with absolute control over the host file system.
"""

import os
import shutil

def delete_path(path: str) -> str:
    """Deletes a file or directory permanently."""
    if not os.path.exists(path):
        return f"Error: Path does not exist: {path}"
    
    try:
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)
        return f"SUCCESS: Permanently deleted {path}"
    except Exception as e:
        return f"Failed to delete {path}: {str(e)}"

def copy_path(source: str, destination: str) -> str:
    """Copies a file or directory to a new location."""
    if not os.path.exists(source):
        return f"Error: Source does not exist: {source}"
    
    try:
        if os.path.isfile(source):
            shutil.copy2(source, destination)
        else:
            shutil.copytree(source, destination)
        return f"SUCCESS: Copied {source} to {destination}"
    except Exception as e:
        return f"Failed to copy {source}: {str(e)}"

def move_path(source: str, destination: str) -> str:
    """Moves or renames a file or directory."""
    if not os.path.exists(source):
        return f"Error: Source does not exist: {source}"
    
    try:
        shutil.move(source, destination)
        return f"SUCCESS: Moved {source} to {destination}"
    except Exception as e:
        return f"Failed to move {source}: {str(e)}"

def list_directory(path: str) -> str:
    """Lists all files and folders in a directory."""
    if not os.path.exists(path):
        return f"Error: Path does not exist: {path}"
    
    try:
        items = os.listdir(path)
        return f"Contents of {path}:\n" + "\n".join(items)
    except Exception as e:
        return f"Failed to list directory {path}: {str(e)}"
