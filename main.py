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
PENDING_MEDIA_FILE = 'pending_media.json' # File baru untuk antrean

# --- Batasan Posting per Run ---
MAX_POSTS_PER_RUN = 1 # Ubah nilai ini sesuai keinginan Anda (misal: 1, 2, atau 3)

# --- Fungsi Pembantu ---
def load_json_file(file_path):
    """Memuat data dari file JSON."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                logging.info(f"Memuat data dari: {os.path.abspath(file_path)}")
                return data
            except json.JSONDecodeError:
                logging.warning(f"File {file_path} rusak atau kosong. Membuat yang baru.")
                return [] if file_path == PENDING_MEDIA_FILE else {}
    logging.info(f"File {file_path} tidak ditemukan. Membuat yang baru.")
    return [] if file_path == PENDING_MEDIA_FILE else {}

def save_json_file(file_path, data):
    """Menyimpan data ke file JSON."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    logging.info(f"Data disimpan ke: {os.path.abspath(file_path)}")

def load_last_update_offset():
    """Memuat offset update terakhir dari file teks."""
    if os.path.exists(LAST_UPDATE_OFFSET_FILE):
        with open(LAST_UPDATE_OFFSET_FILE, 'r') as f:
            try:
                offset = int(f.read().strip())
                logging.info(f"Memuat offset terakhir dari: {os.path.abspath(LAST_UPDATE_OFFSET_FILE)} -> {offset}")
                return offset
            except ValueError:
                logging.warning(f"File {LAST_UPDATE_OFFSET_FILE} berisi nilai tidak valid. Mengatur offset ke 0.")
                return 0
    logging.info(f"File {LAST_UPDATE_OFFSET_FILE} tidak ditemukan. Mengatur offset ke 0.")
    return 0

