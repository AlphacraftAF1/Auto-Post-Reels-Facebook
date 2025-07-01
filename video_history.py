# video_history.py
import json
import os

POSTED_HISTORY_FILE = "posted.json"

def load_posted_videos():
    """Memuat daftar ID video yang sudah diposting dari file."""
    if not os.path.exists(POSTED_HISTORY_FILE):
        return []
    try:
        with open(POSTED_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: {POSTED_HISTORY_FILE} kosong atau rusak. Membuat file baru.")
        return []
    except Exception as e:
        print(f"Error saat memuat riwayat video: {e}")
        return []

def save_posted_videos(video_ids):
    """Menyimpan daftar ID video yang sudah diposting ke file."""
    try:
        with open(POSTED_HISTORY_FILE, 'w') as f:
            json.dump(video_ids, f, indent=4)
    except Exception as e:
        print(f"Error saat menyimpan riwayat video: {e}")

def is_video_posted(video_id):
    """Memeriksa apakah video_id sudah ada dalam riwayat."""
    posted_videos = load_posted_videos()
    return video_id in posted_videos

def add_posted_video(video_id):
    """Menambahkan video_id ke riwayat posting."""
    posted_videos = load_posted_videos()
    if video_id not in posted_videos:
        posted_videos.append(video_id)
        save_posted_videos(posted_videos)
        print(f"Video ID '{video_id}' ditambahkan ke riwayat.")
    else:
        print(f"Video ID '{video_id}' sudah ada dalam riwayat.")

# Contoh penggunaan (bisa dihapus nanti)
if __name__ == "__main__":
    # Pastikan posted.json ada atau akan dibuat
    if os.path.exists(POSTED_HISTORY_FILE):
        os.remove(POSTED_HISTORY_FILE) # Hapus untuk percobaan bersih

    print(f"Is 'video123' posted? {is_video_posted('video123')}")
    add_posted_video('video123')
    print(f"Is 'video123' posted? {is_video_posted('video123')}")
    add_posted_video('video456')
    print(f"Is 'video456' posted? {is_video_posted('video456')}")
    print(f"Is 'video789' posted? {is_video_posted('video789')}")

    print("\nKonten posted.json:")
    with open(POSTED_HISTORY_FILE, 'r') as f:
        print(f.read())
