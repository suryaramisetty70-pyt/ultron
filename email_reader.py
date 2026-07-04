import imaplib
import email
from datetime import datetime, timedelta
import email.utils

import os

EMAIL = os.getenv("GMAIL_USER")
PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def get_recent_emails():

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, "ALL")

        email_ids = messages[0].split()

        emails = []

        now = datetime.now()

        for e_id in email_ids[-10:]:

            status, msg_data = mail.fetch(e_id, "(RFC822)")

            for response_part in msg_data:

                if isinstance(response_part, tuple):

                    msg = email.message_from_bytes(response_part[1])

                    subject = msg["subject"]
                    from_ = msg["from"]

                    date_tuple = email.utils.parsedate_tz(msg["Date"])
                    if date_tuple:
                        email_time = datetime.fromtimestamp(
                            email.utils.mktime_tz(date_tuple)
                        )

                        if now - email_time <= timedelta(hours=3):

                            emails.append({
                                "from": from_,
                                "subject": subject
                            })

        mail.logout()
        return emails

    except:
        return []