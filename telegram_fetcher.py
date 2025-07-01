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
    initial_offset_for_getupdates = get_last_update_offset() + 1 # Ambil update setelah yang terakhir tersimpan
    
    # --- PERUBAHAN DI SINI ---
    # Ambil lebih banyak update (misal 50) untuk memastikan tidak melewatkan media
    params = {
        'offset': initial_offset_for_getupdates,
        'limit': 50, # Tingkatkan batas pengambilan update
        'timeout': 20
    }
    # --- AKHIR PERUBAHAN ---

    try:
        get_updates_url = f"{base_url}getUpdates"
        logger.info(f"Fetching updates from Telegram with offset: {params['offset']} and limit: {params['limit']}")
        response = requests.get(get_updates_url, params=params)
        response.raise_for_status()
        updates = response.json().get('result', [])

        if not updates:
            logger.info("No new updates found from Telegram.")
            return None, None

        # --- PERUBAHAN DI SINI: Logika offset yang lebih robust ---
        # Setelah mengambil update, kita selalu menyimpan update_id tertinggi yang kita lihat
        # Ini penting agar bot tidak terjebak mengulang update lama
        max_update_id_in_batch = initial_offset_for_getupdates -1 # Default jika tidak ada update

        if updates:
            max_update_id_in_batch = max(u['update_id'] for u in updates)
            # Offset akan disimpan *setelah* kita menentukan media yang akan diproses
            # atau jika tidak ada media yang ditemukan
        
        latest_media_message = None
        media_type = None

        # Iterasi melalui update dari yang terbaru ke terlama
        for update in sorted(updates, key=lambda x: x['update_id'], reverse=True):
            if 'message' in update:
                message = update['message']
                if str(message['chat']['id']) == str(chat_id):
                    # Kita menemukan media dari chat yang benar
                    if 'video' in message:
                        latest_media_message = message
                        media_type = 'video'
                        logger.info(f"Found a video message (Update ID: {update['update_id']}).")
                        break # Hentikan loop, kita sudah menemukan media terbaru yang valid
                    elif 'photo' in message:
                        latest_media_message = message
                        media_type = 'photo'
                        logger.info(f"Found a photo message (Update ID: {update['update_id']}).")
                        break # Hentikan loop, kita sudah menemukan media terbaru yang valid
        
        # --- Simpan offset setelah upaya pencarian media ---
        # Jika media ditemukan, kita simpan update_id dari media tersebut.
        # Jika tidak ada media yang ditemukan, kita simpan update_id tertinggi yang sudah dilihat.
        if latest_media_message:
            save_last_update_offset(latest_media_message['update_id'])
        else:
            save_last_update_offset(max_update_id_in_batch)
        # --- AKHIR PERUBAHAN ---

        if not latest_media_message:
            logger.info(f"No new video or photo message found from CHAT_ID '{chat_id}' in fetched updates.")
            return None, None

        # ... (bagian kode selanjutnya tetap sama untuk mendapatkan file_id, download, dan return)
