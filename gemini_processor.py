import google.generativeai as genai
import random
import logging
import os

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Daftar caption fallback lucu
FALLBACK_CAPTIONS = [
    "Ketika ide muncul di kepala, tapi eksekusinya butuh kopi. ☕",
    "Hidup itu seperti Reels, kadang cepat, kadang lambat, tapi selalu ada momennya. ✨",
    "Melihat ini, saya jadi ingin rebahan sambil ngemil. Ada yang sama? 😴",
    "Ini bukan sekadar postingan, ini adalah seni. Atau mungkin cuma gabut. 🤔",
    "Terkadang, yang kita butuhkan hanyalah senyuman dan koneksi internet yang stabil. 😊",
    "Reels ini dipersembahkan oleh tim rebahan profesional. Selamat menikmati! 🛋️",
    "Jangan lupa bahagia, karena hidup ini terlalu singkat untuk tidak tertawa. 😂",
    "Mungkin ini tanda untuk istirahat sejenak dan menikmati hal-hal kecil. 🍃",
    "Kalau ada yang bilang ini tidak penting, berarti mereka belum tahu seni menikmati hidup. 😉",
    "Selamat datang di dunia absurditas yang menyenangkan. Siap-siap terhibur! 🥳"
]

def process_caption(original_caption, gemini_api_key):
    """
    Memproses caption menggunakan Gemini API untuk membersihkan dan membuatnya menarik.
    Jika caption kosong atau generik, gunakan fallback caption.
    """
    if not gemini_api_key:
        logging.warning("Kunci API Gemini tidak ditemukan. Menggunakan caption asli atau fallback.")
        if not original_caption or original_caption.strip() == "":
            return random.choice(FALLBACK_CAPTIONS)
        return original_caption

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Cek apakah caption kosong atau generik (misalnya, hanya spasi)
    if not original_caption or original_caption.strip() == "":
        logging.info("Caption asli kosong atau generik. Menggunakan fallback caption.")
        return random.choice(FALLBACK_CAPTIONS)

    # Prompt untuk Gemini API
    # Menambahkan instruksi eksplisit untuk tagar Reels/Shorts
    prompt = (
        f"Saya memiliki caption berikut dari sebuah video atau foto yang akan diposting ke Facebook Reels:\n\n"
        f"'{original_caption}'\n\n"
        f"Tolong bersihkan caption ini dari informasi yang tidak relevan (seperti ID internal, URL yang tidak perlu, atau teks sistem), "
        f"dan buatlah lebih menarik, lucu, atau relevan untuk audiens Facebook Reels. "
        f"Tambahkan emoji yang sesuai. Untuk video, sertakan tagar seperti #Reels, #Shorts, #VideoPendek, atau #KontenLucu. "
        f"Pastikan caption tidak terlalu panjang (maksimal 200 karakter). "
        f"Jika caption sudah bagus, cukup sempurnakan sedikit. "
        f"Berikan hanya caption yang sudah diproses, tanpa tambahan teks atau penjelasan."
    )

    try:
        logging.info("Mengirim caption ke Gemini API untuk diproses...")
        response = model.generate_content(prompt)
        processed_text = response.text.strip()

        # Batasi panjang caption yang diproses
        if len(processed_text) > 200:
            processed_text = processed_text[:197] + "..." # Potong dan tambahkan elipsis

        logging.info(f"Caption dari Gemini: {processed_text}")
        return processed_text
    except Exception as e:
        logging.error(f"Gagal memproses caption dengan Gemini API: {e}. Menggunakan caption asli atau fallback.", exc_info=True)
        if not original_caption or original_caption.strip() == "":
            return random.choice(FALLBACK_CAPTIONS)
        return original_caption

if __name__ == '__main__':
    # Contoh penggunaan (untuk pengujian lokal)
    TEST_GEMINI_API_KEY = os.getenv('GEMINI_API_KEY_TEST', 'YOUR_GEMINI_API_KEY_HERE') # Ganti dengan kunci API Anda
    
    if TEST_GEMINI_API_KEY == 'YOUR_GEMINI_API_KEY_HERE':
        logging.warning("Variabel lingkungan GEMINI_API_KEY_TEST tidak diatur. Tidak dapat menjalankan contoh Gemini Processor.")
    else:
        logging.info("Menjalankan contoh gemini_processor.py...")
        
        # Contoh caption kosong
        caption1 = ""
        print(f"Caption asli: '{caption1}' -> Diproses: '{process_caption(caption1, TEST_GEMINI_API_KEY)}'")

        # Contoh caption generik
        caption2 = "Photo dari Telegram"
        print(f"Caption asli: '{caption2}' -> Diproses: '{process_caption(caption2, TEST_GEMINI_API_KEY)}'")

        # Contoh caption dengan teks
        caption3 = "Video lucu kucing main bola. #kucing #lucu #gemoy"
        print(f"Caption asli: '{caption3}' -> Diproses: '{process_caption(caption3, TEST_GEMINI_API_KEY)}'")

        # Contoh caption yang terlalu panjang
        long_caption = "Ini adalah caption yang sangat panjang sekali, lebih dari dua ratus karakter, yang dibuat hanya untuk menguji apakah fungsi pemrosesan caption akan memotongnya dengan benar dan menambahkan elipsis di bagian akhir. Semoga ini bekerja dengan baik dan tidak menimbulkan masalah. Kita akan lihat bagaimana hasilnya nanti."
        print(f"Caption asli: '{long_caption}' -> Diproses: '{process_caption(long_caption, TEST_GEMINI_API_KEY)}'")
