"""
Smart Music Engine
Uses PyWhatKit to automatically find and play mood-based music on YouTube (100% Free).
"""

import pywhatkit
import time

def play_music_by_mood(mood: str) -> str:
    """
    Analyzes the user's mood and plays a matching music playlist on YouTube.
    """
    search_term = f"{mood} mood music mix playlist"
    print(f"[Ultron] Opening YouTube for: {search_term}")
    
    try:
        # playonyt opens the browser and automatically clicks the first video
        pywhatkit.playonyt(search_term)
        return f"SUCCESS: I am now playing {mood} music on YouTube."
    except Exception as e:
        return f"ERROR: Could not open music. {str(e)}"
