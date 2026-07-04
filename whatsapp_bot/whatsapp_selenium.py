from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

import time


def send_whatsapp_message(phone, message):

    try:

        options = webdriver.ChromeOptions()

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        # OPEN WHATSAPP WEB
        driver.get("https://web.whatsapp.com")

        print("\nLogin to WhatsApp if needed...")
        time.sleep(25)

        # OPEN CHAT
        url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"

        driver.get(url)

        print("Opening chat...")
        time.sleep(15)

        # FIND MESSAGE BOX
        message_box = driver.find_element(
            By.XPATH,
            '//div[@contenteditable="true"]'
        )

        # PRESS ENTER
        message_box.send_keys(Keys.ENTER)

        print("✅ Message Sent Successfully")

    except Exception as e:

        print("ERROR:", e)