def save_last_update_offset(offset):
    """Menyimpan offset update terakhir ke file teks."""
    with open(LAST_UPDATE_OFFSET_FILE, 'w') as f:
        f.write(str(offset))
    logging.info(f"Offset terakhir disimpan ke: {os.path.abspath(LAST_UPDATE_OFFSET_FILE)} -> {offset}")

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

    posted_media = load_json_file(POSTED_MEDIA_FILE) # Dictionary
    pending_media_queue = load_json_file(PENDING_MEDIA_FILE) # List
    last_offset = load_last_update_offset()

    try:
        # 1. Ambil media baru dari Telegram dan tambahkan ke antrean
        logging.info(f"Mengambil media terbaru dari Telegram (offset: {last_offset})...")
        new_updates_from_telegram, new_max_offset_seen = telegram_fetcher.fetch_new_media(
            TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, last_offset, posted_media
        )

        if new_updates_from_telegram:
            logging.info(f"Ditemukan {len(new_updates_from_telegram)} update baru dari Telegram.")
            # Tambahkan media baru ke antrean jika belum ada di posted_media atau pending_media
            pending_unique_ids = {item['file_unique_id'] for item in pending_media_queue}
            for media_info in new_updates_from_telegram:
                file_unique_id = media_info['file_unique_id']
                if file_unique_id not in posted_media and file_unique_id not in pending_unique_ids:
                    pending_media_queue.append(media_info)
                    pending_unique_ids.add(file_unique_id) # Tambahkan ke set lokal untuk cek cepat
                    logging.info(f"Menambahkan media {file_unique_id} ke antrean.")
                else:
                    logging.info(f"Media {file_unique_id} sudah ada di posted_media atau antrean. Melewatkan.")
            save_json_file(PENDING_MEDIA_FILE, pending_media_queue)
        else:
            logging.info("Tidak ada update baru dari Telegram untuk ditambahkan ke antrean.")

        # Selalu update offset terakhir ke update_id tertinggi yang pernah dilihat dari Telegram
        # Ini mencegah pengambilan ulang update lama dari Telegram API
        save_last_update_offset(new_max_offset_seen)

        # 2. Proses media dari antrean (terbaru ke terlama)
        if not pending_media_queue:
            logging.info("Antrean media kosong. Tidak ada yang perlu diposting.")
            send_telegram_notification("ℹ️ Antrean media kosong. Tidak ada yang perlu diposting.")
            send_telegram_notification("✅ Siklus AutoPost Facebook Reels selesai.")
            return

        # Urutkan antrean dari yang terbaru ke terlama (v5, v4, v3...)
        pending_media_queue.sort(key=lambda x: x['update_id'], reverse=True)
        
        media_to_process_this_run = pending_media_queue[:MAX_POSTS_PER_RUN]
        logging.info(f"Memproses {len(media_to_process_this_run)} media dari antrean (total {len(pending_media_queue)} di antrean).")
        send_telegram_notification(f"⏳ Akan memproses {len(media_to_process_this_run)} media dari antrean.")

        processed_ids_this_run = [] # Untuk melacak media yang berhasil/gagal diproses di run ini

        for media_info in media_to_process_this_run:
            file_unique_id = media_info['file_unique_id']
            media_path = media_info['file_path']
            original_caption = media_info.get('caption', '')
            media_type = media_info['type'] # 'video' atau 'photo'

            logging.info(f"Memproses media: {media_path} (ID Unik: {file_unique_id}) dari antrean.")

            post_status = 'failed_upload' # Default status jika terjadi kesalahan
            post_id = None
            processed_caption = ""

            try:
                # Unduh file lagi karena file lokal mungkin sudah dihapus
                # (Ini penting jika bot crash atau file dihapus sebelum diproses dari antrean)
                if not os.path.exists(media_path):
                    logging.info(f"File lokal {media_path} tidak ditemukan, mencoba mengunduh ulang.")
                    redownloaded_path = telegram_fetcher.download_telegram_file(
                        TELEGRAM_BOT_TOKEN, media_info['file_id'], file_unique_id, media_type
                    )
                    if redownloaded_path:
                        media_path = redownloaded_path
                    else:
                        raise Exception(f"Gagal mengunduh ulang media {file_unique_id}.")

                # 3. Cek Caption (Kosong / Spam / Siap Posting)
                logging.info("Memproses caption...")
                processed_caption = gemini_processor.process_caption(original_caption, GEMINI_API_KEY)
                logging.info(f"Caption akhir: {processed_caption}")

                # 4. Deteksi Reels / Biasa / Foto
                is_reel = False
                if media_type == 'video':
                    logging.info("Menganalisis video untuk deteksi Reels...")
                    is_reel = video_utils.is_reel(media_path)
                    if is_reel:
                        logging.info("Video dideteksi sebagai Reels.")
                    else:
                        logging.info("Video dideteksi sebagai Video Reguler.")
                else:
                    logging.info("Media dideteksi sebagai Foto.")

                # 5. Upload ke Facebook
                logging.info(f"Mengunggah media ke Facebook sebagai {'Reels' if is_reel else media_type.capitalize()}...")
                
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
                    post_status = 'posted'
                else:
                    logging.error("Gagal mendapatkan Post ID setelah unggah.")
                    send_telegram_notification(
                        f"❌ Gagal posting ke Facebook untuk media ID unik: {file_unique_id}. Post ID tidak ditemukan."
                    )
                    post_status = 'failed_upload'

            except Exception as e:
                logging.error(f"Terjadi kesalahan saat mengunggah media {file_unique_id}: {e}", exc_info=True)
                send_telegram_notification(
                    f"❌ Terjadi kesalahan saat posting ke Facebook untuk media ID unik: {file_unique_id}.\n"
                    f"Kesalahan: {str(e)[:200]}..."
                )
                post_status = 'failed_upload'
            finally:
                # Tambahkan ke posted_media (terlepas dari sukses/gagal)
                posted_media[file_unique_id] = {
                    'caption': processed_caption,
                    'post_id': post_id,
                    'posted_at': datetime.now().isoformat(),
                    'media_type': media_type,
                    'is_reel': is_reel if media_type == 'video' else False,
                    'status': post_status
                }
                save_json_file(POSTED_MEDIA_FILE, posted_media)
                
                # Tandai ID sebagai diproses di run ini agar bisa dihapus dari antrean
                processed_ids_this_run.append(file_unique_id)

                # 6. Cleanup: Hapus file lokal setelah selesai
                if os.path.exists(media_path):
                    os.remove(media_path)
                    logging.info(f"File lokal dihapus: {media_path}")

        # Hapus media yang berhasil/gagal diproses dari antrean
        pending_media_queue = [item for item in pending_media_queue if item['file_unique_id'] not in processed_ids_this_run]
        save_json_file(PENDING_MEDIA_FILE, pending_media_queue)

        logging.info(f"Siklus AutoPost selesai. Offset update terakhir disimpan: {new_max_offset_seen}")
        send_telegram_notification("✅ Siklus AutoPost Facebook Reels selesai.")

    except Exception as e:
        logging.error(f"Terjadi kesalahan fatal dalam siklus AutoPost: {e}", exc_info=True)
        send_telegram_notification(
            f"❌ Terjadi kesalahan fatal dalam siklus AutoPost Facebook Reels: {str(e)[:200]}..."
        )

if __name__ == "__main__":
    run_autopost()
