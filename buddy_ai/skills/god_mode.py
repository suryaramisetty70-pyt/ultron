"""
Ultron God Mode Skills
Gives Ultron complete, dynamic access to the Windows PowerShell terminal.
"""
import subprocess

def run_powershell(command):
    """
    Executes a PowerShell command dynamically and returns the output.
    Ultron can use this to open settings, find files, check PC health, etc.
    """
    print(f"[God Mode] Executing: {command}")
    try:
        # Run the command with a timeout to prevent hanging the AI
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if error:
            return f"Command executed with errors: {error}"
            
        if not output:
            return "Command executed successfully with no output."
            
        # Truncate output if it's massive to avoid blowing up the LLM context window
        if len(output) > 2000:
            output = output[:2000] + "\n...[OUTPUT TRUNCATED]"
            
        return output
        
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Failed to run command: {str(e)}"
