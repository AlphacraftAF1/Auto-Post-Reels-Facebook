# reels_uploader.py
import requests
import os

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

def upload_reel(video_path, description):
    """
    Mengunggah video ke Facebook Reels.
    Mengembalikan True jika sukses, False jika gagal, beserta ID Reels jika sukses.
    """
    if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
        print("FB_PAGE_ID atau FB_ACCESS_TOKEN tidak diatur.")
        return False, None
    if not os.path.exists(video_path):
        print(f"File video tidak ditemukan untuk diunggah: {video_path}")
        return False, None

    # Step 1: Inisiasi upload session
    init_url = f"https://graph.facebook.com/v23.0/{FB_PAGE_ID}/video_reels"
    init_params = {
        "upload_phase": "start",
        "access_token": FB_ACCESS_TOKEN
    }
    init_data = {
        "name": os.path.basename(video_path), # Menggunakan nama file sebagai nama sementara
        "file_size": os.path.getsize(video_path)
    }

    try:
        print("Memulai sesi upload Reels...")
        init_response = requests.post(init_url, params=init_params, json=init_data)
        init_response.raise_for_status() # Akan memicu exception untuk status kode error
        init_data = init_response.json()
        
        video_id = init_data.get("video_id")
        upload_url = init_data.get("upload_url")
        
        if not video_id or not upload_url:
            print(f"Gagal mendapatkan video_id atau upload_url dari inisiasi: {init_data}")
            return False, None

        # Step 2: Upload video
        print(f"Mengunggah video ke: {upload_url}...")
        with open(video_path, 'rb') as video_file:
            upload_response = requests.post(upload_url, data=video_file, headers={'Content-Type': 'video/mp4'})
            upload_response.raise_for_status()
            upload_data = upload_response.json()

        if not upload_data.get("success"):
            print(f"Gagal mengunggah video: {upload_data}")
            return False, None

        # Step 3: Selesaikan upload dan publish Reels
        print(f"Menyelesaikan upload dan mempublikasikan Reels (ID: {video_id})...")
        finish_url = f"https://graph.facebook.com/v23.0/{FB_PAGE_ID}/video_reels"
        finish_params = {
            "upload_phase": "finish",
            "video_id": video_id,
            "description": description,
            "access_token": FB_ACCESS_TOKEN
        }
        
        # Tambahkan status_update ke description
        # finish_params["description"] = f"{description}\n\nStatus Update: Ready to publish."


        finish_response = requests.post(finish_url, params=finish_params)
        finish_response.raise_for_status()
        finish_data = finish_response.json()

        if finish_data.get("success"):
            print(f"Reels berhasil diposting dengan ID: {video_id}")
            return True, video_id
        else:
            print(f"Gagal mempublikasikan Reels: {finish_data}")
            return False, None

    except requests.exceptions.RequestException as e:
        print(f"Error koneksi atau API Facebook: {e}")
        if e.response is not None:
            print(f"Respon Error: {e.response.text}")
        return False, None
    except Exception as e:
        print(f"Error umum saat mengunggah Reels: {e}")
        return False, None

# Contoh penggunaan (tidak bisa langsung jalan tanpa token dan video)
if __name__ == "__main__":
    # Untuk menjalankan ini, Anda perlu mengatur environment variables:
    # export FB_PAGE_ID="your_page_id"
    # export FB_ACCESS_TOKEN="your_access_token"
    # Dan memiliki file video di 'videos/test_video.mp4'
    
    # from video_utils import validate_video # Jika ingin memvalidasi sebelum upload
    # test_video_path = "videos/test_video.mp4" # Ganti dengan path video Anda
    # test_description = "Ini adalah video Reels percobaan dari bot saya!"

    # if os.path.exists(test_video_path):
    #     if validate_video(test_video_path): # Opsional: Validasi dulu
    #         success, reel_id = upload_reel(test_video_path, test_description)
    #         if success:
    #             print(f"Upload berhasil! Reel ID: {reel_id}")
    #         else:
    #             print("Upload gagal.")
    #     else:
    #         print("Video tidak valid untuk diupload.")
    # else:
    #     print(f"File {test_video_path} tidak ditemukan. Buat dummy video untuk tes.")
