import os
import logging
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

# Caption fallback
GENERIC_EMOJI_HASHTAG_CAPTIONS = [
    "😂 #lucu #ngakak #viral",
    "✨ #momenindah #inspirasi #foryou",
    "😄 #hiburan #senyum #kocak",
    "📸 #fotokeren #memories #daily #fyp",
    "🎥 #videolucu #seru #reels #explore"
]

GENERIC_TELEGRAM_DEFAULTS = [
    "Photo",
    "Video",
    "Photo dari Telegram",
    "Video dari Telegram",
]

def is_already_posted(file_unique_id):
    if os.path.exists(POSTED_MEDIA_FILE):
        with open(POSTED_MEDIA_FILE, 'r') as f:
            data = json.load(f)
            return file_unique_id in data
    return False

def mark_as_posted(file_unique_id, post_type, post_id, caption):
    if os.path.exists(POSTED_MEDIA_FILE):
        with open(POSTED_MEDIA_FILE, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    data[file_unique_id] = {
        "post_type": post_type,
        "post_id": post_id,
        "caption": caption
    }
    with open(POSTED_MEDIA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

async def main_async():
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)

    send_telegram("🚀 Memulai proses autopost. Mencari media terbaru dari Telegram...")
    logger.info("Starting autopost process.")

    downloaded_media_path, media_info = get_latest_media_from_bot_chat(BOT_TOKEN, CHAT_ID, VIDEO_FOLDER)
    if not downloaded_media_path or not media_info:
        send_telegram("❌ Tidak ada media baru yang ditemukan atau gagal mengambil media.")
        logger.warning("No new media found or failed to fetch media.")
        return

    file_unique_id = media_info.get("file_unique_id")
    if is_already_posted(file_unique_id):
        send_telegram("⏩ Media ini sudah pernah diposting sebelumnya. Melewati...")
        logger.info(f"Duplicate media detected (file_unique_id={file_unique_id}). Skipping upload.")
        if os.path.exists(downloaded_media_path):
            os.remove(downloaded_media_path)
        return

    media_type = media_info.get('type')
    raw_caption = media_info.get('caption', None)

    if not raw_caption or raw_caption.strip().lower() in [g.lower() for g in GENERIC_TELEGRAM_DEFAULTS]:
        logger.info(f"Raw caption is empty or generic ('{raw_caption}'). Generating fallback caption.")
        processed_caption = random.choice(GENERIC_EMOJI_HASHTAG_CAPTIONS)
    else:
        logger.info(f"Processing caption via Gemini: '{raw_caption}'")
        processed_caption = process_caption_with_gemini(raw_caption, media_type=media_type)

    logger.info(f"Final caption: {processed_caption}")
    send_telegram(f"📥 Media ditemukan. Caption: '{processed_caption}'.")

    upload_success = False
    post_id = None
    post_type = None

    if media_type == 'video':
        logger.info(f"Processing video: {downloaded_media_path}")
        if validate_video(downloaded_media_path):
            send_telegram("🎥 Video cocok untuk Reels. Mengupload sebagai Reels...")
            upload_success, post_id = upload_reel(downloaded_media_path, processed_caption)
            post_type = "Reels"
        else:
            send_telegram("🎞️ Video tidak cocok untuk Reels. Mengupload sebagai video biasa...")
            upload_success, post_id = upload_regular_video(downloaded_media_path, processed_caption)
            post_type = "Video Reguler"
    elif media_type == 'photo':
        send_telegram("📸 Media adalah foto. Mengupload sebagai foto...")
        upload_success, post_id = upload_photo(downloaded_media_path, processed_caption)
        post_type = "Foto"
    else:
        send_telegram(f"⚠️ Tipe media tidak didukung: {media_type}")
        logger.warning(f"Unsupported media type: {media_type}")
        if os.path.exists(downloaded_media_path):
            os.remove(downloaded_media_path)
        return

    if upload_success:
        send_telegram(f"✅ {post_type} berhasil diposting!\nCaption: {processed_caption}\nPost ID: {post_id}")
        mark_as_posted(file_unique_id, post_type, post_id, processed_caption)
        logger.info(f"{post_type} posted: {processed_caption} (Post ID: {post_id})")
    else:
        send_telegram(f"❌ Gagal upload {post_type}: '{processed_caption}'.")
        logger.error(f"Failed to upload {post_type}: {processed_caption}")

    if os.path.exists(downloaded_media_path):
        os.remove(downloaded_media_path)
        logger.info(f"Deleted local file: {downloaded_media_path}")

if __name__ == "__main__":
    asyncio.run(main_async())
