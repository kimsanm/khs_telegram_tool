#!/usr/bin/env python3
"""KHS Telegram Tool: personal account utilities + official Telegram Bot API features."""
import asyncio
import csv
import os
import sys
import time
from pathlib import Path

import requests
from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
SESSION_FILE = ROOT / "khs_user_session"
EXPORT_DIR = ROOT / "exports"
LOG_DIR = ROOT / "logs"
EXPORT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)


def load_env():
    """Small .env reader, avoids extra dependency and never prints secrets."""
    if not ENV_FILE.exists():
        raise RuntimeError("Missing .env. Copy .env.example to .env and fill credentials.")
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def config():
    load_env()
    delay = float(os.getenv("ACTION_DELAY_SECONDS", "2") or "2")
    if delay < 1:
        delay = 1
    return delay


def get_api_credentials():
    load_env()
    api_id = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
    if not api_id.isdigit() or not api_hash:
        raise RuntimeError("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env. Get them from https://my.telegram.org")
    return int(api_id), api_hash


def get_bot_token():
    load_env()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN in .env using @BotFather.")
    return token


def bot_api(method, payload=None, token=None, timeout=25):
    token = token or get_bot_token()
    url = f"https://api.telegram.org/bot{token}/{method}"
    response = requests.post(url, json=payload or {}, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "Telegram Bot API error"))
    return data["result"]


async def make_client():
    api_id, api_hash = get_api_credentials()
    client = TelegramClient(str(SESSION_FILE), api_id, api_hash)
    await client.start()
    return client


def setup():
    load_env()
    print("Configuration file:", ENV_FILE)
    print("User API ID:", "configured" if os.getenv("TELEGRAM_API_ID") else "missing")
    print("User API HASH:", "configured" if os.getenv("TELEGRAM_API_HASH") else "missing")
    print("Bot token:", "configured" if os.getenv("TELEGRAM_BOT_TOKEN") else "optional / missing")
    print("Edit .env with: nano .env")
    print("API credentials: https://my.telegram.org")
    print("Bot token: create/manage your bot with @BotFather")


async def login():
    client = await make_client()
    me = await client.get_me()
    print(f"Logged in as {me.first_name} (ID {me.id}).")
    await client.disconnect()


async def account():
    client = await make_client()
    try:
        me = await client.get_me()
        print("Name:", me.first_name or "")
        print("Username:", ("@" + me.username) if me.username else "(none)")
        print("User ID:", me.id)
        print("Phone:", me.phone or "(not returned)")
        print("Bot account:", bool(me.bot))
    finally:
        await client.disconnect()


async def chats():
    client = await make_client()
    try:
        dialogs = await client.get_dialogs(limit=50)
        for i, d in enumerate(dialogs, 1):
            print(f"{i:>2}. {d.name} | id={d.id} | type={type(d.entity).__name__}")
        print(f"\nShowing {len(dialogs)} recent dialogs.")
    finally:
        await client.disconnect()


async def send_message():
    client = await make_client()
    try:
        target = input("Recipient username or chat ID (only where you may message): ").strip()
        message = input("Message: ").strip()
        if not target or not message:
            print("Recipient and message are required.")
            return
        print("\nPreview:")
        print("To:", target)
        print("Text:", message)
        if input("Type SEND to confirm: ").strip() != "SEND":
            print("Cancelled.")
            return
        delay = config()
        await asyncio.sleep(delay)
        await client.send_message(target, message)
        print("Message sent.")
    except FloodWaitError as exc:
        print(f"Telegram rate limit: wait {exc.seconds} seconds before retrying.")
    except RPCError as exc:
        print("Telegram rejected the request:", str(exc))
    finally:
        await client.disconnect()


async def export_chats():
    client = await make_client()
    try:
        dialogs = await client.get_dialogs(limit=1000)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        path = EXPORT_DIR / f"chats_{stamp}.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "chat_id", "entity_type", "username"])
            for d in dialogs:
                entity = d.entity
                writer.writerow([
                    d.name, d.id, type(entity).__name__,
                    getattr(entity, "username", "") or ""
                ])
        try:
            path.chmod(0o600)
        except OSError:
            pass
        print(f"Exported {len(dialogs)} dialogs to {path}")
    finally:
        await client.disconnect()


def bot_info():
    result = bot_api("getMe")
    print("Bot name:", result.get("first_name"))
    print("Username:", "@" + result.get("username", ""))
    print("Bot ID:", result.get("id"))
    print("Can join groups:", result.get("can_join_groups"))
    print("Can read all group messages:", result.get("can_read_all_group_messages"))


def allowed_ids():
    raw = os.getenv("BOT_ALLOWED_USER_IDS", "").strip()
    return {x.strip() for x in raw.split(",") if x.strip()}


