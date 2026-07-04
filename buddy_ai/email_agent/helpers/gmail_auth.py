# buddy_ai/email_agent/helpers/gmail_auth.py
# OAuth2 Gmail authentication with automatic token refresh
# Handles credentials securely, Windows-compatible

from __future__ import annotations
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger("buddy.email.auth")

# Gmail API scopes — modify scope requires user re-auth
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]

# Default credential file locations
DEFAULT_CREDENTIALS_DIR = Path.home() / ".buddy_ai" / "credentials"
CREDENTIALS_FILE = DEFAULT_CREDENTIALS_DIR / "gmail_credentials.json"
TOKEN_FILE = DEFAULT_CREDENTIALS_DIR / "gmail_token.json"


def ensure_credentials_dir() -> None:
    DEFAULT_CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)


def load_credentials() -> Optional[Credentials]:
    """Load saved credentials from disk."""
    ensure_credentials_dir()
    if not TOKEN_FILE.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), GMAIL_SCOPES)
        return creds
    except Exception as e:
        logger.warning(f"Failed to load saved credentials: {e}")
        return None


def save_credentials(creds: Credentials) -> None:
    """Persist credentials to disk for future sessions."""
    ensure_credentials_dir()
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    logger.info("Gmail credentials saved successfully")


def refresh_credentials(creds: Credentials) -> Credentials:
    """Refresh expired credentials using refresh token."""
    try:
        creds.refresh(Request())
        save_credentials(creds)
        logger.info("Gmail token refreshed successfully")
        return creds
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise


def run_oauth_flow() -> Credentials:
    """Run full OAuth2 flow — opens browser for user authorization."""
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Gmail credentials file not found at: {CREDENTIALS_FILE}\n"
            "Please download your OAuth credentials from Google Cloud Console\n"
            "and save them to that path."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), GMAIL_SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    save_credentials(creds)
    logger.info("OAuth2 flow completed — credentials saved")
    return creds


def get_valid_credentials() -> Credentials:
    """Get valid (refreshed if needed) credentials. Runs OAuth flow if none exist."""
    creds = load_credentials()
    if creds is None:
        logger.info("No saved credentials — starting OAuth2 flow")
        return run_oauth_flow()
    if creds.expired and creds.refresh_token:
        return refresh_credentials(creds)
    if not creds.valid:
        logger.warning("Credentials invalid — re-running OAuth2 flow")
        return run_oauth_flow()
    return creds


def build_gmail_service():
    """Build and return authenticated Gmail API service."""
    creds = get_valid_credentials()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    logger.info("Gmail API service built successfully")
    return service


async def build_gmail_service_async():
    """Async wrapper for building Gmail service (runs in thread pool)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, build_gmail_service)
