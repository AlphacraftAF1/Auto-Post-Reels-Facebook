import requests
import os
import logging
from urllib.parse import urlparse

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_message(bot_token, chat_id, text):
    """Mengirim pesan teks ke chat Telegram tertentu."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Akan memunculkan HTTPError untuk kode status 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Gagal mengirim pesan Telegram: {e}")
        raise

def fetch_new_media(bot_token, target_chat_id, last_offset, posted_media_ids):
    """
    Mengambil update terbaru dari Telegram dan mengunduh media.
    Mengembalikan semua media baru yang ditemukan (terurut terbaru ke terlama).
    """
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {
        'offset': last_offset + 1, # Mulai dari update setelah yang terakhir diproses
        'limit': 50, # Ambil hingga 50 update
        'timeout': 30 # Timeout untuk permintaan
    }
    
    new_media_updates_list = []
    current_max_offset = last_offset
    
    try:
        response = requests.get(url, params=params, timeout=40)
        response.raise_for_status() # Angkat HTTPError untuk kode status 4xx/5xx
        updates = response.json().get('result', [])

        if not updates:
            logging.info("Tidak ada update baru dari Telegram.")
            return [], last_offset

        # Urutkan update dari yang paling baru ke yang paling lama (reverse=True)
        updates.sort(key=lambda u: u['update_id'], reverse=True)

        for update in updates:
            current_max_offset = max(current_max_offset, update['update_id'])
            message = update.get('message')
            if not message:
                continue

            chat_id = message.get('chat', {}).get('id')
            if chat_id != target_chat_id:
                logging.debug(f"Melewatkan pesan dari chat ID {chat_id} (bukan target {target_chat_id}).")
                continue

            file_id = None
            file_unique_id = None
            media_type = None
            caption = message.get('caption', message.get('text', ''))

            if 'video' in message:
                video = message['video']
                file_id = video['file_id']
                file_unique_id = video['file_unique_id']
                media_type = 'video'
                width = video.get('width')
                height = video.get('height')
                duration = video.get('duration')
                logging.info(f"Ditemukan video (ID Unik: {file_unique_id})")
            elif 'photo' in message:
                photo = message['photo'][-1]
                file_id = photo['file_id']
                file_unique_id = photo['file_unique_id']
                media_type = 'photo'
                width = photo.get('width')
                height = photo.get('height')
                duration = None
                logging.info(f"Ditemukan foto (ID Unik: {file_unique_id})")
            else:
                logging.debug(f"Melewatkan pesan tanpa video atau foto (ID Update: {update['update_id']}).")
                continue
            
            # Unduh media (file_path akan digunakan nanti oleh main.py jika media ini diproses)
            # Kita unduh di sini agar metadata seperti dimensi bisa langsung didapat
            file_path = download_telegram_file(bot_token, file_id, file_unique_id, media_type)
            if file_path:
                media_info = {
                    'update_id': update['update_id'],
                    'file_id': file_id,
                    'file_unique_id': file_unique_id,
                    'file_path': file_path,
                    'type': media_type,
                    'caption': caption,
                    'width': width,
                    'height': height,
                    'duration': duration
                }
                new_media_updates_list.append(media_info)
            else:
                logging.error(f"Gagal mengunduh media {file_unique_id}. Tidak akan ditambahkan ke daftar.")

        return new_media_updates_list, current_max_offset

    except requests.exceptions.ConnectionError as e:
        logging.error(f"Kesalahan koneksi saat mengambil update Telegram: {e}")
        return [], last_offset
    except requests.exceptions.Timeout:
        logging.error("Permintaan getUpdates Telegram timeout.")
        return [], last_offset
    except requests.exceptions.RequestException as e:
        logging.error(f"Kesalahan saat mengambil update Telegram: {e}")
        return [], last_offset
    except Exception as e:
        logging.error(f"Terjadi kesalahan tak terduga saat mengambil update Telegram: {e}", exc_info=True)
        return [], last_offset

def download_telegram_file(bot_token, file_id, file_unique_id, media_type):
    """Mengunduh file dari Telegram menggunakan file_id."""
    get_file_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    try:
        response = requests.get(get_file_url, timeout=10)
        response.raise_for_status()
        file_info = response.json().get('result')
        if not file_info:
            logging.error(f"Tidak dapat mendapatkan info file untuk file_id: {file_id}")
            return None

        file_path_tg = file_info.get('file_path')
        if not file_path_tg:
            logging.error(f"File path tidak ditemukan untuk file_id: {file_id}")
            return None

        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path_tg}"
        
        # Tentukan ekstensi file berdasarkan tipe media
        if media_type == 'video':
            ext = os.path.splitext(urlparse(file_path_tg).path)[1] or '.mp4'
        elif media_type == 'photo':
            ext = os.path.splitext(urlparse(file_path_tg).path)[1] or '.jpg'
        else:
            ext = '.bin' # Fallback

        local_filename = f"{file_unique_id}{ext}"
        
        logging.info(f"Mengunduh {media_type} dari: {download_url} ke {local_filename}")
        file_response = requests.get(download_url, stream=True, timeout=60)
        file_response.raise_for_status()

        with open(local_filename, 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Berhasil mengunduh file: {local_filename}")
        return local_filename

    except requests.exceptions.RequestException as e:
        logging.error(f"Gagal mengunduh file Telegram {file_id}: {e}")
        return None
    except Exception as e:
        logging.error(f"Terjadi kesalahan tak terduga saat mengunduh file Telegram: {e}", exc_info=True)
        return None

if __name__ == '__main__':
    # Contoh penggunaan (untuk pengujian lokal)
    # Pastikan Anda memiliki BOT_TOKEN dan CHAT_ID yang valid di lingkungan Anda
    # atau ganti dengan nilai langsung untuk pengujian.
    TEST_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN_TEST', 'YOUR_BOT_TOKEN_HERE')
    TEST_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID_TEST', 'YOUR_CHAT_ID_HERE')) # Ganti dengan ID chat Anda
    
    if TEST_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE' or TEST_CHAT_ID == 'YOUR_CHAT_ID_HERE':
        logging.warning("Variabel lingkungan TELEGRAM_BOT_TOKEN_TEST atau TELEGRAM_CHAT_ID_TEST tidak diatur. Tidak dapat menjalankan contoh.")
    else:
        logging.info("Menjalankan contoh telegram_fetcher.py...")
        # Buat dummy posted_media_ids untuk pengujian
        dummy_posted_media = {'AgADBAADgqwxG8g0fVf': {'caption': 'Test', 'post_id': '123'}}
        
        # Ambil update dengan offset 0 untuk mendapatkan semua update terbaru
        media_list, new_offset = fetch_new_media(TEST_BOT_TOKEN, TEST_CHAT_ID, 0, dummy_posted_media)
        
        logging.info(f"Ditemukan {len(media_list)} media baru.")
        for media in media_list:
            logging.info(f"Tipe: {media['type']}, Path: {media['file_path']}, Caption: {media['caption'][:50]}...")
            # Hapus file yang diunduh setelah pengujian
            if os.path.exists(media['file_path']):
                os.remove(media['file_path'])
                logging.info(f"File pengujian dihapus: {media['file_path']}")
        logging.info(f"Offset terakhir yang diproses: {new_offset}")
