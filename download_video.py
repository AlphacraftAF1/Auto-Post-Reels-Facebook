# download_video.py
import yt_dlp
import os

def download_youtube_shorts(keyword, output_path="videos"):
    """
    Mencari dan mendownload video YouTube Shorts berdasarkan keyword.
    Mengembalikan path file video dan info video jika berhasil, None jika gagal.
    """
    # Pastikan direktori output ada
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Opsi untuk mencari video (tanpa download dulu)
    # Kita akan mencoba untuk mendapatkan URL dengan lebih pasti di sini
    search_ydl_opts = {
        'format': 'mp4',
        'paths': {'home': output_path},
        'noplaylist': True,
        'quiet': True,
        # 'extract_flat': 'in_playlist', # Menonaktifkan ini untuk mendapatkan info lebih lengkap termasuk URL
        'default_search': 'ytsearch10:', # Cari 10 hasil teratas
        'geo_bypass': True,
        'skip_download': True, # Hanya dapatkan info, jangan download
        'force_generic_extractor': True,
        'dump_single_json': True, # Mencetak metadata sebagai JSON
    }

    video_url = None
    video_info = None

    try:
        # Mencari video dan mendapatkan URL
        search_query = f"{keyword} shorts"
        print(f"Mencari YouTube Shorts dengan query: '{search_query}'")
        
        with yt_dlp.YoutubeDL(search_ydl_opts) as ydl:
            # Karena 'extract_flat' dinonaktifkan, ini akan mengunduh metadata lengkap
            # untuk setiap entri, yang akan mencakup 'webpage_url'
            search_results = ydl.extract_info(search_query, download=False)
            
            if 'entries' in search_results and search_results['entries']:
                print(f"Ditemukan {len(search_results['entries'])} hasil pencarian awal.")
                for entry in search_results['entries']:
                    if entry and entry.get('duration') is not None and entry.get('webpage_url'):
                        duration = entry['duration']
                        url = entry['webpage_url']
                        print(f"  - Video: {entry.get('title', 'N/A')}, Durasi: {duration}s, URL: {url}")
                        
                        # Filter durasi
                        if duration <= 65: # Toleransi durasi sedikit lebih tinggi
                            video_url = url
                            video_info = entry
                            print(f"  -> Memilih video ini sebagai Shorts yang cocok.")
                            break # Ambil video shorts pertama yang ditemukan yang memenuhi kriteria
                    else:
                        print(f"  - Melewati entri tanpa durasi, URL, atau tidak valid: {entry.get('title', 'N/A')}")

        if not video_url:
            print(f"Tidak ditemukan video shorts yang cocok (URL valid, durasi <=65s) untuk keyword: {keyword} setelah filtering.")
            return None, None

        # Opsi untuk mendownload video yang ditemukan
        download_ydl_opts = {
            'format': 'mp4',
            'paths': {'home': output_path},
            'outtmpl': {'default': '%(id)s.%(ext)s'}, # Nama file berdasarkan ID video
            'noplaylist': True,
            'quiet': True,
            'merge_output_format': 'mp4',
            'geo_bypass': True,
            'retries': 3, # Coba lagi jika download gagal
            'fragment_retries': 3,
        }
        
        print(f"Mulai mendownload video dari URL: {video_url}")
        with yt_dlp.YoutubeDL(download_ydl_opts) as ydl:
            # Mengunduh video menggunakan URL yang sudah didapat
            info_dict = ydl.extract_info(video_url, download=True)
            video_id = info_dict.get('id')
            video_ext = info_dict.get('ext', 'mp4')
            downloaded_file_path = os.path.join(output_path, f"{video_id}.{video_ext}")
            
            if os.path.exists(downloaded_file_path):
                print(f"Video berhasil didownload ke: {downloaded_file_path}")
                return downloaded_file_path, info_dict
            else:
                print(f"Gagal menemukan file setelah download untuk URL: {video_url}. Path yang diharapkan: {downloaded_file_path}")
                return None, None

    except yt_dlp.DownloadError as e:
        print(f"Error yt-dlp saat mendownload atau mencari video: {e}")
        return None, None
    except Exception as e:
        print(f"Error umum di download_youtube_shorts: {e}")
        return None, None

# Contoh penggunaan (bisa dihapus nanti)
if __name__ == "__main__":
    # Pastikan folder 'temp_videos' ada atau akan dibuat
    path, info = download_youtube_shorts("funny animals", "temp_videos")
    if path:
        print(f"Downloaded: {path}")
        print(f"Title: {info.get('title')}")
        print(f"Duration: {info.get('duration')}s")
        # os.remove(path) # Hapus setelah selesai tes
    else:
        print("Gagal mendownload video.")
