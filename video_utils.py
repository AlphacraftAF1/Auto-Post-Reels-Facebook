# video_utils.py
import ffmpeg
import os

def get_video_duration(video_path):
    """Mendapatkan durasi video dalam detik."""
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        return duration
    except ffmpeg.Error as e:
        print(f"Error saat mendapatkan durasi video: {e.stderr.decode()}")
        return None
    except Exception as e:
        print(f"Error umum saat mendapatkan durasi video: {e}")
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
        print(f"Error saat mendapatkan resolusi video: {e.stderr.decode()}")
        return None, None
    except Exception as e:
        print(f"Error umum saat mendapatkan resolusi video: {e}")
        return None, None

def validate_video(video_path):
    """
    Memvalidasi video:
    1. Durasi kurang dari atau sama dengan 60 detik.
    2. Rasio aspek mendekati 9:16 (portrait).
    """
    if not os.path.exists(video_path):
        print(f"File video tidak ditemukan: {video_path}")
        return False

    duration = get_video_duration(video_path)
    if duration is None or duration > 60:
        print(f"Video terlalu panjang ({duration}s) atau durasi tidak dapat diidentifikasi.")
        return False

    width, height = get_video_resolution(video_path)
    if width is None or height is None:
        print("Resolusi video tidak dapat diidentifikasi.")
        return False

    # Hitung rasio aspek (tinggi / lebar) untuk portrait
    # Idealnya 16/9 = 1.777...
    # Kita berikan sedikit toleransi untuk variasi rasio aspek portrait
    aspect_ratio = height / width
    if not (aspect_ratio >= 1.6 and aspect_ratio <= 2.0): # Toleransi untuk 9:16 (1.77)
        print(f"Rasio aspek video tidak 9:16 (potrait). Rasio: {width}:{height} ({aspect_ratio:.2f})")
        return False

    print(f"Video valid: Durasi {duration:.2f}s, Resolusi {width}x{height}")
    return True

# Contoh penggunaan (bisa dihapus nanti)
if __name__ == "__main__":
    # Buat dummy video atau gunakan video yang ada untuk testing
    # Pastikan ffmpeg terinstal dan dapat diakses dari PATH sistem
    dummy_video_path_valid = "videos/dummy_valid.mp4"
    dummy_video_path_long = "videos/dummy_long.mp4"
    dummy_video_path_landscape = "videos/dummy_landscape.mp4"

    # Untuk testing, Anda perlu membuat file video dummy atau menggunakan video sungguhan
    # Contoh: Video 10 detik, 1080x1920 (9:16)
    # Anda bisa membuat dengan ffmpeg:
    # ffmpeg -f lavfi -i color=c=blue:s=1080x1920:d=10 -vf "drawtext=text='Valid Short':fontcolor=white:fontsize=100:x=(w-text_w)/2:y=(h-text_h)/2" -c:v libx264 -preset veryfast -crf 23 -y videos/dummy_valid.mp4
    # Video 70 detik, 1080x1920 (9:16)
    # ffmpeg -f lavfi -i color=c=red:s=1080x1920:d=70 -vf "drawtext=text='Long Short':fontcolor=white:fontsize=100:x=(w-text_w)/2:y=(h-text_h)/2" -c:v libx264 -preset veryfast -crf 23 -y videos/dummy_long.mp4
    # Video 10 detik, 1920x1080 (16:9)
    # ffmpeg -f lavfi -i color=c=green:s=1920x1080:d=10 -vf "drawtext=text='Landscape Short':fontcolor=white:fontsize=100:x=(w-text_w)/2:y=(h-text_h)/2" -c:v libx264 -preset veryfast -crf 23 -y videos/dummy_landscape.mp4

    print(f"Validasi {dummy_video_path_valid}: {validate_video(dummy_video_path_valid)}")
    print(f"Validasi {dummy_video_path_long}: {validate_video(dummy_video_path_long)}")
    print(f"Validasi {dummy_video_path_landscape}: {validate_video(dummy_video_path_landscape)}")
