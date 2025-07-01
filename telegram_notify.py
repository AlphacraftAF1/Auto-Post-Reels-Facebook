# telegram_notify.py
import requests, os
import logging

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # Ini chat ID tempat notifikasi dikirim

def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("Telegram token or chat ID not set. Skipping Telegram notification.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        logger.info("Telegram notification sent successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram error (RequestException): {e}", exc_info=True)
        if e.response is not None:
            logger.error(f"Telegram response error: {e.response.text}")
    except Exception as e:
        logger.error(f"Telegram error (General Exception): {e}", exc_info=True)

# Contoh penggunaan (bisa dihapus nanti)
if __name__ == "__main__":
    pass
