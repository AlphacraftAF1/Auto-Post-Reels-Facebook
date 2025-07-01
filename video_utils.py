# video_utils.py
import subprocess
import json
import logging
import re
import os # <-- BARU: import os

logger = logging.getLogger(__name__)

def get_video_metadata(video_path):
    """Mendapatkan metadata video menggunakan ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,codec_name',
        '-show_entries', 'format=duration',
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
    if metadata and 'format' in metadata and 'duration' in metadata['format']:
        duration = float(metadata['format']['duration'])
        logger.info(f"Durasi video: {duration} detik")
        return duration
    logger.warning(f"Tidak dapat menentukan durasi video untuk {video_path}.")
    return 0

def get_video_resolution(video_path):
    """Mendapatkan resolusi (width, height) video."""
    metadata = get_video_metadata(video_path)
    if metadata and 'streams' in metadata and len(metadata['streams']) > 0:
        video_stream = metadata['streams'][0]
        width = video_stream.get('width')
        height = video_stream.get('height')
        if width and height:
            return width, height
    logger.warning(f"Tidak dapat menentukan resolusi video untuk {video_path}.")
    return None, None

def validate_video(video_path):
    """
    Memvalidasi apakah video memenuhi persyaratan dasar untuk Facebook Reels:
    - Durasi: 3 detik hingga 90 detik
    - Rasio aspek: mendekati 9:16, 16:9, atau 1:1
    """
    if not os.path.exists(video_path):
        logger.warning(f"File video tidak ditemukan: {video_path}")
        return False

    duration = get_video_duration(video_path)
    if not (3 <= duration <= 90):
        logger.warning(f"Durasi video ({duration:.2f}s) tidak dalam rentang 3-90 detik untuk Reels.")
        return False

    width, height = get_video_resolution(video_path)
    if not width or not height:
        logger.warning("Resolusi video tidak dapat diidentifikasi.")
        return False

    aspect_ratio = width / height
    tolerance = 0.05 # Toleransi yang sedikit lebih longgar untuk rasio aspek

    is_portrait_9_16 = abs(aspect_ratio - (9/16)) < tolerance
    is_landscape_16_9 = abs(aspect_ratio - (16/9)) < tolerance
    is_square_1_1 = abs(aspect_ratio - (1/1)) < tolerance

    if not (is_portrait_9_16 or is_landscape_16_9 or is_square_1_1):
        logger.warning(f"Rasio aspek video ({width}:{height}, {aspect_ratio:.2f}) tidak mendekati 9:16, 16:9, atau 1:1 untuk Reels.")
        return False

    logger.info(f"Video {video_path} valid untuk Reels (Durasi: {duration:.2f}s, Rasio: {width}x{height}).")
    return True

if __name__ == "__main__":
    pass
