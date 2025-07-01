# facebook_uploader.py
import requests
import os
import logging
import json
import time

logger = logging.getLogger(__name__)

FB_GRAPH_API_BASE = "https://graph.facebook.com/V23.0" # Pastikan versi API terbaru

def get_upload_status(upload_phase_id, fb_access_token):
    """Memeriksa status upload video."""
    status_url = f"{FB_GRAPH_API_BASE}/{upload_phase_id}"
    params = {
        "access_token": fb_access_token
    }
    try:
        response = requests.get(status_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking upload status for {upload_phase_id}: {e}", exc_info=True)
        return None

def upload_video_chunked(video_path, upload_session_id, fb_access_token, start_offset=0):
    """Mengunggah video dalam potongan (chunk) untuk upload yang lebih besar."""
    chunk_size = 1024 * 1024 * 5  # 5 MB chunks
    file_size = os.path.getsize(video_path)
    
    logger.info(f"Memulai upload chunked untuk video: {video_path} (Ukuran: {file_size} bytes)")

    with open(video_path, 'rb') as f:
        f.seek(start_offset)
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            end_offset = start_offset + len(chunk)
            headers = {
                "Authorization": f"OAuth {fb_access_token}",
                "Content-Type": "application/octet-stream",
                "file_offset": str(start_offset),
                "X-Entity-Type": "file",
                "X-Entity-Name": os.path.basename(video_path),
                "X-Entity-Length": str(file_size),
                "X-Facebook-Graph-Api-Version": "v19.0", # Pastikan versi API
            }
            
            try:
                response = requests.post(
                    f"{FB_GRAPH_API_BASE}/{upload_session_id}",
                    headers=headers,
                    data=chunk,
                    timeout=300 # Timeout untuk upload chunk
                )
                response.raise_for_status()
                logger.info(f"Chunk uploaded: {start_offset}-{end_offset}/{file_size} bytes. Response: {response.json()}")
                start_offset = end_offset
            except requests.exceptions.RequestException as e:
                logger.error(f"Error uploading chunk {start_offset}-{end_offset}: {e}", exc_info=True)
                return False
    return True

def publish_video(page_id, fb_access_token, file_size, file_path, description, is_reel=False):
    """Memulai sesi upload dan mempublikasikan video."""
    
    # 1. Inisialisasi sesi upload
    upload_url = f"{FB_GRAPH_API_BASE}/{page_id}/videos"
    params = {
        "access_token": fb_access_token,
        "upload_phase": "start",
        "file_size": file_size
    }
    if is_reel:
        params["is_reel"] = True # Tambahkan parameter is_reel untuk Reels

    try:
        response = requests.post(upload_url, params=params)
        response.raise_for_status()
        upload_data = response.json()
        upload_session_id = upload_data.get("upload_session_id")
        video_id = upload_data.get("video_id")
        
        if not upload_session_id or not video_id:
            logger.error(f"Gagal memulai sesi upload: {upload_data}")
            return False, None
        
        logger.info(f"Sesi upload dimulai. Session ID: {upload_session_id}, Video ID: {video_id}")

        # 2. Upload video dalam chunk
        if not upload_video_chunked(file_path, upload_session_id, fb_access_token):
            logger.error("Gagal mengunggah chunk video.")
            return False, None

        # 3. Selesaikan sesi upload
        finish_url = f"{FB_GRAPH_API_BASE}/{page_id}/videos"
        params = {
            "access_token": fb_access_token,
            "upload_phase": "finish",
            "upload_session_id": upload_session_id,
            "description": description,
            "video_id": video_id,
        }
        # Jika itu Reels, tambahkan parameter is_reel lagi
        if is_reel:
            params["is_reel"] = True

        response = requests.post(finish_url, params=params)
        response.raise_for_status()
        publish_data = response.json()
        
        if publish_data.get("success") or publish_data.get("id"):
            logger.info(f"Video berhasil dipublikasikan. Post ID: {publish_data.get('id')}")
            return True, publish_data.get("id")
        else:
            logger.error(f"Gagal mempublikasikan video: {publish_data}")
            return False, None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error saat mempublikasikan video: {e}", exc_info=True)
        return False, None
    except Exception as e:
        logger.error(f"Terjadi kesalahan tak terduga di publish_video: {e}", exc_info=True)
        return False, None


def upload_reel(video_path, description):
    """Mengunggah video sebagai Facebook Reel."""
    page_id = os.getenv("FB_PAGE_ID")
    fb_access_token = os.getenv("FB_ACCESS_TOKEN")

    if not page_id or not fb_access_token:
        logger.error("FB_PAGE_ID atau FB_ACCESS_TOKEN tidak ditemukan di environment variables.")
        return False, None

    file_size = os.path.getsize(video_path)
    logger.info(f"Mencoba mengupload Reels: {video_path} dengan deskripsi: {description}")
    
    return publish_video(page_id, fb_access_token, file_size, video_path, description, is_reel=True)

def upload_regular_video(video_path, description):
    """Mengunggah video sebagai video Facebook biasa."""
    page_id = os.getenv("FB_PAGE_ID")
    fb_access_token = os.getenv("FB_ACCESS_TOKEN")

    if not page_id or not fb_access_token:
        logger.error("FB_PAGE_ID atau FB_ACCESS_TOKEN tidak ditemukan di environment variables.")
        return False, None

    file_size = os.path.getsize(video_path)
    logger.info(f"Mencoba mengupload video reguler: {video_path} dengan deskripsi: {description}")
    
    return publish_video(page_id, fb_access_token, file_size, video_path, description, is_reel=False)

def upload_photo(photo_path, description):
    """Mengunggah foto ke Facebook Page."""
    page_id = os.getenv("FB_PAGE_ID")
    fb_access_token = os.getenv("FB_ACCESS_TOKEN")

    if not page_id or not fb_access_token:
        logger.error("FB_PAGE_ID atau FB_ACCESS_TOKEN tidak ditemukan di environment variables.")
        return False, None

    url = f"{FB_GRAPH_API_BASE}/{page_id}/photos"
    params = {
        "access_token": fb_access_token,
        "caption": description
    }
    files = {
        "source": open(photo_path, "rb")
    }

    try:
        logger.info(f"Mencoba mengupload foto: {photo_path} dengan deskripsi: {description}")
        response = requests.post(url, params=params, files=files, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        if result.get("id"):
            logger.info(f"Foto berhasil diupload. Post ID: {result.get('id')}")
            return True, result.get("id")
        else:
            logger.error(f"Gagal mengupload foto: {result}")
            return False, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error saat mengupload foto: {e}", exc_info=True)
        return False, None
    except Exception as e:
        logger.error(f"Terjadi kesalahan tak terduga di upload_photo: {e}", exc_info=True)
        return False, None
    finally:
        if "source" in files:
            files["source"].close() # Pastikan file ditutup

if __name__ == "__main__":
    # Contoh penggunaan (pastikan Anda memiliki file media dan variabel env diset)
    # os.environ["FB_PAGE_ID"] = "YOUR_PAGE_ID"
    # os.environ["FB_ACCESS_TOKEN"] = "YOUR_ACCESS_TOKEN"
    # test_video_path = "path/to/your/test_video.mp4"
    # test_photo_path = "path/to/your/test_photo.jpg"
    #
    # # Test Reel Upload
    # success, post_id = upload_reel(test_video_path, "Test Reel from Python!")
    # print(f"Reel Upload Success: {success}, Post ID: {post_id}")
    #
    # # Test Regular Video Upload
    # success, post_id = upload_regular_video(test_video_path, "Test Regular Video from Python!")
    # print(f"Regular Video Upload Success: {success}, Post ID: {post_id}")
    #
    # # Test Photo Upload
    # success, post_id = upload_photo(test_photo_path, "Test Photo from Python!")
    # print(f"Photo Upload Success: {success}, Post ID: {post_id}")
    pass
