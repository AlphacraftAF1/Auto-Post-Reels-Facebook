import os
import json
import time
import logging
from datetime import datetime

# Impor modul kustom
import telegram_fetcher
import gemini_processor
import video_utils
import facebook_uploader

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Variabel Lingkungan ---
# Pastikan variabel-variabel ini diatur di lingkungan GitHub Actions Anda
FB_ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN')
FB_PAGE_ID = os.getenv('FB_PAGE_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID') # Pastikan ini adalah string, bukan integer

# Konversi TELEGRAM_CHAT_ID ke integer jika perlu, atau biarkan sebagai string jika API mengharapkan string
try:
    TELEGRAM_CHAT_ID = int(TELEGRAM_CHAT_ID)
except (ValueError, TypeError):
    logging.error("TELEGRAM_CHAT_ID tidak valid. Pastikan ini adalah ID numerik.")
    exit(1)

# --- Nama File Konfigurasi ---
POSTED_MEDIA_FILE = 'posted_media.json'
LAST_UPDATE_OFFSET_FILE = 'last_update_offset.txt'

# --- Fungsi Pembantu ---
def load_posted_media():
    """Memuat daftar media yang sudah diposting dari file JSON."""
    if os.path.exists(POSTED_MEDIA_FILE):
        with open(POSTED_MEDIA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logging.warning(f"File {POSTED_MEDIA_FILE} rusak atau kosong. Membuat yang baru.")
                return {}
    return {}

def save_posted_media(posted_media_data):
    """Menyimpan daftar media yang sudah diposting ke file JSON."""
    with open(POSTED_MEDIA_FILE, 'w') as f:
        json.dump(posted_media_data, f, indent=4)

def load_last_update_offset():
    """Memuat offset update terakhir dari file teks."""
    if os.path.exists(LAST_UPDATE_OFFSET_FILE):
        with open(LAST_UPDATE_OFFSET_FILE, 'r') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                logging.warning(f"File {LAST_UPDATE_OFFSET_FILE} berisi nilai tidak valid. Mengatur offset ke 0.")
                return 0
    return 0

def save_last_update_offset(offset):
    """Menyimpan offset update terakhir ke file teks."""
    with open(LAST_UPDATE_OFFSET_FILE, 'w') as f:
        f.write(str(offset))

def send_telegram_notification(message):
    """Mengirim notifikasi ke Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Token bot Telegram atau ID chat tidak diatur. Tidak dapat mengirim notifikasi.")
        return

    # Menggunakan fungsi dari telegram_fetcher untuk mengirim pesan
    try:
        telegram_fetcher.send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
        logging.info(f"Notifikasi Telegram terkirim: {message}")
    except Exception as e:
        logging.error(f"Gagal mengirim notifikasi Telegram: {e}")

# --- Fungsi Utama AutoPost ---
def run_autopost():
    """Menjalankan alur utama auto-posting."""
    if not all([FB_ACCESS_TOKEN, FB_PAGE_ID, GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        logging.error("Variabel lingkungan tidak lengkap. Pastikan semua variabel diatur.")
        send_telegram_notification("❌ Gagal: Variabel lingkungan tidak lengkap untuk AutoPost Facebook.")
        return

    logging.info("Memulai siklus AutoPost Facebook Reels...")
    send_telegram_notification("🚀 Memulai siklus AutoPost Facebook Reels...")

    posted_media = load_posted_media()
    last_offset = load_last_update_offset()

    try:
        logging.info(f"Mengambil media terbaru dari Telegram (offset: {last_offset})...")
        # Ambil hingga 50 update dari Telegram
        new_media_updates, new_last_offset = telegram_fetcher.fetch_new_media(
            TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, last_offset, posted_media
        )

        if not new_media_updates:
            logging.info("Tidak ada media baru yang ditemukan untuk diposting.")
            send_telegram_notification("ℹ️ Tidak ada media baru yang ditemukan untuk diposting.")
            save_last_update_offset(new_last_offset) # Simpan offset terbaru meskipun tidak ada media
            return

        logging.info(f"Ditemukan {len(new_media_updates)} media baru untuk diproses.")

        for media_info in new_media_updates:
            file_unique_id = media_info['file_unique_id']
            media_path = media_info['file_path']
            original_caption = media_info.get('caption', '')
            media_type = media_info['type'] # 'video' atau 'photo'

            logging.info(f"Memproses media: {media_path} (ID Unik: {file_unique_id})")

            # 3. Cek Caption (Kosong / Spam / Siap Posting)
            logging.info("Memproses caption...")
            processed_caption = gemini_processor.process_caption(original_caption, GEMINI_API_KEY)
            logging.info(f"Caption akhir: {processed_caption}")

            # 4. Deteksi Reels / Biasa / Foto
            is_reel = False
            if media_type == 'video':
                logging.info("Menganalisis video untuk deteksi Reels...")
                if video_utils.is_reel(media_path):
                    is_reel = True
                    logging.info("Video dideteksi sebagai Reels.")
                else:
                    logging.info("Video dideteksi sebagai Video Reguler.")
            else:
                logging.info("Media dideteksi sebagai Foto.")

            # 5. Upload ke Facebook
            logging.info(f"Mengunggah media ke Facebook sebagai {'Reels' if is_reel else media_type.capitalize()}...")
            post_id = None
            try:
                if is_reel:
                    post_id = facebook_uploader.upload_reel(
                        media_path, processed_caption, FB_ACCESS_TOKEN, FB_PAGE_ID
                    )
                elif media_type == 'video':
                    post_id = facebook_uploader.upload_video(
                        media_path, processed_caption, FB_ACCESS_TOKEN, FB_PAGE_ID
                    )
                elif media_type == 'photo':
                    post_id = facebook_uploader.upload_photo(
                        media_path, processed_caption, FB_ACCESS_TOKEN, FB_PAGE_ID
                    )

                if post_id:
                    logging.info(f"Media berhasil diunggah! Post ID: {post_id}")
                    send_telegram_notification(
                        f"✅ Berhasil posting ke Facebook!\n"
                        f"Tipe: {'Reels' if is_reel else media_type.capitalize()}\n"
                        f"Caption: {processed_caption[:100]}...\n"
                        f"Post ID: {post_id}"
                    )
                    # Simpan ke posted_media.json
                    posted_media[file_unique_id] = {
                        'caption': processed_caption,
                        'post_id': post_id,
                        'posted_at': datetime.now().isoformat(),
                        'media_type': media_type,
                        'is_reel': is_reel
                    }
                    save_posted_media(posted_media)
                else:
                    logging.error("Gagal mendapatkan Post ID setelah unggah.")
                    send_telegram_notification(
                        f"❌ Gagal posting ke Facebook untuk media ID unik: {file_unique_id}. Post ID tidak ditemukan."
                    )

            except Exception as e:
                logging.error(f"Terjadi kesalahan saat mengunggah media {file_unique_id}: {e}")
                send_telegram_notification(
                    f"❌ Gagal posting ke Facebook untuk media ID unik: {file_unique_id}.\n"
                    f"Kesalahan: {str(e)[:200]}..."
                )
            finally:
                # 6. Cleanup: Hapus file lokal setelah selesai
                if os.path.exists(media_path):
                    os.remove(media_path)
                    logging.info(f"File lokal dihapus: {media_path}")

        # Simpan offset update_id terakhir
        save_last_update_offset(new_last_offset)
        logging.info(f"Siklus AutoPost selesai. Offset update terakhir disimpan: {new_last_offset}")
        send_telegram_notification("✅ Siklus AutoPost Facebook Reels selesai.")

    except Exception as e:
        logging.error(f"Terjadi kesalahan fatal dalam siklus AutoPost: {e}", exc_info=True)
        send_telegram_notification(
            f"❌ Terjadi kesalahan fatal dalam siklus AutoPost Facebook Reels: {str(e)[:200]}..."
        )

if __name__ == "__main__":
    run_autopost()
