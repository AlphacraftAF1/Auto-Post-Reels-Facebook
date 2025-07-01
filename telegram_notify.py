# telegram_notify.py
import requests
import os
import logging

logger = logging.getLogger(__name__)

def send_telegram(message):
    """Mengirim pesan notifikasi ke grup Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID tidak ditemukan di environment variables.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Pesan Telegram berhasil dikirim: {message}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal mengirim pesan Telegram: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Terjadi kesalahan tak terduga di send_telegram: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Contoh penggunaan (pastikan Anda memiliki token dan chat ID yang valid)
    # os.environ["TELEGRAM_BOT_TOKEN"] = "YOUR_BOT_TOKEN"
    # os.environ["TELEGRAM_CHAT_ID"] = "YOUR_CHAT_ID"
    # send_telegram("Halo dari bot autopost!")
    pass
