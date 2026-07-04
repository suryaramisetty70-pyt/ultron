import chromadb
from chromadb.config import Settings
import datetime
import os
import json

class UltronMemory:
    def __init__(self, db_path="ultron_chroma_db"):
        print("[Ultron Memory] Initializing Vector Database...")
        # Persist ChromaDB locally
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Get or create a collection for conversation history
        self.collection = self.client.get_or_create_collection(
            name="conversation_history",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Episodic User Profile
        self.profile_path = "user_profile.json"
        if os.path.exists(self.profile_path):
            with open(self.profile_path, "r") as f:
                self.user_profile = json.load(f)
        else:
            self.user_profile = {"preferences": {}}
            self._save_profile()
            
        print("[Ultron Memory] Vector Database Online.")

    def _save_profile(self):
        with open(self.profile_path, "w") as f:
            json.dump(self.user_profile, f, indent=4)
            
    def update_user_preference(self, key, value):
        """Updates a specific preference in the episodic memory."""
        self.user_profile["preferences"][key] = value
        self._save_profile()
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
                past_contexts.append(f"User said: {doc} | Ultron replied: {meta['response']}")
                
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
