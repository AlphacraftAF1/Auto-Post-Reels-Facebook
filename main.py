# main.py
import os
import logging
import time
import asyncio
import random

from telegram_fetcher import get_latest_media_from_bot_chat
from video_utils import validate_video
from facebook_uploader import upload_reel, upload_regular_video, upload_photo
from telegram_notify import send_telegram
from gemini_processor import process_caption_with_gemini
from media_history import add_posted_media, is_media_posted

# Konfigurasi
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
VIDEO_FOLDER = "videos" # Folder untuk menyimpan media yang diunduh sementara

MAX_VIDEO_SIZE_MB = 20 # Batas ukuran video dalam MB (misalnya 20MB)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- DAFTAR CAPTION EMOTE + HASHTAG UNTUK FALLBACK ---
GENERIC_EMOJI_HASHTAG_CAPTIONS = [
    "😂 #lucu #ngakak #viral",
    "✨ #momenindah #inspirasi #foryou",
    "😄 #hiburan #senyum #kocak",
    "📸 #fotokeren #memories #daily #fyp",
    "🎥 #videolucu #seru #reels #explore"
]
# --- AKHIR DAFTAR CAPTION EMOTE + HASHTAG ---

# --- DAFTAR CAPTION BAWAAN TELEGRAM YANG HARUS DIANGGAP KOSONG UNTUK AI ---
GENERIC_TELEGRAM_DEFAULTS = [
    "Photo",
    "Video",
    "Photo dari Telegram",
    "Video dari Telegram",
    # Anda bisa menambahkan lebih banyak jika menemukan pola default lain dari Telegram
]
# --- AKHIR DAFTAR CAPTION BAWAAN TELEGRAM ---

async def main_async():
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)

    send_telegram("🚀 Memulai proses autopost. Mencari media terbaru dari Telegram...")
    logger.info("Starting autopost process.")

    downloaded_media_path = None
    media_info = None

    try:
        logger.info("Fetching latest media (video/photo) from Telegram chat.")
        downloaded_media_path, media_info = get_latest_media_from_bot_chat(BOT_TOKEN, CHAT_ID, VIDEO_FOLDER)

        if not downloaded_media_path or not media_info:
            send_telegram("❌ Tidak ada media baru yang ditemukan atau gagal mengambil media. Mungkin Anda belum kirim media terbaru, atau sudah diproses.")
            logger.warning("No new media found or failed to fetch media.")
            return

        media_type = media_info.get('type')
        raw_caption = media_info.get('caption', None)
        
        # Dapatkan ID unik media dari Telegram untuk pengecekan duplikasi
        media_unique_id = media_info.get('file_unique_id')

        # --- Tambahan: Cek Duplikasi di sini ---
        if is_media_posted(media_unique_id):
            send_telegram(f"🔁 Media sudah pernah diposting (ID: {media_unique_id}). Melewati.")
            logger.info(f"Media with ID '{media_unique_id}' already posted. Skipping.")
            if os.path.exists(downloaded_media_path):
                os.remove(downloaded_media_path)
            return
        # --- Akhir Tambahan ---
            
        # --- BARU: Validasi Ukuran File Video/Foto ---
        file_size_bytes = os.path.getsize(downloaded_media_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        logger.info(f"Ukuran file media: {file_size_mb:.2f} MB")

        if file_size_mb > MAX_VIDEO_SIZE_MB:
            send_telegram(f"⚠️ Ukuran media ({file_size_mb:.2f} MB) melebihi batas {MAX_VIDEO_SIZE_MB} MB. Melewati.")
            logger.warning(f"Media size {file_size_mb:.2f} MB exceeds max limit {MAX_VIDEO_SIZE_MB} MB. Skipping.")
            if os.path.exists(downloaded_media_path):
                os.remove(downloaded_media_path)
            return
        # --- AKHIR Validasi Ukuran File ---
        
        processed_caption = ""
        if not raw_caption or \
           raw_caption.strip() == "" or \
           raw_caption.strip().lower() in [g.lower() for g in GENERIC_TELEGRAM_DEFAULTS]:
            
            logger.info(f"Raw caption is empty or generic Telegram default ('{raw_caption}'). Generating generic emoji+hashtag caption.")
            processed_caption = random.choice(GENERIC_EMOJI_HASHTAG_CAPTIONS)
        else:
            logger.info(f"Raw caption detected: '{raw_caption}'. Calling Gemini to process it.")
            processed_caption = process_caption_with_gemini(raw_caption, media_type=media_type)

        logger.info(f"Media ditemukan: Tipe={media_type}, Keterangan='{raw_caption}' (Final Processed: '{processed_caption}')")
        send_telegram(f"📥 Media ditemukan: '{raw_caption}'. Tipe: {media_type}. Menggunakan caption: '{processed_caption}'.")

        # --- Logika Penentuan Tipe Upload ---
        upload_success = False
        post_id = None
        
        final_description = processed_caption

        if media_type == 'video':
            logger.info(f"Processing video: {downloaded_media_path}")
            if validate_video(downloaded_media_path):
                send_telegram("🎥 Video cocok untuk Reels. Mencoba mengupload sebagai Reels...")
                upload_success, post_id = upload_reel(downloaded_media_path, final_description)
                post_type = "Reels"
            else:
                send_telegram("🎞️ Video tidak cocok untuk Reels (durasi/rasio). Mencoba mengupload sebagai video biasa...")
                upload_success, post_id = upload_regular_video(downloaded_media_path, final_description)
                post_type = "Video Reguler"
        
        elif media_type == 'photo':
            send_telegram("📸 Media adalah foto. Mencoba mengupload sebagai foto...")
            upload_success, post_id = upload_photo(downloaded_media_path, final_description)
            post_type = "Foto"
        
        else:
            send_telegram(f"⚠️ Tipe media tidak didukung: {media_type}. Melewati.")
            logger.warning(f"Unsupported media type: {media_type}")
            if os.path.exists(downloaded_media_path):
                os.remove(downloaded_media_path)
            return

        # --- Notifikasi Hasil Upload ---
        if upload_success:
            send_telegram(f"✅ {post_type} berhasil diposting ke Facebook!\nJudul: {processed_caption}\nPost ID: {post_id}")
            logger.info(f"{post_type} posted successfully: {processed_caption}, Post ID: {post_id}")
            add_posted_media(media_unique_id) # Tambahkan ID unik ke riwayat setelah berhasil
        else:
            send_telegram(f"❌ Gagal upload {post_type} ke Facebook: '{processed_caption}'. Coba periksa log.")
            logger.error(f"Failed to upload {post_type}: {processed_caption}")
        
        # Hapus media lokal setelah selesai diproses
        if os.path.exists(downloaded_media_path):
            os.remove(downloaded_media_path)
            logger.info(f"Cleaned up local media file: {downloaded_media_path}")

    except Exception as e:
        error_message = f"🚨 Terjadi kesalahan fatal dalam proses utama: {e}"
        send_telegram(error_message)
        logger.critical(error_message, exc_info=True)
        if downloaded_media_path and os.path.exists(downloaded_media_path):
            os.remove(downloaded_media_path)
            logger.info(f"Cleaned up local media file after error: {downloaded_media_path}")

if __name__ == "__main__":
    asyncio.run(main_async())
