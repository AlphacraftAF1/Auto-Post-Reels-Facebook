# download_video.py
import yt_dlp
import os

def download_youtube_shorts(keyword, output_path="videos"):
    """
    Mencari dan mendownload video YouTube Shorts berdasarkan keyword.
    Mengembalikan path file video dan info video jika berhasil, None jika gagal.
    """
    ydl_opts = {
        'format': 'mp4',
        'paths': {'home': output_path},
        'noplaylist': True,
        'quiet': True, # Mengurangi output konsol yt-dlp
        'extract_flat': 'in_playlist', # Hanya ekstrak URL dari playlist, bukan download semua
        'skip_download': True, # Awalnya hanya cek info, download nanti
        'default_search': 'ytsearch10:', # Cari 10 hasil teratas
        'geo_bypass': True, # Bypass batasan geografis jika ada
    }

    video_url = None
    video_info = None

    try:
        # Mencari video dan mendapatkan URL
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch10:{keyword} short", download=False)
            if 'entries' in search_results and search_results['entries']:
                # Filter untuk mencari video yang kemungkinan besar adalah shorts (durasi pendek)
                for entry in search_results['entries']:
                    if entry and entry.get('duration') and entry['duration'] <= 60: # Shorts biasanya < 60 detik
                        video_url = entry.get('webpage_url')
                        video_info = entry
                        break # Ambil video shorts pertama yang ditemukan

        if not video_url:
            print(f"Tidak ditemukan video shorts yang cocok untuk keyword: {keyword}")
            return None, None

        # Download video yang ditemukan
        download_opts = {
            'format': 'mp4',
            'paths': {'home': output_path},
            'outtmpl': {'default': '%(id)s.%(ext)s'}, # Nama file berdasarkan ID video
            'noplaylist': True,
            'quiet': True,
            'merge_output_format': 'mp4',
            'geo_bypass': True,
        }
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            video_id = info_dict.get('id')
            video_ext = info_dict.get('ext', 'mp4') # Default ke mp4
            downloaded_file_path = os.path.join(output_path, f"{video_id}.{video_ext}")
            
            # Memastikan file ada setelah download
            if os.path.exists(downloaded_file_path):
                print(f"Video didownload: {downloaded_file_path}")
                return downloaded_file_path, info_dict
            else:
                print(f"Gagal menemukan file setelah download untuk URL: {video_url}")
                return None, None

    except yt_dlp.DownloadError as e:
        print(f"Error mendownload video: {e}")
        return None, None
    except Exception as e:
        print(f"Error umum di download_youtube_shorts: {e}")
        return None, None

# Contoh penggunaan (bisa dihapus nanti)
if __name__ == "__main__":
    path, info = download_youtube_shorts("funny animals", "temp_videos")
    if path:
        print(f"Downloaded: {path}")
        print(f"Title: {info.get('title')}")
        print(f"Duration: {info.get('duration')}s")
        # os.remove(path) # Hapus setelah selesai tes
