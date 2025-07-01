# facebook_uploader.py
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
        logger.error(f"Video file not found for Reels upload: {video_path}")
        return False, None

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
            logger.error(f"Failed to get video_id or upload_url from Reels initialization: {init_data}")
            return False, None

        logger.info(f"Uploading video to Reels: {upload_url}...")
        with open(video_path, 'rb') as video_file:
            upload_response = requests.post(upload_url, data=video_file, headers={'Content-Type': 'video/mp4'})
            upload_response.raise_for_status()
            upload_data = upload_response.json()

        if not upload_data.get("success"):
            logger.error(f"Failed to upload video to Reels: {upload_data}")
            return False, None

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
        logger.error(f"Facebook API or connection error during Reels upload: {e}", exc_info=True)
        if e.response is not None:
            logger.error(f"Error response from Facebook: {e.response.text}")
        return False, None
    except Exception as e:
        logger.error(f"General error during Reels upload: {e}", exc_info=True)
        return False, None

def upload_regular_video(video_path, description):
    """
    Mengunggah video sebagai postingan video reguler ke Facebook Page.
    Mengembalikan True jika sukses, False jika gagal, beserta ID post jika sukses.
    """
    if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
        logger.error("FB_PAGE_ID or FB_ACCESS_TOKEN not set for regular video upload.")
        return False, None
    if not os.path.exists(video_path):
        logger.error(f"Video file not found for regular video upload: {video_path}")
        return False, None

    upload_url = f"https://graph.facebook.com/v23.0/{FB_PAGE_ID}/videos"
    params = {
        "description": description,
        "access_token": FB_ACCESS_TOKEN,
        "file_size": os.path.getsize(video_path) # opsional tapi baik untuk diberikan
    }

    try:
        logger.info(f"Uploading regular video: {video_path}...")
        with open(video_path, 'rb') as video_file:
            files = {'source': (os.path.basename(video_path), video_file, 'video/mp4')}
            response = requests.post(upload_url, params=params, files=files)
            response.raise_for_status()
            upload_data = response.json()

        if upload_data.get("id"):
            post_id = upload_data["id"]
            logger.info(f"Regular video successfully posted with ID: {post_id}")
            return True, post_id
        else:
            logger.error(f"Failed to post regular video: {upload_data}")
            return False, None

    except requests.exceptions.RequestException as e:
        logger.error(f"Facebook API or connection error during regular video upload: {e}", exc_info=True)
        if e.response is not None:
            logger.error(f"Error response from Facebook: {e.response.text}")
        return False, None
    except Exception as e:
        logger.error(f"General error during regular video upload: {e}", exc_info=True)
        return False, None


def upload_photo(photo_path, description):
    """
    Mengunggah foto sebagai postingan foto ke Facebook Page.
    Mengembalikan True jika sukses, False jika gagal, beserta ID post jika sukses.
    """
    if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
        logger.error("FB_PAGE_ID or FB_ACCESS_TOKEN not set for photo upload.")
        return False, None
    if not os.path.exists(photo_path):
        logger.error(f"Photo file not found for upload: {photo_path}")
        return False, None

    upload_url = f"https://graph.facebook.com/v23.0/{FB_PAGE_ID}/photos"
    params = {
        "caption": description,
        "access_token": FB_ACCESS_TOKEN,
    }

    try:
        logger.info(f"Uploading photo: {photo_path}...")
        with open(photo_path, 'rb') as photo_file:
            files = {'source': (os.path.basename(photo_path), photo_file, 'image/jpeg')} # Asumsi JPEG
            response = requests.post(upload_url, params=params, files=files)
            response.raise_for_status()
            upload_data = response.json()

        if upload_data.get("id"):
            post_id = upload_data["id"]
            logger.info(f"Photo successfully posted with ID: {post_id}")
            return True, post_id
        else:
            logger.error(f"Failed to post photo: {upload_data}")
            return False, None

    except requests.exceptions.RequestException as e:
        logger.error(f"Facebook API or connection error during photo upload: {e}", exc_info=True)
        if e.response is not None:
            logger.error(f"Error response from Facebook: {e.response.text}")
        return False, None
    except Exception as e:
        logger.error(f"General error during photo upload: {e}", exc_info=True)
        return False, None

# Contoh penggunaan (bisa dihapus nanti)
if __name__ == "__main__":
    pass
