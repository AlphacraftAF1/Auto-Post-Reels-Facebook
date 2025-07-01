# telegram_fetcher.py
import requests
import os
import json
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

def get_latest_media_from_bot_chat(bot_token, chat_id, output_folder):
    """
    Mengambil media (video atau foto) terbaru yang dikirim ke bot dari chat_id tertentu.
    Mengembalikan:
        - media_filepath (string): Path ke file yang didownload
        - media_info (dict): Metadata media dari Telegram (termasuk 'type': 'video'/'photo')
    Jika tidak ada media baru atau gagal, mengembalikan (None, None).
    """
    if not bot_token or not chat_id:
        logger.error("BOT_TOKEN or CHAT_ID not set for Telegram fetcher.")
        return None, None

    base_url = f"https://api.telegram.org/bot{bot_token}/"
    initial_offset_for_getupdates = get_last_update_offset() + 1
    
    params = {
        'offset': initial_offset_for_getupdates,
        'limit': 50, # Tingkatkan batas pengambilan update
        'timeout': 20
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

        max_update_id_in_batch = initial_offset_for_getupdates - 1 

        if updates:
            max_update_id_in_batch = max(u['update_id'] for u in updates)
        
        # --- PERUBAHAN DI SINI ---
        latest_media_update_object = None # Ini akan menyimpan seluruh objek 'update'
        # --- AKHIR PERUBAHAN ---

        media_type = None

        # Iterasi melalui update dari yang terbaru ke terlama
        for update_item in sorted(updates, key=lambda x: x['update_id'], reverse=True):
            if 'message' in update_item:
                message = update_item['message']
                if str(message['chat']['id']) == str(chat_id):
                    # Kita menemukan media dari chat yang benar
                    if 'video' in message:
                        latest_media_update_object = update_item # Simpan seluruh objek update
                        media_type = 'video'
                        logger.info(f"Found a video message (Update ID: {update_item['update_id']}).")
                        break # Hentikan loop, kita sudah menemukan media terbaru yang valid
                    elif 'photo' in message:
                        latest_media_update_object = update_item # Simpan seluruh objek update
                        media_type = 'photo'
                        logger.info(f"Found a photo message (Update ID: {update_item['update_id']}).")
                        break # Hentikan loop, kita sudah menemukan media terbaru yang valid
        
        # --- PERUBAHAN DI SINI ---
        # Simpan offset berdasarkan update_id dari objek update yang ditemukan
        if latest_media_update_object:
            save_last_update_offset(latest_media_update_object['update_id'])
        else: # Jika tidak ada media yang ditemukan dalam batch ini
            save_last_update_offset(max_update_id_in_batch)

        if not latest_media_update_object: # Sekarang cek objek update_object, bukan message
            logger.info(f"No new video or photo message found from CHAT_ID '{chat_id}' in fetched updates.")
            return None, None
        
        # Dapatkan objek message dari update_object yang ditemukan
        latest_media_message = latest_media_update_object['message']
        # --- AKHIR PERUBAHAN ---

        file_id = None
        file_unique_id = None
        largest_photo = None 

        if media_type == 'video':
            file_id = latest_media_message['video']['file_id']
            file_unique_id = latest_media_message['video']['file_unique_id']
        elif media_type == 'photo':
            largest_photo = latest_media_message['photo'][-1]
            file_id = largest_photo['file_id']
            file_unique_id = largest_photo['file_unique_id']

        if not file_id:
            logger.error("No file_id found for the detected media.")
            return None, None

        get_file_url = f"{base_url}getFile"
        file_response = requests.get(get_file_url, params={'file_id': file_id})
        file_response.raise_for_status()
        file_info = file_response.json().get('result', {})

        if not file_info or 'file_path' not in file_info:
            logger.error(f"Could not get file info from Telegram for file_id: {file_id}")
            return None, None

        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_info['file_path']}"
        
        file_extension = "bin"
        if file_info.get('file_path'):
            _, ext = os.path.splitext(file_info['file_path'])
            if ext:
                file_extension = ext.lstrip('.')
        
        output_filepath = os.path.join(output_folder, f"{file_unique_id}.{file_extension}")

        if os.path.exists(output_filepath):
            logger.info(f"File {output_filepath} already exists. Assuming it was processed. Skipping download.")
            return None, None

        logger.info(f"Downloading {media_type} from Telegram URL: {download_url}")
        file_download_response = requests.get(download_url, stream=True)
        file_download_response.raise_for_status()

        with open(output_filepath, 'wb') as f:
            for chunk in file_download_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"{media_type.capitalize()} downloaded successfully to: {output_filepath}")
        
        media_metadata = {
            'type': media_type,
            'file_id': file_id,
            'file_unique_id': file_unique_id,
            'caption': latest_media_message.get('caption', f"{media_type.capitalize()} dari Telegram"),
            'duration': latest_media_message['video'].get('duration') if media_type == 'video' else None,
            'width': latest_media_message['video'].get('width') if media_type == 'video' else (largest_photo.get('width') if media_type == 'photo' else None),
            'height': latest_media_message['video'].get('height') if media_type == 'video' else (largest_photo.get('height') if media_type == 'photo' else None),
            'mime_type': file_info.get('mime_type') or (f'image/{file_extension}' if media_type == 'photo' else None)
        }
        return output_filepath, media_metadata

    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram API request failed: {e}", exc_info=True)
        return None, None
    except Exception as e:
        logger.error(f"Error in get_latest_media_from_bot_chat: {e}", exc_info=True)
        return None, None

# Contoh penggunaan lokal (bisa dihapus nanti)
if __name__ == "__main__":
    pass
