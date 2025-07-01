# video_utils.py
import subprocess
import json
import logging

logger = logging.getLogger(__name__)

def get_video_metadata(video_path):
    """Mendapatkan metadata video menggunakan ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,duration_ts,nb_frames',
        '-of', 'json',
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        return metadata
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ffprobe: {e.stderr}", exc_info=True)
        return None
    except FileNotFoundError:
        logger.error("FFmpeg/ffprobe tidak ditemukan. Pastikan sudah terinstal dan ada di PATH.")
        return None
    except Exception as e:
        logger.error(f"Error getting video metadata: {e}", exc_info=True)
        return None

def get_video_duration(video_path):
    """Mendapatkan durasi video dalam detik."""
    metadata = get_video_metadata(video_path)
    if metadata and 'streams' in metadata and len(metadata['streams']) > 0:
        duration_ts = metadata['streams'][0].get('duration_ts')
        nb_frames = metadata['streams'][0].get('nb_frames')
        
        # ffprobe bisa memberikan duration_ts atau duration (float)
        # Jika duration_ts ada, itu adalah timestamp, perlu dihitung dengan framerate jika ada
        # Untuk kemudahan, kita bisa coba ambil 'duration' langsung dari format jika tersedia
        if 'format' in metadata and 'duration' in metadata['format']:
            duration = float(metadata['format']['duration'])
            logger.info(f"Durasi video (dari format): {duration} detik")
            return duration
        elif duration_ts:
            # Ini adalah fallback jika 'duration' tidak langsung tersedia di 'format'
            # Ini mungkin kurang akurat tanpa framerate, tapi bisa jadi estimasi
            logger.warning("Durasi tidak langsung tersedia, menggunakan duration_ts. Akurasi mungkin bervariasi.")
            return float(duration_ts) / 1000 # Asumsi ms
    logger.warning(f"Tidak dapat menentukan durasi video untuk {video_path}.")
    return 0

def validate_video(video_path):
    """
    Memvalidasi apakah video memenuhi persyaratan untuk Facebook Reels:
    - Durasi: 3 detik hingga 90 detik
    - Rasio aspek: 9:16 (portrait) atau 16:9 (landscape) atau 1:1 (square)
    """
    metadata = get_video_metadata(video_path)
    if not metadata or 'streams' not in metadata or not metadata['streams']:
        logger.error(f"Metadata video tidak ditemukan atau tidak valid untuk {video_path}.")
        return False

    video_stream = metadata['streams'][0]
    width = video_stream.get('width')
    height = video_stream.get('height')
    
    # Gunakan get_video_duration yang sudah ada
    duration = get_video_duration(video_path) 

    if not width or not height or not duration:
        logger.error(f"Metadata (width, height, duration) tidak lengkap untuk {video_path}.")
        return False

    # Validasi Durasi
    if not (3 <= duration <= 90):
        logger.warning(f"Durasi video ({duration:.2f}s) tidak dalam rentang 3-90 detik untuk Reels.")
        return False

    # Validasi Rasio Aspek
    aspect_ratio = width / height
    
    # Toleransi kecil untuk floating point comparison
    tolerance = 0.01

    is_portrait = abs(aspect_ratio - (9/16)) < tolerance
    is_landscape = abs(aspect_ratio - (16/9)) < tolerance
    is_square = abs(aspect_ratio - (1/1)) < tolerance

    if not (is_portrait or is_landscape or is_square):
        logger.warning(f"Rasio aspek video ({width}:{height}, {aspect_ratio:.2f}) tidak 9:16, 16:9, atau 1:1 untuk Reels.")
        return False

    logger.info(f"Video {video_path} valid untuk Reels (Durasi: {duration:.2f}s, Rasio: {width}:{height}).")
    return True

if __name__ == "__main__":
    # Contoh penggunaan (ganti dengan path video Anda)
    # test_video_portrait = "path/to/your/portrait_video.mp4"
    # test_video_landscape = "path/to/your/landscape_video.mp4"
    # test_video_square = "path/to/your/square_video.mp4"
    # test_video_short = "path/to/your/short_video.mp4" # < 3s
    # test_video_long = "path/to/your/long_video.mp4" # > 90s
    # test_video_invalid_ratio = "path/to/your/invalid_ratio_video.mp4"

    # print(f"Portrait video valid: {validate_video(test_video_portrait)}")
    # print(f"Landscape video valid: {validate_video(test_video_landscape)}")
    # print(f"Square video valid: {validate_video(test_video_square)}")
    # print(f"Short video valid: {validate_video(test_video_short)}")
    # print(f"Long video valid: {validate_video(test_video_long)}")
    # print(f"Invalid ratio video valid: {validate_video(test_video_invalid_ratio)}")
    pass
