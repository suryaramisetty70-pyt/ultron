def detect_intent(command: str):

    command = command.lower()

    if any(word in command for word in ["send", "message", "call"]):
        return "communication"

    elif any(word in command for word in ["email", "mail"]):
        return "email"

    elif any(word in command for word in ["search", "google", "find"]):
        return "web"

    elif any(word in command for word in ["code", "program", "developer"]):
        return "coding"

    elif any(word in command for word in ["open", "volume", "shutdown", "restart"]):
        return "system"

    else:
        return "chat"