# telegram_fetcher.py
import requests
import os
import json
import time
import logging

logger = logging.getLogger(__name__)

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
    
    # Dapatkan offset terakhir
    current_offset = get_last_update_offset()
    
    # Kita akan mencoba mengambil lebih dari 1 update untuk mencari video terbaru
    # Ambil 10 update terakhir. Jika ada update yang sudah diproses, Telegram akan mengabaikannya
    # jika offset yang dikirim adalah update_id + 1.
    params = {
        'offset': current_offset + 1, # Ambil update setelah yang terakhir diproses
        'limit': 10, # Ambil beberapa update, bukan cuma 1
        'timeout': 20 # Timeout request lebih lama
    }

    try:
        get_updates_url = f"{base_url}getUpdates"
        logger.info(f"Fetching updates from Telegram with offset: {params['offset']} and limit: {params['limit']}")
        response = requests.get(get_updates_url, params=params)
        response.raise_for_status()
        updates = response.json().get('result', [])

        if not updates:
            logger.info("No new updates found from Telegram.")
            return None, None

        # Update offset tertinggi yang kita lihat, bahkan jika tidak ada video.
        # Ini penting agar kita tidak terus-menerus memproses update yang sama.
        max_update_id = current_offset
        if updates:
            max_update_id = max(u['update_id'] for u in updates)
            save_last_update_offset(max_update_id)


        # Cari video terbaru dari CHAT_ID yang benar
        latest_video_message = None
        # Urutkan update dari yang terbaru ke terlama berdasarkan update_id
        for update in sorted(updates, key=lambda x: x['update_id'], reverse=True):
            if 'message' in update:
                message = update['message']
                if str(message['chat']['id']) == str(chat_id) and 'video' in message:
                    latest_video_message = message
                    logger.info(f"Found a video message (Update ID: {update['update_id']}).")
                    # Kita sudah menyimpan offset dari max_update_id di atas
                    break # Ambil video pertama yang cocok dan keluar loop

        if not latest_video_message:
            logger.info(f"No new video message found from CHAT_ID '{chat_id}' in fetched updates.")
            return None, None

        video_file_id = latest_video_message['video']['file_id']
        video_unique_id = latest_video_message['video']['file_unique_id']
        
        # Cek apakah video ini sudah pernah kita proses berdasarkan file_unique_id
        # Ini membutuhkan file history. Untuk saat ini kita abaikan dulu, fokus download
        
        # Dapatkan info file untuk URL download
        get_file_url = f"{base_url}getFile"
        file_response = requests.get(get_file_url, params={'file_id': video_file_id})
        file_response.raise_for_status()
        file_info = file_response.json().get('result', {})

        if not file_info or 'file_path' not in file_info:
            logger.error(f"Could not get file info for file_id: {video_file_id}")
            return None, None

        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_info['file_path']}"
        output_filepath = os.path.join(output_folder, f"{video_unique_id}.mp4")

        # Pastikan kita tidak mendownload ulang file yang sudah ada
        if os.path.exists(output_filepath):
            logger.info(f"File {output_filepath} already exists. Assuming it was processed. Skipping download.")
            # Kita bisa memutuskan di sini apakah akan memproses ulang atau tidak.
            # Untuk skenario ini, kita anggap sudah diproses dan kembali None
            # Jika Anda ingin memproses ulang, hapus block if ini.
            return None, None

        # Download file video
        logger.info(f"Downloading video from Telegram URL: {download_url}")
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
            'caption': latest_video_message.get('caption', 'Video dari Telegram'),
            'duration': latest_video_message['video'].get('duration'),
            'width': latest_video_message['video'].get('width'),
            'height': latest_video_message['video'].get('height'),
            'mime_type': latest_video_message['video'].get('mime_type')
        }
        return output_filepath, video_metadata

    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram API request failed: {e}", exc_info=True)
        return None, None
    except Exception as e:
        logger.error(f"Error in get_latest_video_from_bot_chat: {e}", exc_info=True)
        return None, None

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
