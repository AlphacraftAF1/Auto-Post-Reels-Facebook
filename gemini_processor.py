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

def process_caption_with_gemini(caption_text, media_type="video"):
    """
    Memproses teks caption menggunakan model Gemini untuk menambahkan emoji dan hashtag.
    """
    configure_gemini()
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""
    Anda adalah asisten AI yang membantu membuat caption media sosial yang menarik.
    Tugas Anda adalah:
    1. Perbaiki tata bahasa atau ejaan jika diperlukan.
    2. Tambahkan 1-3 emoji yang relevan di awal atau di tengah kalimat.
    3. Tambahkan 3-5 hashtag yang relevan dan populer di akhir caption.
    4. Pastikan caption tetap singkat, menarik, dan sesuai dengan konteks {media_type}.
    5. JANGAN tambahkan pengantar seperti "Berikut caption Anda:" atau sejenisnya. Langsung saja berikan caption yang sudah jadi.
    6. JANGAN mengulang caption asli secara keseluruhan jika tidak ada perubahan yang diperlukan selain penambahan emoji/hashtag.
    7. JANGAN menambahkan informasi yang tidak ada dalam caption asli.
    8. JANGAN menambahkan karakter aneh atau format yang tidak standar.

    Caption asli: "{caption_text}"

    Caption yang diperbaiki dengan emoji dan hashtag:
    """
    
    try:
        logger.info(f"Mengirim caption ke Gemini untuk diproses: '{caption_text}' (Tipe: {media_type})")
        response = model.generate_content(prompt)
        processed_text = response.text.strip()
        logger.info(f"Caption diproses oleh Gemini: '{processed_text}'")
        return processed_text
    except Exception as e:
        logger.error(f"Error saat memproses caption dengan Gemini: {e}", exc_info=True)
        # Fallback ke caption asli jika ada error
        return caption_text

if __name__ == "__main__":
    # Contoh penggunaan (pastikan GEMINI_API_KEY diset di environment)
    # os.environ["GEMINI_API_KEY"] = "YOUR_GEMINI_API_KEY"
    #
    # caption1 = "Ayamnya ga diprek, kecil, kering, masinya jg kering."
    # processed1 = process_caption_with_gemini(caption1, media_type="video")
    # print(f"Original: '{caption1}'\nProcessed: '{processed1}'\n")
    #
    # caption2 = "Ria ricis Dryzahay"
    # processed2 = process_caption_with_gemini(caption2, media_type="photo")
    # print(f"Original: '{caption2}'\nProcessed: '{processed2}'\n")
    #
    # caption3 = "RUTE BARU LRT JABODETABEK"
    # processed3 = process_caption_with_gemini(caption3, media_type="photo")
    # print(f"Original: '{caption3}'\nProcessed: '{processed3}'\n")
    #
    # caption4 = "super mario"
    # processed4 = process_caption_with_gemini(caption4, media_type="video")
    # print(f"Original: '{caption4}'\nProcessed: '{processed4}'\n")
    pass
