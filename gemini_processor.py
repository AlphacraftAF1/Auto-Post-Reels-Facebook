# gemini_processor.py
import os
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logger.error("GEMINI_API_KEY not set. Gemini features will be unavailable.")

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

    model = genai.GenerativeModel('gemini-2.0-flash')

    # --- PERUBAHAN DI SINI: PROMPT YANG LEBIH BAIK UNTUK CAPTION KOSONG ---
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
        input_caption_prompt, # <-- Gunakan variabel baru ini
        "\n--- Output yang Dihasilkan ---"
    ]
    # --- AKHIR PERUBAHAN PROMPT ---

    try:
        logger.info(f"Sending prompt to Gemini for caption processing. Raw: '{raw_caption}'")
        response = model.generate_content(prompt_parts)
        
        cleaned_and_generated_caption = response.text.strip()
        
        if not cleaned_and_generated_caption:
            logger.warning("Gemini returned an empty caption. Using fallback default.")
            return f"{media_type.capitalize()} dari Telegram Bot"

        logger.info(f"Gemini processed caption. Original: '{raw_caption}', Processed: '{cleaned_and_generated_caption}'")
        return cleaned_and_generated_caption

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}. Using fallback default.", exc_info=True)
        return f"{media_type.capitalize()} dari Telegram Bot"

# Bagian if __name__ == "__main__": tetap sama
if __name__ == "__main__":
    pass
