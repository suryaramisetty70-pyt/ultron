import base64
import os
import pickle
import asyncio

from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from core.base_agent import BaseAgent
from core.event_bus import EventBus
from core.command_queue import CommandQueue


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]


class GmailAgent(BaseAgent):

    AGENT_ID = "gmail_agent"

    def __init__(
        self,
        event_bus,
        command_queue,
        credentials_path="credentials.json",
        token_path="token.pickle"
    ):

        super().__init__(
            agent_id=self.AGENT_ID,
            event_bus=event_bus,
            command_queue=command_queue
        )

        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    # ==========================================
    # START
    # ==========================================

    async def on_start(self):

        self.authenticate()

        self.register_intent(
            "check_inbox",
            self.check_inbox
        )

        self.register_intent(
            "important_emails",
            self.important_emails
        )

        self.register_intent(
            "send_email",
            self.send_email
        )

    # ==========================================
    # STOP
    # ==========================================

    async def on_stop(self):

        pass

    # ==========================================
    # AUTHENTICATION
    # ==========================================

    def authenticate(self):

        creds = None

        if os.path.exists(self.token_path):

            with open(
                self.token_path,
                "rb"
            ) as token:

                creds = pickle.load(token)

        if not creds or not creds.valid:

            if creds and creds.expired and creds.refresh_token:

                creds.refresh(Request())

            else:

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    SCOPES
                )

                creds = flow.run_local_server(
                    port=0
                )

            with open(
                self.token_path,
                "wb"
            ) as token:

                pickle.dump(
                    creds,
                    token
                )

        self.service = build(
            "gmail",
            "v1",
            credentials=creds
        )

    # ==========================================
    # HANDLE COMMAND
    # ==========================================

    async def handle_command(
        self,
        command
    ):

        intent = command.get(
            "intent"
        )

        payload = command.get(
            "payload",
            {}
        )

        if intent in self.intent_handlers:

            return await self.intent_handlers[
                intent
            ](payload)

        return {
            "success": False,
            "message": "Unknown Gmail intent"
        }

    # ==========================================
    # CHECK INBOX
    # ==========================================

    async def check_inbox(
        self,
        payload
    ):

        try:

            max_results = payload.get(
                "max_results",
                10
            )

            results = self.service.users().messages().list(
                userId="me",
                maxResults=max_results,
                labelIds=["INBOX"]
            ).execute()

            messages = results.get(
                "messages",
                []
            )

            email_list = []

            for msg in messages:

                message = self.service.users().messages().get(
                    userId="me",
                    id=msg["id"]
                ).execute()

                headers = message[
                    "payload"
                ][
                    "headers"
                ]

                subject = "No Subject"

                for header in headers:

                    if header["name"] == "Subject":

                        subject = header["value"]

                email_list.append(
                    subject
                )

            return {
                "success": True,
                "emails": email_list
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }

    # ==========================================
    # IMPORTANT EMAILS
    # ==========================================

    async def important_emails(
        self,
        payload
    ):

        try:

            results = self.service.users().messages().list(
                userId="me",
                labelIds=["IMPORTANT"],
                maxResults=5
            ).execute()

            messages = results.get(
                "messages",
                []
            )

            important = []

            for msg in messages:

                message = self.service.users().messages().get(
                    userId="me",
                    id=msg["id"]
                ).execute()

                headers = message[
                    "payload"
                ][
                    "headers"
                ]

                subject = "No Subject"

                for header in headers:

                    if header["name"] == "Subject":

                        subject = header["value"]

                important.append(
                    subject
                )

            return {
                "success": True,
                "important_emails": important
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }

    # ==========================================
    # SEND EMAIL
    # ==========================================

    async def send_email(
        self,
        payload
    ):

        try:

            to = payload.get("to")

            subject = payload.get("subject")

            body = payload.get("body")

            message = MIMEText(body)

            message["to"] = to
            message["subject"] = subject

            raw = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()

            send_message = {
                "raw": raw
            }

            self.service.users().messages().send(
                userId="me",
                body=send_message
            ).execute()

            return {
                "success": True,
                "message": "Email sent successfully"
            }

        except Exception as e:

            return {
                "success": False,
                "message": str(e)
            }


# ==========================================
# LEGACY COMPATIBILITY LAYER
# ==========================================

_dummy_event_bus = EventBus()

_dummy_command_queue = CommandQueue()

_gmail_agent = GmailAgent(
    _dummy_event_bus,
    _dummy_command_queue
)

try:

    asyncio.run(
        _gmail_agent.on_start()
    )

except:

    pass


def get_email_summary():

    result = asyncio.run(

        _gmail_agent.check_inbox(
            {
                "max_results": 10
            }
        )
    )

    if result["success"]:

        return (
            f"You have "
            f"{len(result['emails'])} "
            f"recent emails."
        )

    return "Unable to fetch emails."


def get_important_emails():

    result = asyncio.run(

        _gmail_agent.important_emails(
            {}
        )
    )

    if result["success"]:

        return (
            "Important emails are: "
            + ", ".join(
                result["important_emails"]
            )
        )

    return "Unable to fetch important emails."


def read_important_emails():

    return get_important_emails()


def read_email_summary():

    return get_email_summary()