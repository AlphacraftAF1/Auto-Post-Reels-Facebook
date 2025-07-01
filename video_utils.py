import subprocess
import json
import logging
import os

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_video_info(video_path):
    """
    Mendapatkan informasi video (durasi, lebar, tinggi) menggunakan ffprobe.
    Mengembalikan dictionary dengan 'duration', 'width', 'height' atau None jika gagal.
    """
    if not os.path.exists(video_path):
        logging.error(f"File video tidak ditemukan: {video_path}")
        return None

    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0', # Pilih stream video pertama
        '-show_entries', 'stream=width,height,duration',
        '-of', 'json',
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        video_data = json.loads(result.stdout)
        
        if 'streams' in video_data and len(video_data['streams']) > 0:
            stream = video_data['streams'][0]
            duration = float(stream.get('duration', 0))
            width = int(stream.get('width', 0))
            height = int(stream.get('height', 0))
            
            return {
                'duration': duration,
                'width': width,
                'height': height
            }
        else:
            logging.error(f"Tidak dapat menemukan stream video di {video_path}")
            return None
    except FileNotFoundError:
        logging.error("FFmpeg/ffprobe tidak ditemukan. Pastikan sudah terinstal dan ada di PATH.")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"ffprobe mengembalikan error: {e.stderr}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Gagal mengurai output JSON dari ffprobe untuk {video_path}")
        return None
    except Exception as e:
        logging.error(f"Terjadi kesalahan saat mendapatkan info video untuk {video_path}: {e}", exc_info=True)
        return None

def is_reel(video_path):
    """
    Memeriksa apakah video memenuhi kriteria Facebook Reels:
    - Durasi <= 60 detik
    - Rasio aspek 9:16 (portrait)
    """
    video_info = get_video_info(video_path)

    if not video_info:
        logging.warning(f"Tidak dapat memverifikasi video {video_path} untuk kriteria Reels.")
        return False

    duration = video_info['duration']
    width = video_info['width']
    height = video_info['height']

    logging.info(f"Info video {video_path}: Durasi={duration:.2f}s, Dimensi={width}x{height}")

    # Kriteria durasi: <= 90 detik
    if duration > 90:
        logging.info(f"Video bukan Reels: Durasi ({duration:.2f}s) lebih dari 60 detik.")
        return False

    # Kriteria rasio aspek: 9:16 (portrait)
    # Toleransi kecil untuk float comparison
    aspect_ratio_target = 9 / 16
    
    if height == 0: # Hindari pembagian dengan nol
        logging.warning(f"Tinggi video adalah nol untuk {video_path}. Tidak dapat menghitung rasio aspek.")
        return False

    current_aspect_ratio = width / height
    
    # Cek apakah rasio aspek mendekati 9:16
    # Misalnya, 0.5625 (9/16)
    # Toleransi 0.01 untuk fleksibilitas
    if abs(current_aspect_ratio - aspect_ratio_target) > 0.01:
        logging.info(f"Video bukan Reels: Rasio aspek ({current_aspect_ratio:.4f}) bukan 9:16 (target {aspect_ratio_target:.4f}).")
        return False

    logging.info(f"Video {video_path} memenuhi kriteria Reels.")
    return True

if __name__ == '__main__':
    # Contoh penggunaan (untuk pengujian lokal)
    # Anda perlu menyediakan file video untuk pengujian ini
    # Pastikan Anda memiliki FFmpeg/ffprobe terinstal di sistem Anda.

    # Buat dummy video file untuk pengujian (ini hanya placeholder, Anda perlu video asli)
    # Anda bisa menggunakan video pendek dari ponsel Anda dengan rasio 9:16
    
    # Contoh jalur video (ganti dengan jalur video yang ada di sistem Anda)
    test_video_path_reel = 'test_reel.mp4' # Contoh: video 9:16, < 60s
    test_video_path_regular = 'test_regular_video.mp4' # Contoh: video 16:9, > 60s
    
    # Buat file dummy jika tidak ada (hanya untuk mencegah error FileNotFoundError)
    # Dalam penggunaan nyata, file ini akan diunduh dari Telegram
    if not os.path.exists(test_video_path_reel):
        logging.warning(f"File '{test_video_path_reel}' tidak ditemukan. Buat file video dummy untuk pengujian.")
        # Anda bisa membuat file dummy kosong atau mengunduh video kecil
        # with open(test_video_path_reel, 'w') as f:
        #     f.write("dummy video content")
    
    if not os.path.exists(test_video_path_regular):
        logging.warning(f"File '{test_video_path_regular}' tidak ditemukan. Buat file video dummy untuk pengujian.")
        # with open(test_video_path_regular, 'w') as f:
        #     f.write("dummy video content")

    logging.info("Menjalankan contoh video_utils.py...")

    # Uji dengan video yang seharusnya menjadi Reels
    if os.path.exists(test_video_path_reel):
        print(f"'{test_video_path_reel}' adalah Reels? {is_reel(test_video_path_reel)}")
    else:
        print(f"Tidak dapat menguji '{test_video_path_reel}' karena file tidak ada.")

    print("-" * 30)

    # Uji dengan video yang seharusnya bukan Reels
    if os.path.exists(test_video_path_regular):
        print(f"'{test_video_path_regular}' adalah Reels? {is_reel(test_video_path_regular)}")
    else:
        print(f"Tidak dapat menguji '{test_video_path_regular}' karena file tidak ada.")
