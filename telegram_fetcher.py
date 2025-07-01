import requests
import os
import json
import logging

logger = logging.getLogger(__name__)

LAST_UPDATE_OFFSET_FILE = "last_update_offset.txt"
POSTED_MEDIA_FILE = "posted_media.json"

def load_posted_ids():
    if os.path.exists(POSTED_MEDIA_FILE):
        with open(POSTED_MEDIA_FILE) as f:
            return json.load(f)
    return {}

def save_last_update_offset(offset):
    try:
        with open(LAST_UPDATE_OFFSET_FILE, "w") as f:
            f.write(str(offset))
        logger.info(f"Saved last update offset: {offset}")
    except Exception as e:
        logger.error(f"Failed to save last update offset: {e}")

def get_last_update_offset():
    if os.path.exists(LAST_UPDATE_OFFSET_FILE):
        try:
            with open(LAST_UPDATE_OFFSET_FILE, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError) as e:
            logger.warning(f"Could not read last update offset, starting fresh. Error: {e}")
            return 0
    return 0

def get_latest_media_from_bot_chat(bot_token, chat_id, output_folder):
    if not bot_token or not chat_id:
        logger.error("BOT_TOKEN or CHAT_ID not set for Telegram fetcher.")
        return None, None

    base_url = f"https://api.telegram.org/bot{bot_token}/"
    offset = get_last_update_offset() + 1
    posted_ids = load_posted_ids()

    params = {
        'offset': offset,
        'limit': 50,
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

        max_update_id = offset - 1

        for update in sorted(updates, key=lambda x: x['update_id']):
            max_update_id = max(max_update_id, update['update_id'])
            message = update.get('message')
            if not message or str(message.get('chat', {}).get('id')) != str(chat_id):
                continue

            media_type = None
            file_id = None
            file_unique_id = None
            largest_photo = None

            if 'video' in message:
                media_type = 'video'
                file_id = message['video']['file_id']
                file_unique_id = message['video']['file_unique_id']
            elif 'photo' in message:
                media_type = 'photo'
                largest_photo = message['photo'][-1]
                file_id = largest_photo['file_id']
                file_unique_id = largest_photo['file_unique_id']

            if not file_id or not file_unique_id:
                continue

            if file_unique_id in posted_ids:
                logger.info(f"Media sudah pernah diposting: {file_unique_id}")
                continue

            get_file_url = f"{base_url}getFile"
            file_response = requests.get(get_file_url, params={'file_id': file_id})
            file_response.raise_for_status()
            file_info = file_response.json().get('result', {})

            if not file_info or 'file_path' not in file_info:
                continue

            download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_info['file_path']}"
            file_extension = "bin"
            if file_info.get('file_path'):
                _, ext = os.path.splitext(file_info['file_path'])
                if ext:
                    file_extension = ext.lstrip('.')

            output_filepath = os.path.join(output_folder, f"{file_unique_id}.{file_extension}")

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            logger.info(f"Downloading {media_type} from Telegram URL: {download_url}")
            file_download_response = requests.get(download_url, stream=True)
            file_download_response.raise_for_status()

            with open(output_filepath, 'wb') as f:
                for chunk in file_download_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            message_media = message['video'] if media_type == 'video' else largest_photo
            caption = message.get('caption', f"{media_type.capitalize()} dari Telegram")

            save_last_update_offset(update['update_id'])
            logger.info(f"{media_type.capitalize()} downloaded successfully to: {output_filepath}")

            media_metadata = {
                'type': media_type,
                'file_id': file_id,
                'file_unique_id': file_unique_id,
                'caption': caption,
                'duration': message_media.get('duration'),
                'width': message_media.get('width'),
                'height': message_media.get('height'),
                'mime_type': file_info.get('mime_type') or (f'image/{file_extension}' if media_type == 'photo' else None)
            }
            return output_filepath, media_metadata

        save_last_update_offset(max_update_id)
        logger.info("Tidak ada media baru yang belum diposting.")
        return None, None

    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram API request failed: {e}", exc_info=True)
        return None, None
    except Exception as e:
        logger.error(f"Error in get_latest_media_from_bot_chat: {e}", exc_info=True)
        return None, None

# Contoh penggunaan lokal (bisa dihapus nanti)
if __name__ == "__main__":
    pass
