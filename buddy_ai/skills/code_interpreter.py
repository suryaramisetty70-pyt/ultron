"""
Ultron Code Interpreter (ChatGPT Parity)
Allows Ultron to execute arbitrary Python code in a temporary sandbox.
"""
import sys
import subprocess
import tempfile
import os

def execute_python(code):
    """
    Writes Python code to a temporary file, executes it, and returns stdout/stderr.
    This allows Ultron to do complex math, data analysis, or logic on the fly.
    """
    temp_file = None
    try:
        print("[Code Interpreter] Executing Python sandbox...")
        
        # Create a temporary python file
        fd, temp_file = tempfile.mkstemp(suffix=".py")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(code)
            
        # Execute the file with a 15-second timeout to prevent infinite loops
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        output = ""
        if result.stdout:
            output += f"--- STDOUT ---\n{result.stdout}\n"
        if result.stderr:
            output += f"--- STDERR ---\n{result.stderr}\n"
            
        if not output:
            output = "Code executed successfully with no output."
            
        return output
        
    except subprocess.TimeoutExpired:
        return "Error: Python script execution timed out after 15 seconds."
    except Exception as e:
        return f"Failed to execute python: {str(e)}"
    finally:
        # Clean up the temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
