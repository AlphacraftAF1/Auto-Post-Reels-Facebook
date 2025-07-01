# main.py
import os
import logging
import time

from telegram_fetcher import get_latest_media_from_bot_chat # Nama fungsi diubah
from video_utils import validate_video, get_video_duration # Tambah get_video_duration
from facebook_uploader import upload_reel, upload_regular_video, upload_photo # Impor semua uploader
from telegram_notify import send_telegram # Notifikasi ke Telegram

# Konfigurasi
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # Chat ID dari percakapan bot Anda dengan Anda
VIDEO_FOLDER = "videos"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)

    send_telegram("🚀 Memulai proses autopost. Mencari media terbaru dari Telegram...")
    logger.info("Starting autopost process.")

    downloaded_media_path = None
    media_info = None

    try:
        # 1. Ambil media terbaru dari bot chat (bisa video atau foto)
        logger.info("Fetching latest media (video/photo) from Telegram chat.")
        downloaded_media_path, media_info = get_latest_media_from_bot_chat(BOT_TOKEN, CHAT_ID, VIDEO_FOLDER)

        if not downloaded_media_path or not media_info:
            send_telegram("❌ Tidak ada media baru yang ditemukan atau gagal mengambil media. Mungkin Anda belum kirim media terbaru, atau sudah diproses.")
            logger.warning("No new media found or failed to fetch media.")
            return # Keluar jika tidak ada media baru

        media_type = media_info.get('type')
        media_caption = media_info.get('caption', f"{media_type.capitalize()} dari Telegram Bot")
        
        logger.info(f"Media ditemukan: Tipe={media_type}, Keterangan='{media_caption}'")
        send_telegram(f"📥 Media ditemukan: '{media_caption}'. Tipe: {media_type}. Sedang diproses...")

        # --- Logika Penentuan Tipe Upload ---
        upload_success = False
        post_id = None

        if media_type == 'video':
            # Untuk video, kita tentukan apakah ini Reels atau video biasa
            logger.info(f"Processing video: {downloaded_media_path}")
            if validate_video(downloaded_media_path): # Cek validasi untuk Reels
                # Video cocok untuk Reels (durasi < 60s & rasio 9:16)
                send_telegram("🎥 Video cocok untuk Reels. Mencoba mengupload sebagai Reels...")
                upload_success, post_id = upload_reel(downloaded_media_path, media_caption)
                post_type = "Reels"
            else:
                # Video tidak cocok untuk Reels, upload sebagai video biasa
                send_telegram("🎞️ Video tidak cocok untuk Reels (durasi/rasio). Mencoba mengupload sebagai video biasa...")
                upload_success, post_id = upload_regular_video(downloaded_media_path, media_caption)
                post_type = "Video Reguler"
        
        elif media_type == 'photo':
            # Untuk foto
            send_telegram("📸 Media adalah foto. Mencoba mengupload sebagai foto...")
            upload_success, post_id = upload_photo(downloaded_media_path, media_caption)
            post_type = "Foto"
        
        else:
            send_telegram(f"⚠️ Tipe media tidak didukung: {media_type}. Melewati.")
            logger.warning(f"Unsupported media type: {media_type}")
            if os.path.exists(downloaded_media_path):
                os.remove(downloaded_media_path)
            return

        # --- Notifikasi Hasil Upload ---
        if upload_success:
            send_telegram(f"✅ {post_type} berhasil diposting ke Facebook!\nJudul: {media_caption}\nPost ID: {post_id}")
            logger.info(f"{post_type} posted successfully: {media_caption}, Post ID: {post_id}")
        else:
            send_telegram(f"❌ Gagal upload {post_type} ke Facebook: '{media_caption}'. Coba periksa log.")
            logger.error(f"Failed to upload {post_type}: {media_caption}")
        
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
    main()
