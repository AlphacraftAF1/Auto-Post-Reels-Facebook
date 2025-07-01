# reels_uploader.py
import requests
import os
import logging

logger = logging.getLogger(__name__)

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

def upload_reel(video_path, description):
    """
    Mengunggah video ke Facebook Reels.
    Mengembalikan True jika sukses, False jika gagal, beserta ID Reels jika sukses.
    """
    if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
        logger.error("FB_PAGE_ID or FB_ACCESS_TOKEN not set.")
        return False, None
    if not os.path.exists(video_path):
        logger.error(f"Video file not found for upload: {video_path}")
        return False, None

    # Step 1: Inisiasi upload session
    # Menggunakan Graph API v23.0 atau yang terbaru jika tersedia dan stabil
    init_url = f"https://graph.facebook.com/v23.0/{FB_PAGE_ID}/video_reels"
    init_params = {
        "upload_phase": "start",
        "access_token": FB_ACCESS_TOKEN
    }
    init_data = {
        "name": os.path.basename(video_path),
        "file_size": os.path.getsize(video_path)
    }

    try:
        logger.info("Starting Reels upload session...")
        init_response = requests.post(init_url, params=init_params, json=init_data)
        init_response.raise_for_status()
        init_data = init_response.json()
        
        video_id = init_data.get("video_id")
        upload_url = init_data.get("upload_url")
        
        if not video_id or not upload_url:
            logger.error(f"Failed to get video_id or upload_url from initialization: {init_data}")
            return False, None

        # Step 2: Upload video
        logger.info(f"Uploading video to: {upload_url}...")
        with open(video_path, 'rb') as video_file:
            upload_response = requests.post(upload_url, data=video_file, headers={'Content-Type': 'video/mp4'})
            upload_response.raise_for_status()
            upload_data = upload_response.json()

        if not upload_data.get("success"):
            logger.error(f"Failed to upload video: {upload_data}")
            return False, None

        # Step 3: Selesaikan upload dan publish Reels
        logger.info(f"Finishing upload and publishing Reels (ID: {video_id})...")
        finish_url = f"https://graph.facebook.com/v23.0/{FB_PAGE_ID}/video_reels"
        finish_params = {
            "upload_phase": "finish",
            "video_id": video_id,
            "description": description,
            "access_token": FB_ACCESS_TOKEN
        }
        
        finish_response = requests.post(finish_url, params=finish_params)
        finish_response.raise_for_status()
        finish_data = finish_response.json()

        if finish_data.get("success"):
            logger.info(f"Reels successfully posted with ID: {video_id}")
            return True, video_id
        else:
            logger.error(f"Failed to publish Reels: {finish_data}")
            return False, None

    except requests.exceptions.RequestException as e:
        logger.error(f"Facebook API or connection error: {e}", exc_info=True)
        if e.response is not None:
            logger.error(f"Error response from Facebook: {e.response.text}")
        return False, None
    except Exception as e:
        logger.error(f"General error during Reels upload: {e}", exc_info=True)
        return False, None

# Contoh penggunaan (tidak bisa langsung jalan tanpa token dan video)
if __name__ == "__main__":
    pass
