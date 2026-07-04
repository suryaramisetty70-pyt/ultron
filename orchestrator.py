# =========================================
# BUDDY AI ORCHESTRATOR
# =========================================

from memory_manager import buddy_memory

# =========================================
# INTENT DETECTOR
# =========================================

def detect_intent(command):

    command = command.lower()

    # EMAIL AGENT

    if (
        "email" in command
        or "mail" in command
        or "gmail" in command
    ):

        return "email"

    # CODING AGENT

    elif (
        "code" in command
        or "python" in command
        or "program" in command
    ):

        return "coding"

    # SYSTEM CONTROL

    elif (
        "open" in command
        or "close" in command
        or "browser" in command
        or "chrome" in command
    ):

        return "system"

    # NORMAL CHAT

    else:

        return "chat"

# =========================================
# PROCESS COMMAND
# =========================================

def process_command(command):

    intent = detect_intent(command)

    print(f"\nDetected Intent: {intent}\n")

    # SAVE USER MESSAGE

    buddy_memory.set_context(
        "last_command",
        command
    )

    # =====================================
    # EMAIL AGENT
    # =====================================

    if intent == "email":

        response = (
            "Email agent activated."
        )

    # =====================================
    # CODING AGENT
    # =====================================

    elif intent == "coding":

        response = (
            "Coding agent activated."
        )

    # =====================================
    # SYSTEM AGENT
    # =====================================

    elif intent == "system":

        response = (
            "System control activated."
        )

    # =====================================
    # NORMAL CHAT
    # =====================================

    else:

        response = (
            "I understood your message."
        )

    # SAVE MEMORY

    buddy_memory.save_conversation(
        command,
        response
    )

    return response