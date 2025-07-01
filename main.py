# main.py
import os
import time
import json # Untuk posted.json, meskipun di alur ini mungkin kita tidak cek duplikasi karena inputnya manual
             # Tapi tetap bagus untuk jaga-jaga jika ada ide filter di masa depan
import logging # Tambahkan logging untuk debug

from telegram_fetcher import get_latest_video_from_bot_chat
from video_utils import validate_video
from reels_uploader import upload_reel
from telegram_notify import send_telegram # Notifikasi ke Telegram

# Konfigurasi
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # Chat ID dari percakapan bot Anda dengan Anda
VIDEO_FOLDER = "videos"
# POSTED_HISTORY_FILE = "posted.json" # Di alur ini, kita asumsikan tidak ada duplikasi karena input manual

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)

    send_telegram("🚀 Memulai proses autopost Reels. Mencari video terbaru dari Telegram...")
    logger.info("Starting autopost process.")

    video_file_id = None
    video_caption = "Video dari Telegram Bot" # Default caption jika tidak ada
    downloaded_video_path = None

    try:
        # 1. Ambil video terbaru dari bot chat
        # get_latest_video_from_bot_chat akan mengembalikan path file dan info video Telegram
        logger.info("Fetching latest video from Telegram chat.")
        downloaded_video_path, video_info = get_latest_video_from_bot_chat(BOT_TOKEN, CHAT_ID, VIDEO_FOLDER)

        if not downloaded_video_path or not video_info:
            send_telegram("❌ Tidak ada video baru yang ditemukan atau gagal mengambil video. Mungkin Anda belum kirim video terbaru, atau sudah diproses.")
            logger.warning("No new video found or failed to fetch video.")
            return # Keluar jika tidak ada video baru

        video_title_from_telegram = video_info.get('caption', video_caption)
        telegram_file_id = video_info.get('file_id') # Untuk referensi atau untuk mencatat sudah diproses

        logger.info(f"Video ditemukan: {video_title_from_telegram}, File ID: {telegram_file_id}")
        send_telegram(f"📥 Video ditemukan: '{video_title_from_telegram}'. Sedang divalidasi...")

        # 2. Validasi video (durasi dan rasio)
        logger.info(f"Validating video: {downloaded_video_path}")
        if not validate_video(downloaded_video_path):
            send_telegram(f"⚠️ Video tidak valid (durasi > 60s atau rasio bukan 9:16): '{video_title_from_telegram}'. Melewati.")
            logger.warning(f"Video validation failed for: {downloaded_video_path}")
            os.remove(downloaded_video_path) # Hapus video tidak valid
            return

        # 3. Upload ke Facebook Reels
        logger.info(f"Uploading video: {video_title_from_telegram} to Facebook Reels.")
        description = f"{video_title_from_telegram} #shorts #reels #viral #foryou" # Sesuaikan deskripsi
        success, reel_id = upload_reel(downloaded_video_path, description)

        if success:
            send_telegram(f"✅ Reels berhasil diposting ke Facebook!\nJudul: {video_title_from_telegram}\nReel ID: {reel_id}")
            logger.info(f"Reels posted successfully: {video_title_from_telegram}, Reel ID: {reel_id}")
            # Opsional: Jika ingin mencegah duplikasi dari video yang sama, Anda bisa menyimpan telegram_file_id di posted.json
            # add_posted_video(telegram_file_id)
        else:
            send_telegram(f"❌ Gagal upload Reels ke Facebook: '{video_title_from_telegram}'. Coba periksa log.")
            logger.error(f"Failed to upload Reels: {video_title_from_telegram}")
        
        # Hapus video lokal setelah selesai diproses (berhasil atau gagal upload)
        if os.path.exists(downloaded_video_path):
            os.remove(downloaded_video_path)
            logger.info(f"Cleaned up local video file: {downloaded_video_path}")

    except Exception as e:
        error_message = f"🚨 Terjadi kesalahan fatal dalam proses utama: {e}"
        send_telegram(error_message)
        logger.critical(error_message, exc_info=True) # Log exception traceback
        if downloaded_video_path and os.path.exists(downloaded_video_path):
            os.remove(downloaded_video_path)
            logger.info(f"Cleaned up local video file after error: {downloaded_video_path}")

if __name__ == "__main__":
    main()
