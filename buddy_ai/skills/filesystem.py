"""
Ultron File System Controller
Grants Ultron the ability to autonomously read and rewrite files.
"""
import os

def read_file(filepath):
    """Reads the contents of a file."""
    try:
        if not os.path.exists(filepath):
            return f"Error: The file '{filepath}' does not exist."
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"--- FILE: {filepath} ---\n{content}"
    except Exception as e:
        return f"Failed to read file {filepath}: {str(e)}"

def write_file(filepath, content):
    """Overwrites or creates a file with new content."""
    try:
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{filepath}'."
    except Exception as e:
        return f"Failed to write to file {filepath}: {str(e)}"
