from groq import Groq
import json
import os

from gmail_agent import (
    get_email_summary,
    read_important_emails,
    search_emails,
    send_email
)

# ==========================================
# GROQ
# ==========================================

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY", "")
)

# ==========================================
# CONTACT DATABASE
# ==========================================

CONTACT_FILE = "contacts.json"

if not os.path.exists(CONTACT_FILE):

    with open(CONTACT_FILE, "w") as f:

        json.dump({}, f)

def save_contact(name, email):

    with open(CONTACT_FILE, "r") as f:

        contacts = json.load(f)

    contacts[name.lower()] = email

    with open(CONTACT_FILE, "w") as f:

        json.dump(contacts, f, indent=4)

def get_contact_email(name):

    with open(CONTACT_FILE, "r") as f:

        contacts = json.load(f)

    return contacts.get(name.lower())

# ==========================================
# STATES
# ==========================================

waiting_for_vtu = False

waiting_for_message = False

waiting_for_confirmation = False

waiting_for_contact_name = False

waiting_for_contact_vtu = False

current_email = ""

current_message = ""

current_contact_name = ""

# ==========================================
# AI CHAT
# ==========================================

def ai_chat(command):

    try:

        response = client.chat.completions.create(

            model="llama3-8b-8192",

            messages=[

                {
                    "role": "system",

                    "content": (
                        "You are Buddy AI. "
                        "Reply very briefly."
                    )
                },

                {
                    "role": "user",

                    "content": command
                }

            ],

            max_tokens=40
        )

        return (

            response
            .choices[0]
            .message
            .content
        )

    except:

        return (
            "AI unavailable."
        )

# ==========================================
# MAIN PROCESSOR
# ==========================================

def process_command(command):

    global waiting_for_vtu
    global waiting_for_message
    global waiting_for_confirmation

    global waiting_for_contact_name
    global waiting_for_contact_vtu

    global current_email
    global current_message

    global current_contact_name

    command = command.lower().strip()

    # ======================================
    # SAVE CONTACT NAME
    # ======================================

    if waiting_for_contact_name:

        current_contact_name = command

        waiting_for_contact_name = False

        waiting_for_contact_vtu = True

        return (
            "Tell me the VTU number."
        )

    # ======================================
    # SAVE CONTACT VTU
    # ======================================

    if waiting_for_contact_vtu:

        numbers = "".join(

            c for c in command

            if c.isdigit()
        )

        if not numbers:

            return (
                "Please say only the VTU number."
            )

        email = (
            f"vtu{numbers}"
            f"@veltech.edu.in"
        )

        save_contact(
            current_contact_name,
            email
        )

        waiting_for_contact_vtu = False

        return (
            f"Saved contact "
            f"{current_contact_name}"
        )

    # ======================================
    # VTU NUMBER MODE
    # ======================================

    if waiting_for_vtu:

        numbers = "".join(

            c for c in command

            if c.isdigit()
        )

        if not numbers:

            return (
                "Please say only the VTU number."
            )

        current_email = (
            f"vtu{numbers}"
            f"@veltech.edu.in"
        )

        waiting_for_vtu = False

        waiting_for_message = True

        return (
            f"Created {current_email}. "
            f"What message should I send?"
        )

    # ======================================
    # MESSAGE MODE
    # ======================================

    if waiting_for_message:

        current_message = command

        waiting_for_message = False

        waiting_for_confirmation = True

        return (
            "Should I send the email?"
        )

    # ======================================
    # CONFIRM SEND
    # ======================================

    if waiting_for_confirmation:

        if (
            "yes" in command
            or "send" in command
        ):

            result = send_email(

                current_email,

                "Buddy AI Message",

                current_message
            )

            waiting_for_confirmation = False

            current_email = ""
            current_message = ""

            return result

        else:

            waiting_for_confirmation = False

            current_email = ""
            current_message = ""

            return (
                "Email cancelled."
            )

    # ======================================
    # SAVE CONTACT
    # ======================================

    if (
        "save contact" in command
    ):

        waiting_for_contact_name = True

        return (
            "Tell me the contact name."
        )

    # ======================================
    # SEND TO CONTACT
    # ======================================

    if (
        "send to" in command
    ):

        name = (

            command
            .replace("send to", "")
            .strip()
        )

        email = get_contact_email(name)

        if not email:

            return (
                "Contact not found."
            )

        current_email = email

        waiting_for_message = True

        return (
            f"What message should I send to {name}?"
        )

    # ======================================
    # COLLEGE MODE
    # ======================================

    if (

        "college" in command

        or "vtu" in command
    ):

        waiting_for_vtu = True

        return (
            "Tell me the VTU number."
        )

    # ======================================
    # IMPORTANT EMAILS
    # ======================================

    if (
        "important" in command
    ):

        return read_important_emails()

    # ======================================
    # EMAIL SUMMARY
    # ======================================

    if (
        "summary" in command
    ):

        return get_email_summary()

    # ======================================
    # SEARCH EMAILS
    # ======================================

    if (
        "search" in command
        or "find" in command
    ):

        keyword = (

            command
            .replace("search", "")
            .replace("find", "")
            .strip()
        )

        return search_emails(keyword)

    # ======================================
    # EXIT
    # ======================================

    if (
        "exit" in command
    ):

        return "Goodbye sir."

    # ======================================
    # AI CHAT
    # ======================================

    return ai_chat(command)