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
            logging.info(f"Mengunggah video reguler: {file_path} dengan deskripsi: {caption[:50]}...")
            response = requests.post(url, params=params, files=files, timeout=300) # Timeout lebih lama untuk video
            response.raise_for_status()
            
            result = response.json()
            post_id = result.get('id')
            if post_id:
                logging.info(f"Video reguler berhasil diunggah. Post ID: {post_id}")
                return post_id
            else:
                logging.error(f"Gagal mengunggah video reguler. Respon: {result}")
                return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Kesalahan saat mengunggah video reguler: {e}")
        _log_error_response(e)
        return None
    except Exception as e:
        logging.error(f"Terjadi kesalahan tak terduga saat mengunggah video reguler: {e}", exc_info=True)
        return None

def upload_reel(file_path, caption, access_token, page_id):
    """
    Mengunggah video sebagai Facebook Reel.
    Menggunakan alur upload_phase: start -> transfer -> finish.
    Mengembalikan post ID jika berhasil, None jika gagal.
    """
    url_base = f"https://graph.facebook.com/v23.0/{page_id}/video_reels"
    
    if not os.path.exists(file_path):
        logging.error(f"File video untuk Reels tidak ditemukan: {file_path}")
        return None

    # Langkah 1: Inisiasi upload (upload_phase=start)
    start_params = {
        'access_token': access_token,
        'upload_phase': 'start',
        'file_size': os.path.getsize(file_path)
    }
    
    try:
        logging.info("Memulai fase upload Reels (start)...")
        start_response = requests.post(url_base, params=start_params, timeout=30)
        start_response.raise_for_status()
        start_result = start_response.json()
        
        video_id = start_result.get('video_id')
        upload_url = start_result.get('upload_url')

        if not video_id or not upload_url:
            logging.error(f"Gagal memulai upload Reels. Respon: {start_result}")
            return None
        
        logging.info(f"Fase start berhasil. Video ID: {video_id}, Upload URL: {upload_url}")

        # Langkah 2: Transfer video (upload_phase=transfer)
        logging.info("Memulai fase upload Reels (transfer)...")
        with open(file_path, 'rb') as f:
            headers = {
                'Authorization': f'OAuth {access_token}',
                'Content-Type': 'application/octet-stream' # Penting: Tentukan tipe konten
            }
            # Gunakan requests.post langsung ke upload_url
            transfer_response = requests.post(upload_url, data=f, headers=headers, timeout=300) # Timeout lebih lama
            transfer_response.raise_for_status()
        
        logging.info("Fase transfer berhasil.")

        # Langkah 3: Selesaikan upload (upload_phase=finish)
        finish_params = {
            'access_token': access_token,
            'upload_phase': 'finish',
            'video_id': video_id,
            'description': caption, # Untuk Reels, gunakan 'description'
            'title': caption[:50] # Gunakan sebagian caption sebagai judul
        }
        
        logging.info("Memulai fase upload Reels (finish)...")
        finish_response = requests.post(url_base, params=finish_params, timeout=60)
        finish_response.raise_for_status()
        finish_result = finish_response.json()

        post_id = finish_result.get('id')
        if post_id:
            logging.info(f"Reels berhasil diunggah. Post ID: {post_id}")
            return post_id
        else:
            logging.error(f"Gagal menyelesaikan upload Reels. Respon: {finish_result}")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Kesalahan saat mengunggah Reels: {e}")
        _log_error_response(e) # Panggil fungsi pembantu untuk detail error
        return None
    except Exception as e:
        logging.error(f"Terjadi kesalahan tak terduga saat mengunggah Reels: {e}", exc_info=True)
        return None

if __name__ == '__main__':
    # Contoh penggunaan (untuk pengujian lokal)
    # Ganti dengan token akses, ID halaman, dan jalur file Anda yang sebenarnya
    TEST_FB_ACCESS_TOKEN = os.getenv('FB_ACCESS_TOKEN_TEST', 'YOUR_FB_ACCESS_TOKEN_HERE')
    TEST_FB_PAGE_ID = os.getenv('FB_PAGE_ID_TEST', 'YOUR_FB_PAGE_ID_HERE')
    
    # Buat file dummy untuk pengujian (ini hanya placeholder, Anda perlu file asli)
    test_photo_path = 'test_photo.jpg'
    test_video_path = 'test_video.mp4'
    test_reel_path = 'test_reel_upload.mp4' # Pastikan ini adalah video 9:16 dan <= 60s
    
    # Buat file dummy jika tidak ada (hanya untuk mencegah error FileNotFoundError)
    # Dalam penggunaan nyata, file ini akan diunduh dari Telegram
    if not os.path.exists(test_photo_path):
        logging.warning(f"File '{test_photo_path}' tidak ditemukan. Buat file foto dummy untuk pengujian.")
        # from PIL import Image
        # img = Image.new('RGB', (60, 30), color = 'red')
        # img.save(test_photo_path)
    
    if not os.path.exists(test_video_path):
        logging.warning(f"File '{test_video_path}' tidak ditemukan. Buat file video dummy untuk pengujian.")
        # Anda bisa membuat file dummy kosong atau mengunduh video kecil
        # with open(test_video_path, 'w') as f:
        #     f.write("dummy video content")

    if not os.path.exists(test_reel_path):
        logging.warning(f"File '{test_reel_path}' tidak ditemukan. Buat file video dummy untuk pengujian Reels.")
        # with open(test_reel_path, 'w') as f:
        #     f.write("dummy video content")

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

        # Uji upload video reguler
        if os.path.exists(test_video_path):
            print(f"Mengunggah video reguler... Post ID: {upload_video(test_video_path, 'Ini video uji dari Python!', TEST_FB_ACCESS_TOKEN, TEST_FB_PAGE_ID)}")
        else:
            print(f"Melewatkan uji upload video karena '{test_video_path}' tidak ada.")

        print("-" * 30)

        # Uji upload Reels
        if os.path.exists(test_reel_path):
            print(f"Mengunggah Reels... Post ID: {upload_reel(test_reel_path, 'Ini Reels uji dari Python!', TEST_FB_ACCESS_TOKEN, TEST_FB_PAGE_ID)}")
        else:
            print(f"Melewatkan uji upload Reels karena '{test_reel_path}' tidak ada.")
