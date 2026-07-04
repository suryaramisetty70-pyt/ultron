"""
Auto-Coder Protocol
Allows Ultron to autonomously run, test, and scan Python files and entire projects.
"""

import subprocess
import os

def test_python_file(filepath: str) -> str:
    """Runs a Python script and returns the exact output or crash logs (Traceback)."""
    if not os.path.exists(filepath):
        return f"Error: File not found at {filepath}"
    
    try:
        # Run the file and capture output
        result = subprocess.run(["python", filepath], capture_output=True, text=True, timeout=30)
        
        output = ""
        if result.stdout:
            output += f"--- STDOUT (Success Output) ---\n{result.stdout}\n"
        if result.stderr:
            output += f"--- STDERR (Crash / Error Logs) ---\n{result.stderr}\n"
            
        if not output:
            output = "Script executed successfully with no output."
            
        return output
    except subprocess.TimeoutExpired:
        return "Error: Script execution timed out after 30 seconds (might be an infinite loop)."
    except Exception as e:
        return f"Execution Failed: {str(e)}"

def scan_python_project(folder_path: str) -> str:
    """Scans an entire folder for Python syntax errors."""
    if not os.path.exists(folder_path):
        return f"Error: Folder not found at {folder_path}"
        
    report = []
    python_files_found = 0
    
    for root, _, files in os.walk(folder_path):
        # Skip virtual environments
        if ".venv" in root or "node_modules" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                python_files_found += 1
                filepath = os.path.join(root, file)
                
                # Check syntax without running the file
                result = subprocess.run(["python", "-m", "py_compile", filepath], capture_output=True, text=True)
                
                if result.returncode != 0:
                    report.append(f"[ERROR IN {filepath}]\n{result.stderr.strip()}")
                    
    if not report:
        return f"SUCCESS: Scanned {python_files_found} Python files. No syntax errors found in the project!"
        
    return f"FAILED: Scanned {python_files_found} files and found syntax errors:\n\n" + "\n\n".join(report)
