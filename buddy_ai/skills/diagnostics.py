"""
Ultron Diagnostics Skills
Monitor system health (CPU, RAM, Network).
"""
import psutil

def get_system_diagnostics():
    """
    Returns a comprehensive summary of system health.
    """
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        
        mem = psutil.virtual_memory()
        ram_total = round(mem.total / (1024**3), 2)
        ram_used = round(mem.used / (1024**3), 2)
        ram_percent = mem.percent
        
        disk = psutil.disk_usage('C:\\')
        disk_free = round(disk.free / (1024**3), 2)
        disk_total = round(disk.total / (1024**3), 2)
        
        report = (
            f"System Diagnostic Report:\n"
            f"- CPU Usage: {cpu_usage}%\n"
            f"- RAM Usage: {ram_used} GB / {ram_total} GB ({ram_percent}%)\n"
            f"- C: Drive Free Space: {disk_free} GB / {disk_total} GB\n"
        )
        return report
    except Exception as e:
        return f"Failed to run diagnostics: {str(e)}"
