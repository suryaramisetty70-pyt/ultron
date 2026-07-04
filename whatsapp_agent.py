import pywhatkit

def send_whatsapp_message(phone, message):

    try:
        pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=10)
        return "Message sent on WhatsApp"
    except:
        return "Failed to send WhatsApp message"