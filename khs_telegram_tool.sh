KHS Telegram Tool — Termux Edition

1. ដំឡើង Dependencies

pkg update -y
pkg install python nano -y
pip install telethon

2. បង្កើតឯកសារ

nano khs_telegram_tool.sh

បញ្ចូលកូដខាងក្រោម៖

#!/data/data/com.termux/files/usr/bin/bash

set -u

APP_DIR="$HOME/khs-telegram-tool"
mkdir -p "$APP_DIR"
cd "$APP_DIR" || exit 1

clear

BLUE='\033[1;34m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${BLUE}"
echo "=================================="
echo "       KHS TELEGRAM TOOL"
echo "          Termux Edition"
echo "=================================="
echo -e "${RESET}"

echo "1. Install / Update"
echo "2. Configure Telegram API"
echo "3. Login & Open Telegram Menu"
echo "4. Exit"
echo

read -r -p "Select option: " choice

case "$choice" in
  1)
    pkg update -y
    pkg install python -y
    python -m pip install telethon
    echo -e "${GREEN}Installation finished.${RESET}"
    ;;

  2)
    echo "Get your API credentials from:"
    echo "https://my.telegram.org"
    echo
    read -r -p "API ID: " API_ID
    read -r -s -p "API HASH: " API_HASH
    echo

    if [[ ! "$API_ID" =~ ^[0-9]+$ ]] || [[ -z "$API_HASH" ]]; then
      echo "Invalid API credentials."
      exit 1
    fi

    umask 077
    printf '%s\n%s\n' "$API_ID" "$API_HASH" > "$APP_DIR/api.conf"
    chmod 600 "$APP_DIR/api.conf"
    echo "API credentials saved locally."
    ;;

  3)
    if [[ ! -f "$APP_DIR/api.conf" ]]; then
      echo "Please configure Telegram API first."
      exit 1
    fi

    API_ID="$(sed -n '1p' "$APP_DIR/api.conf")"
    API_HASH="$(sed -n '2p' "$APP_DIR/api.conf")"

    export KHS_API_ID="$API_ID"
    export KHS_API_HASH="$API_HASH"

    python - <<'PY'
import os
import asyncio
from telethon import TelegramClient

api_id = int(os.environ["KHS_API_ID"])
api_hash = os.environ["KHS_API_HASH"]

async def main():
    client = TelegramClient("khs_session", api_id, api_hash)
    await client.start()

    try:
        while True:
            print("\n=== KHS TELEGRAM MENU ===")
            print("1. Account information")
            print("2. List recent chats")
            print("3. Send a message")
            print("4. Export chat list")
            print("5. Logout")
            print("0. Exit")

            choice = input("Select: ").strip()

            if choice == "1":
                me = await client.get_me()
                print("Name:", me.first_name)
                print("Username:", me.username)
                print("User ID:", me.id)

            elif choice == "2":
                dialogs = await client.get_dialogs(limit=30)
                for i, dialog in enumerate(dialogs, 1):
                    print(f"{i}. {dialog.name} (ID: {dialog.id})")

            elif choice == "3":
                target = input("Recipient username or chat ID: ").strip()
                message = input("Message: ").strip()
                confirm = input("Send this message? (yes/no): ")
                if confirm.lower() == "yes" and message:
                    await client.send_message(target, message)
                    print("Message sent.")
                else:
                    print("Cancelled.")

            elif choice == "4":
                dialogs = await client.get_dialogs(limit=500)
                with open("chats.txt", "w", encoding="utf-8") as f:
                    for d in dialogs:
                        f.write(f"{d.name}\t{d.id}\n")
                print("Saved to chats.txt")

            elif choice == "5":
                await client.log_out()
                print("Logged out.")
                break

            elif choice == "0":
                break

            else:
                print("Invalid option.")

    finally:
        await client.disconnect()

asyncio.run(main())
PY
    ;;

  4)
    exit 0
    ;;

  *)
    echo "Invalid option."
    ;;
esac
