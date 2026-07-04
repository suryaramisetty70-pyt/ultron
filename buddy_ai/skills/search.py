"""
Ultron Code Search (Local Grep)
Allows Ultron to scan local directories for specific code or text.
"""
import os

def search_files(directory, query, max_results=20):
    """Searches for a specific string across all text files in a directory."""
    try:
        if not os.path.exists(directory):
            return f"Error: Directory '{directory}' does not exist."
            
        results = []
        # Exclude common large/binary directories to avoid hanging
        exclude_dirs = {'.git', '.venv', 'node_modules', '__pycache__'}
        
        for root, dirs, files in os.walk(directory):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if len(results) >= max_results:
                    break
                    
                # Skip known binary or media files
                if file.endswith(('.png', '.jpg', '.mp3', '.mp4', '.pdf', '.exe', '.dll', '.zip')):
                    continue
                    
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if query.lower() in line.lower():
                                results.append(f"{filepath}:{line_num} -> {line.strip()}")
                                if len(results) >= max_results:
                                    break
                except UnicodeDecodeError:
                    # Skip files that aren't valid UTF-8 text
                    continue
                except Exception:
                    continue
                    
        if not results:
            return f"No matches found for '{query}' in '{directory}'."
            
        return "Search Results:\n" + "\n".join(results)
    except Exception as e:
        return f"Failed to search directory {directory}: {str(e)}"
