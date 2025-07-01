# media_history.py
import json
import os
import logging

logger = logging.getLogger(__name__)

POSTED_HISTORY_FILE = "posted.json" # Nama file history tetap sama

def load_posted_media(): # <-- Perubahan nama fungsi
    """Memuat daftar ID media yang sudah diposting dari file."""
    if not os.path.exists(POSTED_HISTORY_FILE):
        logger.info(f"'{POSTED_HISTORY_FILE}' tidak ditemukan. Mengembalikan daftar kosong.")
        return []
    try:
        with open(POSTED_HISTORY_FILE, 'r') as f:
            content = f.read().strip()
            if not content: # Tangani file kosong secara eksplisit
                logger.warning(f"'{POSTED_HISTORY_FILE}' kosong. Mengembalikan daftar kosong.")
                return []
            posted_ids = json.loads(content)
            logger.info(f"Memuat {len(posted_ids)} ID dari '{POSTED_HISTORY_FILE}'.")
            return posted_ids
    except json.JSONDecodeError as e:
        logger.error(f"Error mendekode JSON dari '{POSTED_HISTORY_FILE}': {e}. Mengembalikan daftar kosong.", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Error memuat riwayat media: {e}. Mengembalikan daftar kosong.", exc_info=True) # <-- Perubahan log
        return []

def save_posted_media(media_ids): # <-- Perubahan nama fungsi dan parameter
    """Menyimpan daftar ID media yang sudah diposting ke file."""
    try:
        with open(POSTED_HISTORY_FILE, 'w') as f:
            json.dump(media_ids, f, indent=4)
        logger.info(f"Menyimpan {len(media_ids)} ID ke '{POSTED_HISTORY_FILE}'.")
    except Exception as e:
        logger.error(f"Error menyimpan riwayat media: {e}", exc_info=True) # <-- Perubahan log

def is_media_posted(media_id): # <-- Perubahan nama fungsi dan parameter
    """Memeriksa apakah media_id sudah ada dalam riwayat."""
    posted_media = load_posted_media() # <-- Panggil fungsi baru
    is_posted = media_id in posted_media
    logger.info(f"Memeriksa apakah ID media '{media_id}' sudah diposting: {is_posted}") # <-- Perubahan log
    return is_posted

def add_posted_media(media_id): # <-- Perubahan nama fungsi dan parameter
    """Menambahkan media_id ke riwayat posting."""
    posted_media = load_posted_media() # <-- Panggil fungsi baru
    if media_id not in posted_media:
        posted_media.append(media_id)
        save_posted_media(posted_media) # <-- Panggil fungsi baru
        logger.info(f"ID media '{media_id}' ditambahkan ke riwayat.") # <-- Perubahan log
    else:
        logger.info(f"ID media '{media_id}' sudah ada dalam riwayat (melewati penambahan).") # <-- Perubahan log

# Contoh penggunaan lokal (bisa dihapus nanti)
if __name__ == "__main__":
    pass
