# telegram_notify.py
import requests, os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram token or chat ID not set. Skipping Telegram notification.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        print("Notifikasi Telegram berhasil dikirim.")
    except requests.exceptions.RequestException as e:
        print(f"Telegram error (RequestException): {e}")
        if e.response is not None:
            print(f"Telegram response error: {e.response.text}")
    except Exception as e:
        print(f"Telegram error (General Exception): {e}")

# Contoh penggunaan (bisa dihapus nanti)
if __name__ == "__main__":
    # Untuk menjalankan ini, Anda perlu mengatur environment variables:
    # export TELEGRAM_BOT_TOKEN="your_bot_token"
    # export TELEGRAM_CHAT_ID="your_chat_id"
    # send_telegram("Testing notifikasi dari skrip lokal.")
    # send_telegram("<b>Ini</b> adalah pesan <i>HTML</i>.")
    pass
