import os.path
import base64
import pickle

from email.mime.text import MIMEText

from google.auth.transport.requests import Request

from google.oauth2.credentials import Credentials

from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build

# ==========================================
# SCOPES
# ==========================================

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]

# ==========================================
# AUTH
# ==========================================

def gmail_auth():

    creds = None

    if os.path.exists("token.pickle"):

        with open("token.pickle", "rb") as token:

            creds = pickle.load(token)

    if not creds or not creds.valid:

        if (
            creds
            and creds.expired
            and creds.refresh_token
        ):

            creds.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file(

                "credentials.json",

                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        with open("token.pickle", "wb") as token:

            pickle.dump(creds, token)

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    return service

# ==========================================
# GET EMAIL SUMMARY
# ==========================================

def get_email_summary():

    try:

        service = gmail_auth()

        results = (
            service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=10
            )
            .execute()
        )

        messages = results.get(
            "messages",
            []
        )

        unread_count = len(messages)

        return (
            f"You have "
            f"{unread_count} "
            f"recent emails."
        )

    except Exception as e:

        return f"Summary Error: {e}"

# ==========================================
# READ IMPORTANT EMAILS
# ==========================================

def read_important_emails():

    try:

        service = gmail_auth()

        results = (
            service.users()
            .messages()
            .list(
                userId="me",
                labelIds=["INBOX"],
                maxResults=5
            )
            .execute()
        )

        messages = results.get(
            "messages",
            []
        )

        if not messages:

            return (
                "No important emails found."
            )

        output = []

        for msg in messages:

            message = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg["id"]
                )
                .execute()
            )

            headers = (
                message["payload"]
                .get("headers", [])
            )

            subject = "No Subject"

            for h in headers:

                if h["name"] == "Subject":

                    subject = h["value"]

            output.append(subject)

        return (
            "Important emails are: "
            + ", ".join(output)
        )

    except Exception as e:

        return f"Read Error: {e}"

# ==========================================
# SEARCH EMAILS
# ==========================================

def search_emails(keyword):

    try:

        service = gmail_auth()

        results = (
            service.users()
            .messages()
            .list(
                userId="me",
                q=keyword,
                maxResults=5
            )
            .execute()
        )

        messages = results.get(
            "messages",
            []
        )

        if not messages:

            return (
                "No emails found."
            )

        output = []

        for msg in messages:

            message = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg["id"]
                )
                .execute()
            )

            headers = (
                message["payload"]
                .get("headers", [])
            )

            subject = "No Subject"

            for h in headers:

                if h["name"] == "Subject":

                    subject = h["value"]

            output.append(subject)

        return (
            "Found emails: "
            + ", ".join(output)
        )

    except Exception as e:

        return f"Search Error: {e}"

# ==========================================
# SEND EMAIL
# ==========================================

def send_email(to, subject, body):

    try:

        service = gmail_auth()

        message = MIMEText(body)

        message["to"] = to

        message["subject"] = subject

        raw = base64.urlsafe_b64encode(

            message.as_bytes()

        ).decode()

        send_message = {
            "raw": raw
        }

        service.users().messages().send(

            userId="me",

            body=send_message

        ).execute()

        return (
            "Email sent successfully."
        )

    except Exception as e:

        return (
            f"Send Email Error: {e}"
        )