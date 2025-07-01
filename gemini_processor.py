# gemini_processor.py
import os
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

def configure_gemini():
    """Mengkonfigurasi Gemini API dengan kunci dari environment variable."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY tidak ditemukan di environment variables.")
        raise ValueError("GEMINI_API_KEY is not set.")
    genai.configure(api_key=api_key)
    logger.info("Gemini API dikonfigurasi.")

def process_caption_with_gemini(raw_caption, media_type="media"):
    """
    Memproses teks caption menggunakan model Gemini untuk menambahkan emoji dan hashtag.
    """
    try:
        configure_gemini()
    except ValueError:
        logger.error("Gemini API key is missing. Skipping Gemini processing and using fallback default.")
        return raw_caption if raw_caption else f"{media_type.capitalize()} dari Telegram Bot"


    # --- PERUBAHAN DI SINI: Ubah model menjadi 'gemini-2.0-flash' ---
    model = genai.GenerativeModel('gemini-2.0-flash')
    # --- AKHIR PERUBAHAN ---

    # Tentukan bagian prompt untuk caption input
    input_caption_prompt = ""
    if raw_caption:
        input_caption_prompt = f"Teks asli dari pengguna: \"{raw_caption}\"\n"
    else:
        input_caption_prompt = f"Teks asli dari pengguna KOSONG. Harap buatkan caption baru yang menarik dan relevan untuk sebuah {media_type} ini, tanpa bertanya balik atau meminta informasi tambahan."


    prompt_parts = [
        "Anda adalah AI asisten untuk menulis caption media sosial yang menarik, lucu, dan cocok untuk Facebook Reels/Video/Foto.\n",
        "Tugas Anda adalah: \n",
        "1.  Periksa teks yang saya berikan. Jika ada tautan promosi (misal: 'ruangtopup.com', 'linkbio', 'beli sekarang', dll.) atau kata-kata spam, HAPUS SEMUA bagian tersebut. Jangan tinggalkan tautan atau promosi apapun.\n",
        "2.  PRIORITASKAN bahasa Indonesia. Jika teks asli dalam bahasa Indonesia, lanjutkan dalam bahasa Indonesia. Jika teks asli dalam bahasa Inggris, jawablah dalam bahasa Inggris. Jangan campur bahasa.\n",
        "3.  Jika teks setelah dibersihkan masih valid dan cukup informatif, cukup TINGKATKAN kualitasnya (misal: buat lebih menarik, lucu) dan tambahkan 3-5 hashtag umum yang relevan (misal: #lucu #viral #foryou #videokocak #hiburan #memes #fotokeren) sesuai dengan konteks media. Jangan membuat caption baru yang radikal jika yang asli sudah oke.\n",
        "4.  Jika teks setelah dibersihkan menjadi sangat kosong, terlalu pendek (kurang dari 5 karakter), atau terlalu generik, barulah buatkan caption baru yang orisinal, menarik, dan sesuai dengan tipe media (video/foto). Jangan bertanya balik.\n",
        "5.  Caption harus singkat, menarik perhatian, dan tidak kaku (robotik).\n",
        f"6.  Tipe media ini adalah: {media_type}.\n",
        "--- Contoh 1 ---",
        "Teks Asli: yang terakhir kingg🔥🔥",
        "Output: Tingkahnya bikin ngakak! 😂 #lucu #viral #foryou #videokocak",
        "--- Contoh 2 ---",
        "Teks Asli: - Topup Diamond ML , Free Fire , Credit PUBG dan game lainnya? cobain aja di ruangtopup.com",
        "Output: Momen tak terduga yang bikin senyum! ✨ #hiburan #lucu #videolucu #random",
        "--- Contoh 3 ---",
        "Teks Asli: Ini adalah video keren.",
        "Output: Ada-ada saja! 🤣 #viral #shorts #hiburan #videolucu",
        "--- Contoh 4 ---",
        "Teks Asli: anjing ini lucu sekali",
        "Output: Gemasnya anjing ini! 😍 #anjinglucu #binatanggemas #videokocak #fyp",
        "--- Contoh 5 ---",
        "Teks Asli: (kosong)",
        "Output: Momen seru yang bikin harimu lebih berwarna! ✨ #hiburan #seru #dailyvlog #kocak #fyp",
        "--- Teks Asli Sekarang ---",
        input_caption_prompt,
        "\n--- Output yang Dihasilkan ---"
    ]
    
    try:
        logger.info(f"Mengirim caption ke Gemini untuk diproses: '{raw_caption}' (Tipe: {media_type})")
        response = model.generate_content(prompt_parts)
        
        processed_text = response.text.strip()
        
        if not processed_text:
            logger.warning("Gemini returned an empty caption. Using fallback default.")
            return raw_caption if raw_caption else f"{media_type.capitalize()} dari Telegram Bot"

        logger.info(f"Caption diproses oleh Gemini. Asli: '{raw_caption}', Diproses: '{processed_text}'")
        return processed_text

    except Exception as e:
        logger.error(f"Error saat memproses caption dengan Gemini: {e}. Menggunakan fallback default.", exc_info=True)
        return raw_caption if raw_caption else f"{media_type.capitalize()} dari Telegram Bot"

if __name__ == "__main__":
    pass
