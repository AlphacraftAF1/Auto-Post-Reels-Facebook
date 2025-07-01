# video_utils.py
import ffmpeg
import os
import logging

logger = logging.getLogger(__name__)

def get_video_duration(video_path):
    """Mendapatkan durasi video dalam detik."""
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        return duration
    except ffmpeg.Error as e:
        logger.error(f"Error getting video duration: {e.stderr.decode()}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"General error getting video duration: {e}", exc_info=True)
        return None

def get_video_resolution(video_path):
    """Mendapatkan resolusi (width, height) video."""
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream:
            width = video_stream['width']
            height = video_stream['height']
            return width, height
        return None, None
    except ffmpeg.Error as e:
        logger.error(f"Error getting video resolution: {e.stderr.decode()}", exc_info=True)
        return None, None
    except Exception as e:
        logger.error(f"General error getting video resolution: {e}", exc_info=True)
        return None, None

def validate_video(video_path):
    """
    Memvalidasi video:
    1. Durasi kurang dari atau sama dengan 60 detik.
    2. Rasio aspek mendekati 9:16 (portrait).
    """
    if not os.path.exists(video_path):
        logger.warning(f"Video file not found for validation: {video_path}")
        return False

    duration = get_video_duration(video_path)
    if duration is None or duration > 60:
        logger.warning(f"Video is too long ({duration}s) or duration could not be identified.")
        return False

    width, height = get_video_resolution(video_path)
    if width is None or height is None:
        logger.warning("Video resolution could not be identified.")
        return False

    # Hitung rasio aspek (tinggi / lebar) untuk portrait
    # Idealnya 16/9 = 1.777...
    # Kita berikan sedikit toleransi untuk variasi rasio aspek portrait
    aspect_ratio = height / width
    if not (aspect_ratio >= 1.6 and aspect_ratio <= 2.0): # Toleransi untuk 9:16 (1.77)
        logger.warning(f"Video aspect ratio is not 9:16 (portrait). Ratio: {width}:{height} ({aspect_ratio:.2f})")
        return False

    logger.info(f"Video valid: Duration {duration:.2f}s, Resolution {width}x{height}")
    return True

# Contoh penggunaan (bisa dihapus nanti)
if __name__ == "__main__":
    # Untuk testing, Anda perlu membuat file video dummy atau menggunakan video sungguhan
    # Pastikan ffmpeg terinstal dan dapat diakses dari PATH sistem
    print("Running video_utils.py as main for testing purposes.")
    # Example usage requires a video file, e.g.:
    # valid_test_video = "path/to/your/test_portrait_video.mp4"
    # if os.path.exists(valid_test_video):
    #     print(f"Validation for {valid_test_video}: {validate_video(valid_test_video)}")
    # else:
    #     print(f"Test video not found at {valid_test_video}")
