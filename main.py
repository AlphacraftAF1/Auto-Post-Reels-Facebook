import os
import logging
import time
import asyncio
import random
import json

from telegram_fetcher import get_latest_media_from_bot_chat
from video_utils import validate_video
from facebook_uploader import upload_reel, upload_regular_video, upload_photo
from telegram_notify import send_telegram
from gemini_processor import process_caption_with_gemini

# Konfigurasi
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
VIDEO_FOLDER = "videos"
POSTED_MEDIA_FILE = "posted_media.json"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fallback caption
GENERIC_CAPTIONS = [
    "😂 #lucu #ngakak #viral",
    "✨ #momenindah #inspirasi #foryou",
    "😄 #hiburan #senyum #kocak",
    "📸 #fotokeren #memories #daily #fyp",
    "🎥 #videolucu #seru #reels #explore"
]

GENERIC_TELEGRAM_DEFAULTS = [
    "Photo", "Video", "Photo dari Telegram", "Video dari Telegram"
]

def load_posted_ids():
    if os.path.exists(POSTED_MEDIA_FILE):
        with open(POSTED_MEDIA_FILE) as f:
            return json.load(f)
    return {}

def save_posted_ids(posted_dict):
    with open(POSTED_MEDIA_FILE, "w") as f:
        json.dump(posted_dict, f)

async def main_async():
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)

    posted_ids = load_posted_ids()

    send_telegram("🚀 Memulai proses autopost. Mencari media terbaru dari Telegram...")
    logger.info("Starting autopost process.")

    downloaded_media_path, media_info = get_latest_media_from_bot_chat(BOT_TOKEN, CHAT_ID, VIDEO_FOLDER)

    if not downloaded_media_path or not media_info:
        send_telegram("❌ Tidak ada media baru yang ditemukan atau gagal mengambil media.")
        return

    media_type = media_info.get('type')
    raw_caption = media_info.get('caption', None)
    unique_id = media_info.get('file_unique_id')

    if unique_id in posted_ids:
        logger.warning(f"Media sudah pernah diposting. ID: {unique_id}")
        send_telegram("⚠️ Media ini sudah pernah diposting. Melewati...")
        if os.path.exists(downloaded_media_path):
            os.remove(downloaded_media_path)
        return

    # Caption logic
    if not raw_caption or raw_caption.strip().lower() in [g.lower() for g in GENERIC_TELEGRAM_DEFAULTS]:
        processed_caption = random.choice(GENERIC_CAPTIONS)
    else:
        processed_caption = process_caption_with_gemini(raw_caption, media_type=media_type)

    logger.info(f"Media ditemukan: Tipe={media_type}, Caption='{processed_caption}'")
    send_telegram(f"📥 Media ditemukan. Caption: '{processed_caption}'")

    # Upload logic
    upload_success = False
    post_id = None

    try:
        if media_type == 'video':
            logger.info(f"Validating video: {downloaded_media_path}")
            if validate_video(downloaded_media_path):
                send_telegram("🎥 Upload sebagai Reels...")
                upload_success, post_id = upload_reel(downloaded_media_path, processed_caption)
                post_type = "Reels"
            else:
                send_telegram("🎞️ Upload sebagai video reguler...")
                upload_success, post_id = upload_regular_video(downloaded_media_path, processed_caption)
                post_type = "Video Reguler"

        elif media_type == 'photo':
            send_telegram("📸 Upload sebagai foto...")
            upload_success, post_id = upload_photo(downloaded_media_path, processed_caption)
            post_type = "Foto"

        else:
            send_telegram(f"⚠️ Tipe media tidak didukung: {media_type}. Melewati...")
            return

        if upload_success:
            posted_ids[unique_id] = True
            save_posted_ids(posted_ids)
            send_telegram(f"✅ {post_type} berhasil diposting!
Judul: {processed_caption}
Post ID: {post_id}")
        else:
            send_telegram(f"❌ Gagal upload {post_type}. Cek log.")

    finally:
        if os.path.exists(downloaded_media_path):
            os.remove(downloaded_media_path)
            logger.info(f"🧹 File dibersihkan: {downloaded_media_path}")

if __name__ == "__main__":
    asyncio.run(main_async())
