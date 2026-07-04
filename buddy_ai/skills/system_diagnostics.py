"""
System Diagnostics Engine
Monitors hardware health, battery, CPU, and RAM usage.
"""

import psutil

def run_system_diagnostics() -> str:
    """
    Analyzes CPU, RAM, Battery, and Disk usage to provide a system health report.
    """
    print("\n[Diagnostics] Running hardware sweep...")
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    battery = psutil.sensors_battery()
    
    report = []
    report.append(f"CPU Usage is at {cpu}%.")
    report.append(f"Memory Usage is at {ram.percent}%.")
    report.append(f"Main Drive is {disk.percent}% full.")
    
    if battery:
        report.append(f"Battery is at {battery.percent}%.")
        if battery.power_plugged:
            report.append("System is connected to AC power.")
        elif battery.percent < 20:
            report.append("CRITICAL WARNING: Battery is critically low. System shutdown is imminent without power.")
    else:
        report.append("No battery detected (Desktop system).")
    
    if cpu > 85:
        report.append("WARNING: CPU usage is extremely high. Recommend closing background tasks.")
        
    final_report = " ".join(report)
    print(f"[Diagnostics] Sweep complete: {final_report}")
    return final_report
