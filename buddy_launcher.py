import subprocess
import sys
import time

print("Starting Buddy in background...")

process = subprocess.Popen(
    [sys.executable, "buddy_core.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

print("Buddy is running.")
print("Press Ctrl + C to stop Buddy.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping Buddy...")
    process.terminate()
    print("Buddy stopped.")
