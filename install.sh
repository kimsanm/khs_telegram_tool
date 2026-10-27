#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

APP_DIR="${HOME}/khs-telegram-tool"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

echo "=== KHS Telegram Tool installer ==="
pkg update -y
pkg install -y python git
python -m pip install --upgrade pip
python -m pip install "telethon>=1.36,<2" "requests>=2.31,<3"

mkdir -p exports logs
chmod 700 "$APP_DIR" "$APP_DIR/exports" "$APP_DIR/logs"

if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
  echo "Created $APP_DIR/.env from template."
fi

chmod +x khs.sh
echo
echo "Installed to: $APP_DIR"
echo "Next:"
echo "  cd \"$APP_DIR\""
echo "  nano .env"
echo "  ./khs.sh"
