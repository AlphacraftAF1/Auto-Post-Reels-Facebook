# main.py
import os
import logging
import time

import asyncio # Masih dibutuhkan untuk asyncio.run() di akhir

from telegram_fetcher import get_latest_media_from_bot_chat
from video_utils import validate_video, get_video_duration
from facebook_uploader import upload_reel, upload_regular_video, upload_photo
from telegram_notify import send_telegram
from gemini_processor import process_caption_with_gemini # Import tetap sama


# Konfigurasi
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
VIDEO_FOLDER = "videos"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main_async(): # Tetap async def karena asyncio.run() di akhir
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)

    send_telegram("🚀 Memulai proses autopost. Mencari media terbaru dari Telegram...")
    logger.info("Starting autopost process.")

    downloaded_media_path = None
    media_info = None

    try:
        # 1. Ambil media terbaru dari bot chat (bisa video atau foto)
        logger.info("Fetching latest media (video/photo) from Telegram chat.")
        # Mengganti get_latest_video_from_bot_chat menjadi get_latest_media_from_bot_chat
        downloaded_media_path, media_info = get_latest_media_from_bot_chat(BOT_TOKEN, CHAT_ID, VIDEO_FOLDER)

        if not downloaded_media_path or not media_info:
            send_telegram("❌ Tidak ada media baru yang ditemukan atau gagal mengambil media. Mungkin Anda belum kirim media terbaru, atau sudah diproses.")
            logger.warning("No new media found or failed to fetch media.")
            return

        media_type = media_info.get('type')
        raw_caption = media_info.get('caption', None) # Ambil caption asli, bisa None
        
        # Panggil Gemini untuk memproses/menghasilkan caption
        logger.info("Calling Gemini to process/generate caption...")
        # --- PERUBAHAN DI SINI: Hapus 'await' ---
        processed_caption = process_caption_with_gemini(raw_caption, media_type=media_type)
        # --- AKHIR PERUBAHAN ---
        
        logger.info(f"Media ditemukan: Tipe={media_type}, Keterangan='{raw_caption}' (Gemini Processed: '{processed_caption}')")
        send_telegram(f"📥 Media ditemukan: '{raw_caption}'. Tipe: {media_type}. Sedang diproses dengan Gemini...")

        # --- Logika Penentuan Tipe Upload ---
        upload_success = False
        post_id = None
        
        final_description = processed_caption 

        if media_type == 'video':
            logger.info(f"Processing video: {downloaded_media_path}")
            if validate_video(downloaded_media_path): # Cek validasi untuk Reels
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

# Panggil fungsi async main_async()
if __name__ == "__main__":
    asyncio.run(main_async())
