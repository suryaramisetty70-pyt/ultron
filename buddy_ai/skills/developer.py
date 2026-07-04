"""
Ultron Developer Skills
Allows reading from and writing to the local file system.
"""
import os

def write_file(filename, content, folder_path="Desktop"):
    """
    Writes content to a file. 
    By default saves to the user's Desktop.
    """
    try:
        if folder_path.lower() == "desktop":
            target_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        else:
            target_dir = os.path.expanduser("~") # fallback to user home

        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"Successfully created {filename} at {file_path}"
    except Exception as e:
        return f"Failed to write file: {str(e)}"

def read_file(filename, folder_path="Desktop"):
    """
    Reads the content of a file from the Desktop or Documents.
    """
    try:
        if folder_path.lower() == "desktop":
            target_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        elif folder_path.lower() == "documents":
            target_dir = os.path.join(os.path.expanduser("~"), "Documents")
        else:
            # Try absolute path or current dir
            target_dir = folder_path

        file_path = os.path.join(target_dir, filename)
        
        if not os.path.exists(file_path):
            # Fallback: search desktop
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
            if os.path.exists(desktop_path):
                file_path = desktop_path
            else:
                return f"Error: {filename} does not exist in {target_dir}."
                
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Truncate if too long so we don't blow up the LLM context
        if len(content) > 10000:
            content = content[:10000] + "\n...[Content truncated for length]..."
            
        return f"File Content of {filename}:\n{content}"
    except Exception as e:
        return f"Failed to read file: {str(e)}"
