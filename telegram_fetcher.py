# telegram_fetcher.py
import requests
import os
import json
import logging

logger = logging.getLogger(__name__)

LAST_UPDATE_OFFSET_FILE = "last_update_offset.txt"

def get_last_update_offset():
    """Memuat offset update terakhir dari file."""
    if os.path.exists(LAST_UPDATE_OFFSET_FILE):
        with open(LAST_UPDATE_OFFSET_FILE, 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return 0

def save_last_update_offset(offset):
    """Menyimpan offset update terakhir ke file."""
    with open(LAST_UPDATE_OFFSET_FILE, 'w') as f:
        f.write(str(offset))

def get_latest_media_from_bot_chat(bot_token, chat_id, download_folder):
    """
    Mengambil media (foto atau video) terbaru dari bot Telegram.
    Mengembalikan path file yang diunduh dan informasi media (tipe, caption, file_unique_id).
    """
    offset = get_last_update_offset()
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {
        "offset": offset + 1,  # Mulai dari update setelah yang terakhir diproses
        "limit": 1,            # Hanya ambil 1 update terbaru
        "timeout": 30          # Timeout untuk request
    }

    try:
        logger.info(f"Mencoba mengambil update Telegram dengan offset: {params['offset']}")
        response = requests.get(url, params=params, timeout=40)
        response.raise_for_status()
        updates = response.json().get("result", [])

        if not updates:
            logger.info("Tidak ada update baru dari Telegram.")
            return None, None

        latest_update = updates[0]
        update_id = latest_update.get("update_id")
        
        # Simpan offset terbaru
        save_last_update_offset(update_id)
        logger.info(f"Offset Telegram terbaru disimpan: {update_id}")

        message = latest_update.get("message")
        if not message:
            logger.warning("Update Telegram tidak mengandung pesan.")
            return None, None

        file_id = None
        file_unique_id = None
        file_extension = None
        media_type = None
        caption = message.get("caption")

        # Prioritaskan video jika ada
        if "video" in message:
            video = message["video"]
            file_id = video["file_id"]
            file_unique_id = video["file_unique_id"]
            file_extension = ".mp4"
            media_type = "video"
            logger.info(f"Video ditemukan. File ID: {file_id}, Unique ID: {file_unique_id}")
        elif "photo" in message:
            # Ambil resolusi tertinggi
            photos = message["photo"]
            if photos:
                largest_photo = photos[-1] # Foto terakhir biasanya yang terbesar
                file_id = largest_photo["file_id"]
                file_unique_id = largest_photo["file_unique_id"]
                file_extension = ".jpg"
                media_type = "photo"
                logger.info(f"Foto ditemukan. File ID: {file_id}, Unique ID: {file_unique_id}")
        else:
            logger.info("Pesan tidak mengandung video atau foto yang didukung.")
            return None, None

        if not file_id:
            logger.warning("Tidak dapat menemukan file_id media dalam pesan.")
            return None, None

        # Dapatkan path file dari Telegram
        file_url_response = requests.get(f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}")
        file_url_response.raise_for_status()
        file_path = file_url_response.json()["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"

        # Unduh file
        local_file_path = os.path.join(download_folder, f"downloaded_media_{file_unique_id}{file_extension}")
        logger.info(f"Mengunduh media dari: {download_url} ke {local_file_path}")
        with requests.get(download_url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(local_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info("Media berhasil diunduh.")

        media_info = {
            "type": media_type,
            "caption": caption,
            "file_unique_id": file_unique_id
        }
        return local_file_path, media_info

    except requests.exceptions.RequestException as e:
        logger.error(f"Error saat mengambil atau mengunduh dari Telegram: {e}", exc_info=True)
        return None, None
    except Exception as e:
        logger.error(f"Terjadi kesalahan tak terduga di telegram_fetcher: {e}", exc_info=True)
        return None, None

if __name__ == "__main__":
    pass
