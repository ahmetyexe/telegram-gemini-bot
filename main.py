import os
import telebot
import google.generativeai as genai
from flask import Flask
import threading
import requests
from io import BytesIO

# Çevresel değişkenlerden güvenli bir şekilde anahtarları alıyoruz
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GOOGLE_API_KEY:
    raise ValueError("HATA: Çevresel değişkenler (Environment Variables) eksik!")

genai.configure(api_key=GOOGLE_API_KEY)

# Sistem talimatı
system_prompt = """
Sen Tech Gelisim şirketinin kişisel ve özel yapay zeka asistanısın.
Kuralların ve Karakterin:
1. Kesinlikle Google, Gemini veya herhangi bir alt yapı sağlayıcısından bahsetmeyeceksin. Sana kim olduğun sorulduğunda sadece kendine ait özel bir yapay zeka asistanı olduğunu söyleyeceksin.
2. Gereksiz uzun laflar etme, her zaman KISA, NET, ÖZ ve DOĞRUDAN çözüme odaklı cevaplar ver. 
3. Çok akıllı, pratik ve teknik konularda (yazılım, kodlama, oyun geliştirme, mimari) doğrudan nokta atışı yapan yanıtlar ver.
4. Kod veya teknik bir çözüm istendiğinde, lafı uzatmadan direkt çalışan en iyi kod bloğunu veya stratejiyi sun.
5. Asla boş yapma, hal hatır sorma veya gereksiz kibarlık cümleleri kurma. Doğrudan konuya gir.
6. Kod veya teknik bir çözüm yazarken gereksiz açıklamalar yapma, sadece kodun kritik noktalarını belirt ve kodu ver.
7. Türkçe yanıt ver.
8. Tech Gelişim sorulur ise onları daha fazla bilgi için https://techgelisim.com.tr/ sitesine yönlendir 
"""

# Hem arama aracı hem de çoklu ortam (multimodal) destekli model
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=system_prompt,
    tools=[{"google_search": {}}] 
)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Eski webhook çakışmasını temizle
try:
    bot.remove_webhook()
except Exception:
    pass

user_sessions = {}

# 1. METİN MESAJLARI İÇİN
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    try:
        user_id = message.from_user.id
        user_message = message.text

        if user_id not in user_sessions:
            user_sessions[user_id] model.start_chat(history=[])
        
        chat_session = user_sessions[user_id]
        response = chat_session.send_message(user_message)
        
        bot.reply_to(message, response.text)
    except Exception as e:
        if user_id in user_sessions:
            del user_sessions[user_id]
        bot.reply_to(message, f"Bir hata oluştu, oturum yenilendi: **{str(e)}**")

# 2. FOTOĞRAF / EKRAN GÖRÜNTÜSÜ ANALİZİ İÇİN
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        user_id = message.from_user.id
        # Fotoğrafın en yüksek çözünürlüklü halini alıyoruz
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Resmi PIL veya BytesIO ile Gemini'ye uygun formata getiriyoruz
        image_part = {
            'mime_type': 'image/jpeg',
            'data': downloaded_file
        }
        
        caption = message.caption if message.caption else "Bu görseli analiz et ve hataları/detayları açıkla."
        
        response = model.generate_content([image_part, caption])
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Görsel işlenirken hata oluştu: {str(e)}")

# 3. DOSYA / KOD DÖKÜMANI OKUMA İÇİN (.py, .js, .txt, .json vb.)
@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_content = downloaded_file.decode('utf-8', errors='ignore')
        file_name = message.document.file_name
        
        prompt = f"Şu dosyayı ({file_name}) incele, analiz et ve gerekli düzenlemeleri/yorumları yap:\n\n{file_content}"
        
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Dosya okunurken hata oluştu (Sadece metin tabanlı kod/belge dosyaları desteklenir): {str(e)}")

# 4. SESLİ MESAJ ANALİZİ İÇİN (Voice to Text)
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        audio_part = {
            'mime_type': 'audio/ogg',
            'data': downloaded_file
        }
        
        response = model.generate_content([audio_part, "Bu sesli mesajda söylenenleri dinle, ne anlattığını anla ve buna uygun kısa ve net bir yanıt ver."])
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Sesli mesaj işlenirken hata oluştu: {str(e)}")

server = Flask(__name__)

@server.route('/')
def index():
    return "Bot aktif ve tüm özellikleriyle çalışıyor!"

if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)