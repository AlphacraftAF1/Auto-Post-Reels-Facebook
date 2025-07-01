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

# --- Batasan Posting per Run ---
MAX_POSTS_PER_RUN = 1 # Ubah nilai ini sesuai keinginan Anda (misal: 1, 2, atau 3)

# --- Fungsi Pembantu ---
def load_posted_media():
    """Memuat daftar media yang sudah diposting dari file JSON."""
    if os.path.exists(POSTED_MEDIA_FILE):
        with open(POSTED_MEDIA_FILE, 'r') as f:
            try:
                logging.info(f"Memuat media yang sudah diposting dari: {os.path.abspath(POSTED_MEDIA_FILE)}")
                return json.load(f)
            except json.JSONDecodeError:
                logging.warning(f"File {POSTED_MEDIA_FILE} rusak atau kosong. Membuat yang baru.")
                return {}
    logging.info(f"File {POSTED_MEDIA_FILE} tidak ditemukan. Membuat yang baru.")
    return {}

def save_posted_media(posted_media_data):
    """Menyimpan daftar media yang sudah diposting ke file JSON."""
    with open(POSTED_MEDIA_FILE, 'w') as f:
        json.dump(posted_media_data, f, indent=4)
    logging.info(f"Media yang sudah diposting disimpan ke: {os.path.abspath(POSTED_MEDIA_FILE)}")

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

        logging.info(f"Ditemukan {len(new_media_updates)} media baru yang potensial untuk diproses.")
        
        # --- OPSI PENGURUTAN MEDIA ---
        # Pilih salah satu dari dua opsi di bawah, atau hapus keduanya jika Anda ingin
        # memproses media sesuai urutan yang dikembalikan oleh Telegram_fetcher (terbaru ke terlama).

        # OPSI 1: Prioritaskan Foto, lalu Reels, lalu Video Reguler (seperti sebelumnya)
        # Ini akan mengurutkan ulang media yang baru ditemukan berdasarkan jenisnya.
        # Jika MAX_POSTS_PER_RUN = 1, ini akan memproses foto terbaru terlebih dahulu.
        new_media_updates.sort(key=lambda x: (
            0 if x['type'] == 'photo' else # Foto memiliki prioritas tertinggi (0)
            1 if x['type'] == 'video' and video_utils.is_reel(x['file_path']) else # Reels (video) prioritas kedua (1)
            2 # Video reguler prioritas terendah (2)
        ))

        # OPSI 2 (Alternatif): Jika Anda ingin memproses media yang *paling baru* dari Telegram
        # secara mutlak (berdasarkan update_id), tanpa memandang jenisnya, dan MAX_POSTS_PER_RUN = 1,
        # maka HAPUS blok OPSI 1 di atas. Telegram_fetcher sudah mengembalikan media terbaru duluan.
        # new_media_updates = new_media_updates # Tidak perlu pengurutan tambahan jika telegram_fetcher sudah mengurutkan DESC

        # Batasi jumlah media yang akan diproses per run
        media_to_process = new_media_updates[:MAX_POSTS_PER_RUN]
        logging.info(f"Memproses {len(media_to_process)} media dari total {len(new_media_updates)} media baru yang tersedia.")
        send_telegram_notification(f"⏳ Akan memproses {len(media_to_process)} media baru.")

        for media_info in media_to_process:
            file_unique_id = media_info['file_unique_id']
            media_path = media_info['file_path']
            original_caption = media_info.get('caption', '')
            media_type = media_info['type'] # 'video' atau 'photo'

            logging.info(f"Memproses media: {media_path} (ID Unik: {file_unique_id})")

            post_status = 'failed_upload' # Default status jika terjadi kesalahan
            post_id = None
            processed_caption = ""

            try:
                # 3. Cek Caption (Kosong / Spam / Siap Posting)
                logging.info("Memproses caption...")
                processed_caption = gemini_processor.process_caption(original_caption, GEMINI_API_KEY)
                logging.info(f"Caption akhir: {processed_caption}")

                # 4. Deteksi Reels / Biasa / Foto
                is_reel = False
                if media_type == 'video':
                    logging.info("Menganalisis video untuk deteksi Reels...")
                    # Panggil is_reel lagi karena pengurutan di atas hanya untuk menentukan prioritas,
                    # dan is_reel mungkin perlu membaca file lagi untuk memastikan.
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
                    post_status = 'failed_upload' # Pastikan status diatur jika post_id None

            except Exception as e:
                logging.error(f"Terjadi kesalahan saat mengunggah media {file_unique_id}: {e}", exc_info=True)
                send_telegram_notification(
                    f"❌ Terjadi kesalahan saat posting ke Facebook untuk media ID unik: {file_unique_id}.\n"
                    f"Kesalahan: {str(e)[:200]}..."
                )
                post_status = 'failed_upload' # Pastikan status diatur jika ada exception
            finally:
                # Simpan ke posted_media.json setelah setiap upaya pemrosesan (berhasil atau gagal)
                posted_media[file_unique_id] = {
                    'caption': processed_caption,
                    'post_id': post_id,
                    'posted_at': datetime.now().isoformat(),
                    'media_type': media_type,
                    'is_reel': is_reel if media_type == 'video' else False, # Hanya relevan untuk video
                    'status': post_status # Tambahkan status
                }
                save_posted_media(posted_media) # Simpan setelah setiap media diproses

                # 6. Cleanup: Hapus file lokal setelah selesai
                if os.path.exists(media_path):
                    os.remove(media_path)
                    logging.info(f"File lokal dihapus: {media_path}")

        # Simpan offset update_id terakhir
        # Offset terakhir harus selalu yang paling tinggi dari semua update yang ditemukan,
        # bahkan jika tidak semua diproses, agar tidak mengulang update yang sama di run berikutnya.
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
