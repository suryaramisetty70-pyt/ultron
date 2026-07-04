import json
import os

# =========================================
# MEMORY FILE
# =========================================

MEMORY_FILE = "conversation_memory.json"

# =========================================
# CREATE MEMORY FILE
# =========================================

def initialize_memory():

    if not os.path.exists(MEMORY_FILE):

        with open(
            MEMORY_FILE,
            "w"
        ) as file:

            json.dump(
                [],
                file,
                indent=4
            )

# =========================================
# LOAD MEMORY
# =========================================

def load_memory():

    initialize_memory()

    with open(
        MEMORY_FILE,
        "r"
    ) as file:

        return json.load(file)

# =========================================
# SAVE MEMORY
# =========================================

def save_memory(memory):

    with open(
        MEMORY_FILE,
        "w"
    ) as file:

        json.dump(
            memory,
            file,
            indent=4
        )

# =========================================
# ADD CONVERSATION
# =========================================

def add_to_memory(user, buddy):

    memory = load_memory()

    memory.append({

        "user": user,
        "buddy": buddy

    })

    # keep only latest 20 chats

    memory = memory[-20:]

    save_memory(memory)

# =========================================
# GET CHAT HISTORY
# =========================================

def get_memory_context():

    memory = load_memory()

    context = ""

    for item in memory:

        context += (

            f"User: {item['user']}\n"
            f"Buddy: {item['buddy']}\n"

        )

    return context