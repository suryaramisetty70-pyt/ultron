"""
The "Rewind AI" Memory Engine
Grabs silent screenshots of your desktop every 60 seconds, uses local EasyOCR
to extract the text, and stores it in a ChromaDB Vector Database.
Gives Ultron perfect photographic memory of everything you've ever seen on screen.
"""

import time
import os
import multiprocessing
from datetime import datetime
from PIL import ImageGrab

def _run_rewind_loop():
    """
    The internal loop running on a separate CPU core to prevent UI freezing.
    """
    try:
        import easyocr
        import chromadb
    except ImportError:
        print("[Rewind Engine] FATAL ERROR: easyocr or chromadb not installed. Sleeping loop.")
        return

    print("\n[Rewind Engine] Booting Offline Photographic Memory...")
    # Setup ChromaDB for local persistent storage
    db_path = os.path.join(os.getcwd(), "ultron_memory_db")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="screen_logs")
    
    # Setup EasyOCR (Downloads ~100MB model on first run, uses GPU if available)
    print("[Rewind Engine] Loading Neural OCR Model...")
    reader = easyocr.Reader(['en'], gpu=True) # Automatically falls back to CPU
    print("[Rewind Engine] Memory recording activated (1 snapshot / 60 sec).")
    
    screenshot_path = "temp_rewind_capture.png"
    
    blocklist = ["banking", "password", "key", "credential", "auth", "secret", "private"]
    import ctypes
    from buddy_ai.core_extensions import apply_privacy_noise
    
    while True:
        try:
            # Check active window title for screen consent validation
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            window_title = buff.value.lower()
            
            if any(term in window_title for term in blocklist):
                print(f"[Rewind Engine] Consent Block: Suppressing capture for sensitive window: {buff.value}")
                time.sleep(60)
                continue
                
            # 1. Silent Screenshot
            screen = ImageGrab.grab()
            screen.save(screenshot_path)
            
            # 2. Extract Text
            result = reader.readtext(screenshot_path, detail=0)
            text_content = " ".join(result)
            
            # Privacy redactions and Differential Privacy noise filtering
            text_content = apply_privacy_noise(text_content)
            
            # 3. Push to Vector DB
            if text_content.strip() and len(text_content) > 20: # Ignore blank screens
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                doc_id = f"mem_{int(time.time())}"
                
                collection.add(
                    documents=[text_content],
                    metadatas=[{"timestamp": timestamp}],
                    ids=[doc_id]
                )
                print(f"[Rewind Engine] Memory logged at {timestamp} (Saved to Vector DB).")
                
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
        except Exception as e:
            print(f"[Rewind Engine] Capture Error: {e}")
            
        time.sleep(60)

def start_rewind_engine():
    """Starts the photographic memory loop as a background process."""
    p = multiprocessing.Process(target=_run_rewind_loop, daemon=True)
    p.start()
    return p

def search_rewind_memory(query: str) -> str:
    """
    Searches the local ChromaDB vector database for past screen activity.
    """
    try:
        import chromadb
    except ImportError:
        return "ERROR: ChromaDB is not installed."
        
    print(f"\n[Rewind Engine] Searching photographic memory for: '{query}'...")
    db_path = os.path.join(os.getcwd(), "ultron_memory_db")
    
    if not os.path.exists(db_path):
        return "ERROR: The memory database has not been created yet. Let it run for a few minutes first."
        
    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection(name="screen_logs")
        
        results = collection.query(
            query_texts=[query],
            n_results=1
        )
        
        if not results['documents'] or not results['documents'][0]:
            return f"I searched your visual memory, but found nothing related to '{query}'."
            
        top_match = results['documents'][0][0]
        metadata = results['metadatas'][0][0]
        timestamp = metadata['timestamp']
        
        # Trim the match so we don't overflow the LLM context if the screen had tons of text
        if len(top_match) > 1000:
            top_match = top_match[:1000] + "... [TRUNCATED]"
            
        return f"MEMORY RECOVERED (Timestamp: {timestamp}):\n{top_match}"
        
    except Exception as e:
        return f"ERROR: Failed to retrieve memory. {e}"
