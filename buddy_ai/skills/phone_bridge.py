"""
The Omnichannel Control Array
Allows the user to control Ultron remotely from their phone via Email, Telegram, Discord, or Web.
"""

import multiprocessing
import os
import time
from dotenv import load_dotenv

def run_email_bridge():
    import imaplib
    import email
    import subprocess
    from buddy_ai.skills.email_agent import send_email
    
    load_dotenv()
    user = os.getenv("GMAIL_ADDRESS")
    pwd = os.getenv("GMAIL_APP_PASSWORD")
    
    print("[Omni-Bridge] Email Listener Active.")
    
    while True:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, pwd)
            mail.select("inbox")
            
            # Search for unread emails with the command subject
            status, messages = mail.search(None, '(UNSEEN SUBJECT "[ULTRON COMMAND]")')
            
            if status == "OK":
                for num in messages[0].split():
                    # Fetch the email body
                    res, msg_data = mail.fetch(num, '(RFC822)')
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                            else:
                                body = msg.get_payload(decode=True).decode()
                                
                            command_to_run = body.strip()
                            print(f"[Omni-Bridge] Received Email Command: {command_to_run}")
                            
                            # Execute the command on the OS
                            try:
                                output = subprocess.check_output(command_to_run, shell=True, text=True, stderr=subprocess.STDOUT)
                            except subprocess.CalledProcessError as e:
                                output = f"ERROR executing command:\n{e.output}"
                                
                            # Send the results back to the phone
                            send_email(user, "ULTRON COMMAND RESULT", output)
                            
                            # Delete the command email to clean up
                            mail.store(num, '+FLAGS', '\\Deleted')
            mail.expunge()
            mail.logout()
        except Exception as e:
            pass
            
        time.sleep(10) # Poll every 10 seconds

def run_telegram_bridge():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return
        
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    import subprocess
    
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        cmd = update.message.text
        try:
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            output = f"Error:\n{e.output}"
        
        # Telegram max message length is 4096
        await update.message.reply_text(output[:4000])

    print("[Omni-Bridge] Telegram Hacker Bot Active.")
    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

def run_discord_bridge():
    load_dotenv()
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        return
        
    import discord
    import subprocess
    
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'[Omni-Bridge] Discord Server Active as {client.user}')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
            
        cmd = message.content
        try:
            output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            output = f"Error:\n{e.output}"
            
        await message.channel.send(f"```\n{output[:1900]}\n```")
        
    client.run(token)

def run_web_bridge():
    load_dotenv()
    token = os.getenv("NGROK_AUTH_TOKEN")
    if not token:
        return
        
    from flask import Flask
    from pyngrok import ngrok, conf
    
    conf.get_default().auth_token = token
    app = Flask(__name__)
    
    @app.route("/")
    def index():
        return "<h1>Ultron Remote Access Protocol Active</h1>"
        
    public_url = ngrok.connect(5000)
    print(f"[Omni-Bridge] Web Dashboard Active: {public_url}")
    app.run(port=5000, use_reloader=False)

def start_omnichannel_array():
    """
    Launches all 4 remote phone bridges in the background.
    They will automatically sleep if their respective API keys are missing.
    """
    load_dotenv()
    print("[Ultron Omni-Bridge] Initializing remote arrays...")
    
    if os.getenv("GMAIL_ADDRESS") and os.getenv("GMAIL_APP_PASSWORD"):
        multiprocessing.Process(target=run_email_bridge, daemon=True).start()
        
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        multiprocessing.Process(target=run_telegram_bridge, daemon=True).start()
        
    if os.getenv("DISCORD_BOT_TOKEN"):
        multiprocessing.Process(target=run_discord_bridge, daemon=True).start()
        
    if os.getenv("NGROK_AUTH_TOKEN"):
        multiprocessing.Process(target=run_web_bridge, daemon=True).start()
