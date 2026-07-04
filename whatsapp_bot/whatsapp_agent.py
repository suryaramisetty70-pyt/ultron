import pywhatkit
import time
import pyautogui


def send_whatsapp_message(phone, message):

    try:

        # OPEN WHATSAPP WEB + TYPE MESSAGE
        pywhatkit.sendwhatmsg_instantly(
            phone,
            message,
            wait_time=15,
            tab_close=True
        )

        # SMALL WAIT
        time.sleep(5)

        # PRESS ENTER
        pyautogui.press("enter")

        return "WhatsApp message sent successfully"

    except Exception as e:

        print(e)
        return "Failed to send WhatsApp message"