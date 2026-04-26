"""send_message.py — Send via Telegram Bot API or open WhatsApp Web"""
import os, json
from pathlib import Path


def send_message(parameters: dict, player=None) -> str:
    receiver = parameters.get("receiver", "")
    message  = parameters.get("message_text", "")
    platform = parameters.get("platform", "telegram").lower()

    if not message:
        return "No message text provided."

    if platform == "telegram":
        return _send_telegram(receiver, message)
    elif platform == "whatsapp":
        return _open_whatsapp(receiver, message)
    else:
        return f"Unknown platform: {platform}. Use telegram or whatsapp."


def _send_telegram(receiver: str, message: str) -> str:
    config_file = Path(__file__).resolve().parent.parent / "config" / "api_keys.json"
    try:
        cfg = json.loads(config_file.read_text())
        token   = cfg.get("telegram_bot_token", "")
        chat_id = cfg.get("telegram_chat_id", "") or receiver
        if not token:
            return ("Telegram not configured.\n"
                    "Add 'telegram_bot_token' and 'telegram_chat_id' to config/api_keys.json.\n"
                    "Get token from @BotFather on Telegram.")
        import requests
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        if resp.status_code == 200:
            return f"Telegram message sent to {receiver}: {message[:50]}"
        return f"Telegram error: {resp.text}"
    except Exception as e:
        return f"Telegram error: {e}"


def _open_whatsapp(receiver: str, message: str) -> str:
    import urllib.parse
    # Remove spaces/dashes from phone number
    phone = receiver.replace(" ", "").replace("-", "").replace("+", "")
    msg_encoded = urllib.parse.quote(message)
    url = f"https://api.whatsapp.com/send?phone={phone}&text={msg_encoded}"
    os.system(f"xdg-open '{url}' &")
    return f"Opened WhatsApp Web to send message to {receiver}"
