# main.py
import os
import random
import json
import time

from download_video import download_youtube_shorts
from video_utils import validate_video, get_video_duration
from reels_uploader import upload_reel
from video_history import add_posted_video, is_video_posted
from telegram_notify import send_telegram

# Konfigurasi
KEYWORDS = [
    "funny cat shorts",
    "funny dog shorts",
    "cute animal shorts",
    "comedy shorts",
    "prank shorts"
]
MAX_RETRIES = 3 # Jumlah percobaan jika ada kegagalan
VIDEO_FOLDER = "videos"
POSTED_HISTORY_FILE = "posted.json"

def main():
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)

    retry_count = 0
    while retry_count < MAX_RETRIES:
        keyword = random.choice(KEYWORDS)
        send_telegram(f"🔍 Mencari video YouTube Shorts dengan keyword: '{keyword}'")
        video_path = None
        video_info = None

        try:
            # 1. Download video
            print(f"Mencoba mendownload video dengan keyword: {keyword}")
            video_path, video_info = download_youtube_shorts(keyword, VIDEO_FOLDER)

            if not video_path or not video_info:
                send_telegram(f"⚠️ Gagal menemukan atau mendownload video untuk keyword: '{keyword}'. Mencoba lagi.")
                retry_count += 1
                time.sleep(5) # Jeda sebentar sebelum mencoba lagi
                continue

            video_title = video_info.get('title', 'No Title')
            video_url = video_info.get('webpage_url', 'No URL')

            # 2. Validasi video
            print(f"Validasi video: {video_path}")
            if not validate_video(video_path):
                send_telegram(f"❌ Video tidak valid (durasi > 60s atau rasio bukan 9:16): {video_title} ({video_url}). Mencoba video lain.")
                os.remove(video_path) # Hapus video yang tidak valid
                retry_count += 1
                time.sleep(5)
                continue

            # 3. Cek duplikasi
            video_id = video_info.get('id')
            if is_video_posted(video_id):
                send_telegram(f"🔁 Video sudah pernah diposting: {video_title} ({video_url}). Mencari video lain.")
                os.remove(video_path) # Hapus video duplikat
                retry_count += 1
                time.sleep(5)
                continue

            # 4. Upload ke Facebook Reels
            print(f"Mencoba mengupload video: {video_title} ke Facebook Reels.")
            description = f"{video_title} #shorts #reels #viral #foryou #lucu" # Deskripsi default
            success, reel_id = upload_reel(video_path, description)

            if success:
                add_posted_video(video_id)
                send_telegram(f"✅ Reels berhasil diposting!\nJudul: {video_title}\nURL Video Asli: {video_url}")
                print(f"Video '{video_title}' berhasil diposting dan ID disimpan.")
                # Hapus video lokal setelah berhasil diupload
                os.remove(video_path)
                print(f"Video lokal '{video_path}' dihapus.")
                break # Berhasil, keluar dari loop retry
            else:
                send_telegram(f"❌ Gagal posting Reels.\nJudul: {video_title}\nURL Video Asli: {video_url}\nCoba lagi.")
                print(f"Gagal mengupload video '{video_title}'.")
                retry_count += 1
                time.sleep(10) # Jeda lebih lama jika upload gagal
                if os.path.exists(video_path):
                    os.remove(video_path) # Hapus video jika upload gagal
                continue

        except Exception as e:
            error_message = f"🚨 Terjadi kesalahan umum: {e}. Mencoba lagi."
            send_telegram(error_message)
            print(error_message)
            retry_count += 1
            if video_path and os.path.exists(video_path):
                os.remove(video_path) # Pastikan video dihapus jika terjadi error
            time.sleep(10) # Jeda lebih lama jika ada error tak terduga

    if retry_count == MAX_RETRIES:
        final_fail_message = "💥 Gagal posting Reels setelah beberapa kali percobaan. Mohon periksa log atau konfigurasi."
        send_telegram(final_fail_message)
        print(final_fail_message)

if __name__ == "__main__":
    main()
