# gemini_processor.py
import os
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

# Konfigurasi Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logger.error("GEMINI_API_KEY not set. Gemini features will be unavailable.")

# --- PERUBAHAN DI SINI: Ubah dari async def menjadi def ---
def process_caption_with_gemini(raw_caption, media_type="media"):
    """
    Memproses caption menggunakan Gemini API:
    - Membersihkan tautan promosi/spam.
    - Menghasilkan caption baru jika kosong atau tidak relevan.
    - Menambahkan hashtag umum yang relevan.
    """
    if not API_KEY:
        logger.error("Gemini API key is missing. Skipping Gemini processing and using default caption.")
        return f"{media_type.capitalize()} dari Telegram Bot"

    # Model Gemini Flash
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt_parts = [
        "Anda adalah AI asisten untuk menulis caption media sosial yang menarik, lucu, dan cocok untuk Facebook Reels/Video/Foto.\n",
        "Tugas Anda adalah: \n",
        "1.  Periksa teks yang saya berikan. Jika ada tautan promosi (misal: 'ruangtopup.com', 'linkbio', 'beli sekarang', dll.) atau kata-kata spam, HAPUS SEMUA bagian tersebut. Jangan tinggalkan tautan atau promosi apapun.\n",
        "2.  Jika teks setelah dibersihkan menjadi kosong, terlalu pendek, atau terlalu generik, buatkan caption baru yang menarik dan orisinal.\n",
        "3.  Caption harus singkat, menarik perhatian, dan tidak kaku (robotik).\n",
        "4.  Sertakan 3-5 hashtag umum yang relevan (misal: #lucu #viral #foryou #videolucu #hiburan #memes #fotokeren) sesuai dengan konteks media, jika tidak ada hashtag dalam teks asli atau terlalu sedikit.\n",
        f"5.  Tipe media ini adalah: {media_type}.\n",
        "--- Contoh Teks Asli ---",
        "yang terakhir kingg🔥🔥",
        "--- Contoh Output ---",
        "Tingkahnya bikin ngakak! 😂 #lucu #viral #foryou",
        "--- Contoh Teks Asli ---",
        "- Topup Diamond ML , Free Fire , Credit PUBG dan game lainnya? cobain aja di ruangtopup.com",
        "--- Contoh Output ---",
        "Momen tak terduga yang bikin senyum! ✨ #hiburan #lucu #videolucu",
        "--- Contoh Teks Asli ---",
        "Ini adalah video keren.",
        "--- Contoh Output ---",
        "Ada-ada saja! 🤣 #viral #shorts #hiburan",
        "--- Teks Asli Sekarang ---",
        raw_caption if raw_caption else "Tidak ada caption. Buatkan yang baru.",
        "\n--- Output yang Dihasilkan ---"
    ]

    try:
        logger.info(f"Sending prompt to Gemini for caption processing. Raw: '{raw_caption}'")
        # --- PERUBAHAN DI SINI: Hapus 'await' ---
        response = model.generate_content(prompt_parts)
        # --- AKHIR PERUBAHAN ---
        
        cleaned_and_generated_caption = response.text.strip()
        
        # Validasi respons dasar dari Gemini (misal, tidak kosong)
        if not cleaned_and_generated_caption:
            logger.warning("Gemini returned an empty caption. Using fallback default.")
            return f"{media_type.capitalize()} dari Telegram Bot"

        logger.info(f"Gemini processed caption. Original: '{raw_caption}', Processed: '{cleaned_and_generated_caption}'")
        return cleaned_and_generated_caption

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}. Using fallback default.", exc_info=True)
        return f"{media_type.capitalize()} dari Telegram Bot"

# --- PERUBAHAN DI SINI: Sesuaikan bagian if __name__ == "__main__": agar konsisten ---
if __name__ == "__main__":
    # Ini hanya untuk pengujian lokal. Pastikan GEMINI_API_KEY diatur di ENV VARS
    # os.environ["GEMINI_API_KEY"] = "YOUR_GEMINI_API_KEY"
    
    # Contoh penggunaan
    def test_gemini_sync(): # Ubah ke def karena fungsinya sudah synchronous
        # Setup basic logging for local test
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        caption1 = "- Topup Diamond ML , Free Fire , Credit PUBG dan game lainnya? cobain aja di ruangtopup.com"
        result1 = process_caption_with_gemini(caption1, "video")
        print(f"Test 1 - Original: '{caption1}'\nResult: '{result1}'\n")

        caption2 = None
        result2 = process_caption_with_gemini(caption2, "foto")
        print(f"Test 2 - Original: '{caption2}'\nResult: '{result2}'\n")

        caption3 = "Ini adalah momen kocak anjing yang mencoba menangkap ekornya! 🐶"
        result3 = process_caption_with_gemini(caption3, "video")
        print(f"Test 3 - Original: '{caption3}'\nResult: '{result3}'\n")
    
    test_gemini_sync() # Panggil fungsi synchronous
# --- AKHIR PERUBAHAN ---
