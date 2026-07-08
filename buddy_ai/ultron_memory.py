import chromadb
from chromadb.config import Settings
import datetime
import os
import json
import threading

class UltronMemory:
    def __init__(self, db_path="ultron_chroma_db"):
        print("[Vision Memory] Initializing Vector Database...")
        # Try to use a persistent client; if it fails (Rust panic) fall back to an in‑memory client.
        try:
            self.client = chromadb.PersistentClient(path=db_path)
        except BaseException as e:
            print(f"[Vision Memory] Persistent client failed ({e}); switching to in‑memory client.")
            # Use a safe in‑memory client with minimal settings.
            self.client = chromadb.Client(Settings(anonymized_telemetry=False))
        
        # Get or create a collection for conversation history
        self.collection = self.client.get_or_create_collection(
            name="conversation_history",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Episodic User Profile
        self.profile_path = "user_profile.json"
        if not os.path.exists(self.profile_path):
            self._save_profile_data({"preferences": {}, "custom_instructions": []})
            
        # Pre-warm embedding function in a background thread to prevent first-query lag
        def warm_up():
            try:
                self.collection.query(query_texts=["warmup"], n_results=1)
                print("[Vision Memory] Embedding engine fully warmed up and active.")
            except Exception:
                pass
        threading.Thread(target=warm_up, daemon=True).start()
            
        print("[Vision Memory] Vector Database Online.")

    @property
    def user_profile(self):
        """Dynamically read profile from disk so external API modifications are captured instantly."""
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"preferences": {}, "custom_instructions": []}

    def _save_profile_data(self, data):
        try:
            with open(self.profile_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[Vision Memory] Failed to save profile: {e}")
            
    def update_user_preference(self, key, value):
        """Updates a specific preference in the episodic memory."""
        profile = self.user_profile
        if "preferences" not in profile:
            profile["preferences"] = {}
        profile["preferences"][key] = value
        self._save_profile_data(profile)
        return f"Memory Updated: I will remember that your {key} is {value} forever."
        
    def log_interaction(self, user_input, ai_response):
        """Saves a conversation turn into the vector database with metadata."""
        timestamp = datetime.datetime.now().isoformat()
        
        # We store the user input as the document for semantic searching,
        # and the AI response as metadata.
        
        # Generate a unique ID based on timestamp
        doc_id = f"interaction_{timestamp}"
        
        self.collection.add(
            documents=[user_input],
            metadatas=[{"role": "user", "timestamp": timestamp, "response": ai_response}],
            ids=[doc_id]
        )
        
    def recall(self, query_text, n_results=3):
        """Searches the vector database for semantically similar past conversations."""
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            if not results["documents"] or not results["documents"][0]:
                return None
                
            past_contexts = []
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                past_contexts.append(f"User said: {doc} | Vision replied: {meta['response']}")
                
            return "\n".join(past_contexts)
        except Exception as e:
            return None

# Global instance so skills can update it
_memory_instance = None
def get_memory_instance():
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = UltronMemory()
    return _memory_instance

def update_user_preference(key, value):
    return get_memory_instance().update_user_preference(key, value)

# For testing
if __name__ == "__main__":
    memory = UltronMemory()
    memory.log_interaction("What is your name?", "I am Ultron.")
    memory.log_interaction("I need you to build a Jarvis system.", "I will build it.")
    
    print("Recalling memory related to 'Jarvis':")
    print(memory.recall("Can you build Jarvis?"))
