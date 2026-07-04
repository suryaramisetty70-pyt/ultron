"""
Ultron Time Management Skills
Handles reminders and alarms.
"""
import threading
import time
import subprocess
import os

def _reminder_thread(seconds, message):
    time.sleep(seconds)
    # Using edge-tts directly via subprocess for the reminder so we don't conflict with main audio
    try:
        safe_msg = message.replace('"', '').replace("'", "")
        script = f'''
        import asyncio, edge_tts, pygame, os
        async def run():
            communicate = edge_tts.Communicate("Reminder: {safe_msg}", "en-US-ChristopherNeural")
            await communicate.save("remind.mp3")
        asyncio.run(run())
        pygame.mixer.init()
        pygame.mixer.music.load("remind.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        try: os.remove("remind.mp3")
        except: pass
        '''
        # Write to temp file and run
        temp_file = "temp_remind.py"
        with open(temp_file, "w") as f:
            f.write(script)
        subprocess.run(["python", temp_file], creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            os.remove(temp_file)
        except:
            pass
    except Exception as e:
        print(f"[Reminder Error]: {e}")

def set_reminder(minutes, message):
    """
    Sets a background reminder that will speak out loud after the specified minutes.
    """
    try:
        seconds = float(minutes) * 60
        t = threading.Thread(target=_reminder_thread, args=(seconds, message), daemon=True)
        t.start()
        return f"Reminder set for {minutes} minutes from now."
    except Exception as e:
        return f"Failed to set reminder: {str(e)}"