def bot_poll():
    """Long-polling bot with basic allow-list support and /start /help /id /echo."""
    token = get_bot_token()
    allowed = allowed_ids()
    offset = None
    print("Bot polling started. Press Ctrl+C to stop.")
    print("For private use, set BOT_ALLOWED_USER_IDS in .env.")
    while True:
        params = {"timeout": 25, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates"
            r = requests.get(url, params=params, timeout=35)
            r.raise_for_status()
            payload = r.json()
            if not payload.get("ok"):
                raise RuntimeError(payload.get("description", "getUpdates failed"))
            for update in payload.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message") or {}
                chat = msg.get("chat") or {}
                sender = msg.get("from") or {}
                text = (msg.get("text") or "").strip()
                uid = str(sender.get("id", ""))
                chat_id = chat.get("id")
                if not chat_id or not text:
                    continue
                if allowed and uid not in allowed:
                    continue
                if text.startswith("/start"):
                    reply = "KHS Telegram Bot is online. Commands: /help, /id, /echo <text>"
                elif text.startswith("/help"):
                    reply = "Commands: /start, /help, /id, /echo <text>. Admin tools require authorized bot rights."
                elif text.startswith("/id"):
                    reply = f"Your user ID: {uid}; chat ID: {chat_id}"
                elif text.startswith("/echo "):
                    reply = text[6:1000]
                else:
                    reply = "Received. Use /help for commands."
                time.sleep(max(1.0, float(os.getenv("ACTION_DELAY_SECONDS", "2") or "2")))
                bot_api("sendMessage", {"chat_id": chat_id, "text": reply}, token=token)
        except KeyboardInterrupt:
            print("\nBot stopped.")
            return
        except Exception as exc:
            print("Bot polling error:", str(exc))
            time.sleep(5)


def list_admins():
    token = get_bot_token()
    chat_id = input("Channel/group username or numeric chat ID: ").strip()
    if not chat_id:
        print("Chat ID is required.")
        return
    admins = bot_api("getChatAdministrators", {"chat_id": chat_id}, token=token)
    for item in admins:
        user = item.get("user", {})
        print(f"{user.get('first_name','')} @{user.get('username','')} id={user.get('id')} role={item.get('status')}")


def change_admin():
    token = get_bot_token()
    chat_id = input("Channel/group username or numeric chat ID: ").strip()
    user_id = input("Target user's numeric Telegram ID: ").strip()
    if not chat_id or not user_id.isdigit():
        print("Chat ID and numeric user ID are required.")
        return
    action = input("Action (promote/demote): ").strip().lower()
    if action not in {"promote", "demote"}:
        print("Cancelled: choose promote or demote.")
        return
    print("This only works if the bot is an administrator with the required rights.")
    print(f"Chat: {chat_id} | User ID: {user_id} | Action: {action}")
    if input("Type CONFIRM to continue: ").strip() != "CONFIRM":
        print("Cancelled.")
        return
    if action == "promote":
        # Conservative default: no admin permissions granted automatically.
        print("For safety, this tool does not grant broad admin permissions automatically.")
        print("Use Telegram's native admin UI to choose the exact rights, then retry demote if needed.")
        return
    result = bot_api("promoteChatMember", {
        "chat_id": chat_id, "user_id": int(user_id),
        "can_manage_chat": False, "can_delete_messages": False,
        "can_manage_video_chats": False, "can_restrict_members": False,
        "can_promote_members": False, "can_change_info": False,
        "can_invite_users": False, "can_post_messages": False,
        "can_edit_messages": False, "can_pin_messages": False,
        "can_manage_topics": False
    }, token=token)
    print("Demote request accepted:", result)


async def logout():
    if not SESSION_FILE.with_suffix(".session").exists():
        print("No local session file found.")
        return
    if input("Log out this saved Telegram session? Type LOGOUT: ").strip() != "LOGOUT":
        print("Cancelled.")
        return
    client = await make_client()
    try:
        await client.log_out()
        print("Logged out.")
    finally:
        await client.disconnect()


def main():
    if len(sys.argv) < 2:
        print("Usage: python app.py [setup|login|account|chats|send|export|bot-info|bot-poll|admins|admin-change|logout]")
        return
    action = sys.argv[1]
    try:
        if action == "setup": setup()
        elif action == "login": asyncio.run(login())
        elif action == "account": asyncio.run(account())
        elif action == "chats": asyncio.run(chats())
        elif action == "send": asyncio.run(send_message())
        elif action == "export": asyncio.run(export_chats())
        elif action == "bot-info": bot_info()
        elif action == "bot-poll": bot_poll()
        elif action == "admins": list_admins()
        elif action == "admin-change": change_admin()
        elif action == "logout": asyncio.run(logout())
        else: print("Unknown action.")
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as exc:
        print("Error:", str(exc))
        print("Check .env, internet connection, Telegram permissions, and app setup.")


if __name__ == "__main__":
    main()
