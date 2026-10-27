#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

if ! command -v python >/dev/null 2>&1; then
  echo "Python not found. Run: bash install.sh"
  exit 1
fi

while true; do
  clear
  printf '\033[1;36m'
  echo "======================================"
  echo "          KHS TELEGRAM TOOL"
  echo "       Android Termux Edition"
  echo "======================================"
  printf '\033[0m'
  echo "1. Setup / check configuration"
  echo "2. Login to Telegram user account"
  echo "3. Account information"
  echo "4. List recent chats"
  echo "5. Send a message (confirmation required)"
  echo "6. Export chat list to CSV"
  echo "7. Bot status / get bot information"
  echo "8. Run bot auto-reply polling"
  echo "9. List channel/group administrators"
  echo "10. Promote/demote admin (bot must have rights)"
  echo "11. Logout user account"
  echo "0. Exit"
  echo
  read -r -p "Choose: " choice
  case "$choice" in
    1) python app.py setup ;;
    2) python app.py login ;;
    3) python app.py account ;;
    4) python app.py chats ;;
    5) python app.py send ;;
    6) python app.py export ;;
    7) python app.py bot-info ;;
    8) python app.py bot-poll ;;
    9) python app.py admins ;;
    10) python app.py admin-change ;;
    11) python app.py logout ;;
    0) echo "Bye."; exit 0 ;;
    *) echo "Invalid choice." ;;
  esac
  echo
  read -r -p "Press Enter to return to menu..." _
done
