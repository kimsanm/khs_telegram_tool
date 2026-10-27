# KHS Telegram Tool — Android Termux

A Bash menu wrapper around Python utilities using:
- Telethon for your own Telegram user account (MTProto API)
- Official Telegram Bot HTTP API for bot commands and channel/group admin queries

## Features
- User account login and basic account information
- List recent chats/dialogs
- Send a message after an explicit `SEND` confirmation
- Export up to 1,000 dialogs to a local CSV
- Bot identity check (`getMe`)
- Simple long-polling auto-reply bot (`/start`, `/help`, `/id`, `/echo`)
- List administrators in a channel/group where the bot has access
- Conservative admin workflow with confirmation; promotion intentionally directs you to Telegram's native UI to choose precise rights
- Local file permissions and basic rate-limit handling

## Requirements
- Android with Termux installed from a trusted source
- Internet connection
- For user-account features: API ID and API HASH from https://my.telegram.org
- For bot features: bot token from @BotFather; add the bot to your group/channel and grant only the rights it needs

## Install
Copy this project folder to Termux home, then:

```bash
cd ~/khs-telegram-tool
bash install.sh
```

If you have the ZIP in Downloads, grant storage access first if needed:

```bash
termux-setup-storage
cp ~/storage/downloads/khs_telegram_tool_termux.zip ~/
cd ~
unzip khs_telegram_tool_termux.zip
cd khs_telegram_tool
bash install.sh
```

## Configure
```bash
nano .env
```

Fill only the credentials you need:
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `TELEGRAM_BOT_TOKEN`
- `BOT_ALLOWED_USER_IDS` (recommended; comma-separated numeric user IDs)
- `ACTION_DELAY_SECONDS=2`

Protect the file:
```bash
chmod 600 .env
```

Never share `.env`, the `khs_user_session.session` file, OTP codes, or login QR/session data. Do not commit them to Git.

## Run
```bash
./khs.sh
```

Choose option 2 to log into your personal Telegram account. Telegram may ask for your phone number, login code, and two-step verification password. Enter them only in your own Termux session.

## Bot setup
1. Create a bot with @BotFather.
2. Put its token in `.env`.
3. Add the bot to a group/channel as needed.
4. Grant only the permissions it needs.
5. Set `BOT_ALLOWED_USER_IDS` to your numeric Telegram user ID(s), especially if running polling privately.
6. Choose bot status or polling from the menu.

A bot cannot arbitrarily message users who have never started it. Channel/group admin operations require the bot to be present and have the required rights. Telegram API errors and rate limits can still occur.

## Exports and sessions
- CSV exports are written under `exports/`.
- The user session is stored locally in `khs_user_session.session`.
- Keep your phone locked and avoid backups to untrusted locations.
- To log out, use menu option 11.
- To remove local files manually, stop the tool first, then carefully remove the session and exports yourself.

## Safety and limitations
- Use this only with your own account and chats/groups where you have permission.
- No scraping of private data, mass unsolicited messaging, bulk member adding, or rate-limit evasion.
- This is a starter project, not a formally audited security product.
- The admin promotion function intentionally does not assign broad permissions automatically. Use Telegram's own admin UI to select the exact rights.
- Use Telegram's official API documentation: https://core.telegram.org/bots/api and https://core.telegram.org/api/obtaining_api_id
