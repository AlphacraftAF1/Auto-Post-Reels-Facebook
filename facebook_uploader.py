import requests
import os
import logging
import json

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _log_error_response(e):
    """Fungsi pembantu untuk mencatat detail respons error HTTP."""
    if hasattr(e, 'response') and e.response is not None:
        try:
            error_details = e.response.json()
            logging.error(f"Detail Error Respon Facebook: {json.dumps(error_details, indent=2)}")
        except json.JSONDecodeError:
            logging.error(f"Respon Error Facebook (non-JSON): {e.response.text}")
    else:
        logging.error(f"Tidak ada detail respon dari Facebook.")

def upload_photo(file_path, caption, access_token, page_id):
    """
    Mengunggah foto ke halaman Facebook.
    Mengembalikan post ID jika berhasil, None jika gagal.
    """
    url = f"https://graph.facebook.com/v23.0/{page_id}/photos"
    
    if not os.path.exists(file_path):
        logging.error(f"File foto tidak ditemukan: {file_path}")
        return None

    params = {
        'access_token': access_token,
        'caption': caption
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {'source': f}
            logging.info(f"Mengunggah foto: {file_path} dengan caption: {caption[:50]}...")
            response = requests.post(url, params=params, files=files, timeout=120)
            response.raise_for_status() # Angkat HTTPError untuk kode status 4xx/5xx
            
            result = response.json()
            post_id = result.get('id')
            if post_id:
                logging.info(f"Foto berhasil diunggah. Post ID: {post_id}")
                return post_id
            else:
                logging.error(f"Gagal mengunggah foto. Respon: {result}")
                return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Kesalahan saat mengunggah foto: {e}")
        _log_error_response(e)
        return None
    except Exception as e:
        logging.error(f"Terjadi kesalahan tak terduga saat mengunggah foto: {e}", exc_info=True)
        return None

def upload_video(file_path, caption, access_token, page_id):
    """
    Mengunggah video reguler ke halaman Facebook.
    Facebook akan otomatis mendeteksi jika video memenuhi syarat Reels (durasi <= 60s, rasio 9:16).
    Mengembalikan post ID jika berhasil, None jika gagal.
    """
    url = f"https://graph.facebook.com/v23.0/{page_id}/videos"
    
    if not os.path.exists(file_path):
        logging.error(f"File video tidak ditemukan: {file_path}")
        return None

    params = {
        'access_token': access_token,
        'description': caption, # Untuk video reguler, gunakan 'description' bukan 'caption'
        'title': caption[:50] # Gunakan sebagian caption sebagai judul
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {'source': f}
            logging.info(f"Mengunggah video: {file_path} dengan deskripsi: {caption[:50]}...")
            response = requests.post(url, params=params, files=files, timeout=300) # Timeout lebih lama untuk video
            response.raise_for_status()
            
            result = response.json()
            post_id = result.get('id')
            if post_id:
                logging.info(f"Video berhasil diunggah. Post ID: {post_id}")
                return post_id
            else:
                logging.error(f"Gagal mengunggah video. Respon: {result}")
                return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Kesalahan saat mengunggah video: {e}")
        _log_error_response(e)
        return None
    except Exception as e:
        logging.error(f"Terjadi kesalahan tak terduga saat mengunggah video: {e}", exc_info=True)
        return None

# Fungsi upload_reel() dihapus karena tidak lagi diperlukan.
# Facebook akan otomatis mendeteksi Reels dari upload_video() jika memenuhi syarat.

if __name__ == '__main__':
    # Contoh penggunaan (untuk pengujian lokal)
    # Ganti dengan token akses, ID halaman, dan jalur file Anda yang sebenarnya
    TEST_FB_ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN_TEST', 'YOUR_FB_ACCESS_TOKEN_HERE')
    TEST_FB_PAGE_ID = os.getenv('FB_PAGE_ID_TEST', 'YOUR_FB_PAGE_ID_HERE')
    
    # Buat file dummy untuk pengujian (ini hanya placeholder, Anda perlu file asli)
    test_photo_path = 'test_photo.jpg'
    test_video_path = 'test_video.mp4' # Ini akan diunggah sebagai video biasa atau Reels
    
    # Buat file dummy jika tidak ada (hanya untuk mencegah error FileNotFoundError)
    if not os.path.exists(test_photo_path):
        logging.warning(f"File '{test_photo_path}' tidak ditemukan. Buat file foto dummy untuk pengujian.")
    
    if not os.path.exists(test_video_path):
        logging.warning(f"File '{test_video_path}' tidak ditemukan. Buat file video dummy untuk pengujian.")

    if TEST_FB_ACCESS_TOKEN == 'YOUR_FB_ACCESS_TOKEN_HERE' or TEST_FB_PAGE_ID == 'YOUR_FB_PAGE_ID_HERE':
        logging.warning("Variabel lingkungan FB_ACCESS_TOKEN_TEST atau FB_PAGE_ID_TEST tidak diatur. Tidak dapat menjalankan contoh Facebook Uploader.")
    else:
        logging.info("Menjalankan contoh facebook_uploader.py...")
        
        # Uji upload foto
        if os.path.exists(test_photo_path):
            print(f"Mengunggah foto... Post ID: {upload_photo(test_photo_path, 'Ini foto uji dari Python!', TEST_FB_ACCESS_TOKEN, TEST_FB_PAGE_ID)}")
        else:
            print(f"Melewatkan uji upload foto karena '{test_photo_path}' tidak ada.")

        print("-" * 30)

        # Uji upload video (akan otomatis jadi Reels jika memenuhi syarat)
        if os.path.exists(test_video_path):
            print(f"Mengunggah video... Post ID: {upload_video(test_video_path, 'Ini video uji Reels/Reguler dari Python!', TEST_FB_ACCESS_TOKEN, TEST_FB_PAGE_ID)}")
        else:
            print(f"Melewatkan uji upload video karena '{test_video_path}' tidak ada.")
