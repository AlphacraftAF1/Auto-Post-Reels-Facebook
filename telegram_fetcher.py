# telegram_fetcher.py
import requests
import os
import json
import time
import logging

logger = logging.getLogger(__name__)

# File untuk menyimpan 'offset' agar tidak memproses update yang sama berulang kali
LAST_UPDATE_OFFSET_FILE = "last_update_offset.txt"

def save_last_update_offset(offset):
    """Menyimpan offset update terakhir."""
    try:
        with open(LAST_UPDATE_OFFSET_FILE, "w") as f:
            f.write(str(offset))
        logger.info(f"Saved last update offset: {offset}")
    except Exception as e:
        logger.error(f"Failed to save last update offset: {e}")

def get_last_update_offset():
    """Mengambil offset update terakhir yang tersimpan."""
    if os.path.exists(LAST_UPDATE_OFFSET_FILE):
        try:
            with open(LAST_UPDATE_OFFSET_FILE, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError) as e:
            logger.warning(f"Could not read last update offset, starting fresh. Error: {e}")
            return 0
    return 0

def get_latest_video_from_bot_chat(bot_token, chat_id, output_folder):
    """
    Mengambil video terbaru yang dikirim ke bot dari chat_id tertentu.
    Hanya memproses update baru berdasarkan offset.
    Mengembalikan path file video dan dictionary info video Telegram.
    """
    if not bot_token or not chat_id:
        logger.error("BOT_TOKEN or CHAT_ID not set for Telegram fetcher.")
        return None, None

    base_url = f"https://api.telegram.org/bot{bot_token}/"
    offset = get_last_update_offset() + 1 # Mulai dari update setelah yang terakhir diproses

    try:
        # Coba ambil update terbaru dengan offset
        get_updates_url = f"{base_url}getUpdates"
        params = {
            'offset': offset,
            'limit': 1, # Ambil hanya 1 update terbaru
            'timeout': 10 # Timeout untuk request
        }
        logger.info(f"Fetching updates from Telegram with offset: {offset}")
        response = requests.get(get_updates_url, params=params)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        updates = response.json().get('result', [])

        if not updates:
            logger.info("No new updates found from Telegram.")
            return None, None

        # Kita ambil update terakhir yang valid (mungkin ada update yang bukan video)
        latest_video_update = None
        for update in sorted(updates, key=lambda x: x['update_id'], reverse=True):
            if 'message' in update and 'video' in update['message']:
                # Pastikan video datang dari CHAT_ID yang benar
                if str(update['message']['chat']['id']) == str(chat_id):
                    latest_video_update = update['message']
                    # Simpan offset dari update yang baru diproses
                    save_last_update_offset(update['update_id'])
                    break # Ambil video pertama yang cocok dan keluar

        if not latest_video_update:
            logger.info(f"No new video message found from CHAT_ID '{chat_id}' in latest updates.")
            # Tetap simpan offset update_id tertinggi yang kita lihat, agar tidak memproses lagi
            if updates:
                save_last_update_offset(max(u['update_id'] for u in updates))
            return None, None

        video_file_id = latest_video_update['video']['file_id']
        video_unique_id = latest_video_update['video']['file_unique_id']
        file_name_suffix = video_unique_id # Menggunakan unique ID sebagai nama unik

        # Dapatkan info file untuk URL download
        get_file_url = f"{base_url}getFile"
        file_response = requests.get(get_file_url, params={'file_id': video_file_id})
        file_response.raise_for_status()
        file_info = file_response.json().get('result', {})

        if not file_info or 'file_path' not in file_info:
            logger.error(f"Could not get file info for file_id: {video_file_id}")
            return None, None

        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_info['file_path']}"
        output_filepath = os.path.join(output_folder, f"{file_name_suffix}.mp4")

        # Download file video
        logger.info(f"Downloading video from Telegram: {download_url}")
        file_download_response = requests.get(download_url, stream=True)
        file_download_response.raise_for_status()

        with open(output_filepath, 'wb') as f:
            for chunk in file_download_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Video downloaded successfully to: {output_filepath}")
        
        # Gabungkan info video dari Telegram
        video_metadata = {
            'file_id': video_file_id,
            'file_unique_id': video_unique_id,
            'caption': latest_video_update.get('caption', 'Video dari Telegram'),
            'duration': latest_video_update['video'].get('duration'),
            'width': latest_video_update['video'].get('width'),
            'height': latest_video_update['video'].get('height'),
            'mime_type': latest_video_update['video'].get('mime_type')
        }
        return output_filepath, video_metadata

    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram API request failed: {e}", exc_info=True)
        return None, None
    except Exception as e:
        logger.error(f"Error in get_latest_video_from_bot_chat: {e}", exc_info=True)
        return None, None

# Helper function (if needed) to get info for a specific file_id
def get_video_info_from_telegram_file(bot_token, file_id):
    """Mendapatkan info detail file dari Telegram dengan file_id."""
    base_url = f"https://api.telegram.org/bot{bot_token}/"
    get_file_url = f"{base_url}getFile"
    try:
        response = requests.get(get_file_url, params={'file_id': file_id})
        response.raise_for_status()
        return response.json().get('result', {})
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get file info from Telegram: {e}")
        return {}

# Contoh penggunaan lokal (bisa dihapus nanti)
if __name__ == "__main__":
    # Ini hanya untuk pengujian lokal, perlu set ENV VARS
    # os.environ["TELEGRAM_BOT_TOKEN"] = "YOUR_BOT_TOKEN"
    # os.environ["TELEGRAM_CHAT_ID"] = "YOUR_CHAT_ID"
    # downloaded_path, info = get_latest_video_from_bot_chat(os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID"), "temp_videos")
    # if downloaded_path:
    #     print(f"Downloaded: {downloaded_path}")
    #     print(f"Info: {json.dumps(info, indent=2)}")
    # else:
    #     print("No video downloaded.")
    pass
