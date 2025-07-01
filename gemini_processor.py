import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logger.error("GEMINI_API_KEY not set. Gemini features will be unavailable.")

def process_caption_with_gemini(raw_caption, media_type="media"):
    """
    Memproses caption menggunakan Gemini API:
    - Membersihkan link spam
    - Meningkatkan kualitas caption
    - Membuat caption baru jika kosong atau terlalu pendek
    - Menambahkan hashtag relevan
    """

    if not API_KEY:
        logger.warning("Gemini API key is missing. Skipping Gemini processing.")
        return f"{media_type.capitalize()} dari Telegram Bot"

    model = genai.GenerativeModel('gemini-1.5-flash')  # atau 'gemini-1.5-pro'

    # Prompt dinamis berdasarkan isi caption
    if raw_caption:
        input_caption_prompt = f"Teks asli dari pengguna: \"{raw_caption}\"\n"
    else:
        input_caption_prompt = f"Teks asli dari pengguna KOSONG. Harap buatkan caption baru yang menarik dan relevan untuk sebuah {media_type} ini, tanpa bertanya balik atau meminta informasi tambahan."

    prompt_parts = [
        "Anda adalah AI asisten untuk menulis caption media sosial yang menarik, lucu, dan cocok untuk Facebook Reels/Video/Foto.\n",
        "Tugas Anda:\n",
        "1. Hapus semua tautan promosi/spam.\n",
        "2. Gunakan bahasa Indonesia jika caption asli Indonesia.\n",
        "3. Jika caption sudah bagus, perbaiki & tambahkan hashtag relevan.\n",
        "4. Jika caption kosong atau terlalu pendek, buat caption baru dari awal.\n",
        "5. Jangan bertanya balik. Langsung beri hasil.\n",
        f"6. Tipe media: {media_type}\n",
        "--- Input Caption ---",
        input_caption_prompt,
        "--- Output Caption ---"
    ]

    try:
        logger.info(f"Sending prompt to Gemini for caption processing. Raw: '{raw_caption}'")
        response = model.generate_content(prompt_parts)
        cleaned_caption = response.text.strip()

        if not cleaned_caption:
            logger.warning("Gemini returned empty result. Using fallback.")
            return f"{media_type.capitalize()} dari Telegram Bot"

        logger.info(f"Gemini processed caption. Result: '{cleaned_caption}'")
        return cleaned_caption

    except Exception as e:
        logger.error(f"Gemini error: {e}", exc_info=True)
        return f"{media_type.capitalize()} dari Telegram Bot"

# Opsional: testing lokal
if __name__ == "__main__":
    print(process_caption_with_gemini("Anjing ini lucu banget!", media_type="video"))
