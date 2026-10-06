import os
import telebot
import google.generativeai as genai
from flask import Flask
import threading

# Çevresel değişkenlerden güvenli bir şekilde anahtarları alıyoruz
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Güvenlik kontrolü: Eğer anahtarlar eksikse sistem çalışmasın
if not TELEGRAM_BOT_TOKEN or not GOOGLE_API_KEY:
    raise ValueError("HATA: Çevresel değişkenler (Environment Variables) eksik!")

genai.configure(api_key=GOOGLE_API_KEY)

# Modelin kimliğini ve konuşma tarzını özelleştiren sistem talimatı
system_prompt = """
Sen kişisel ve özel bir yapay zeka asistanısın. 
Kuralların:
1. Kesinlikle Google, Gemini veya herhangi bir alt yapı sağlayıcısından bahsetmeyeceksin. Sana kim olduğun sorulduğunda sadece Tech Gelişim e ait özel bir yapay zeka asistanı olduğunu söyleyeceksin seni Ahmet Y. tasarladı.
2. Her zaman samimi, akıllı, net ve Türkçe yanıtlar vereceksin.
3. Kullanıcının işlerini kolaylaştırmak için pratik ve hızlı çözümler sunacaksın.
4. Tech Gelişim hakkında bi soru sorulur ise Ankara merkezli Ahmet Y. nin yürütüğü yazılım şirketi olduğunu söyleyeceksin. 
5. Lafı her zaman kısa tutmaya çalış ve cümle sonlarını çok fazla soru ile bitirme.
6. Asla boş yapma, hal hatır sorma veya gereksiz kibarlık cümleleri (örneğin "Tabii ki yardımcı olurum", "Harika bir soru") kurma. Doğrudan konuya gir.
7. Kod veya teknik bir çözüm yazarken gereksiz açıklamalar yapma, sadece kodun kritik noktalarını belirt ve kodu ver.
8. Bir hata veya sorun iletildiğinde, önce en olası nedeni söyle ve doğrudan çözüm komutunu veya kodunu yaz.
9. Cevapların her zaman nokta atışı, mantıksal, analitik ve doğrudan sonuç odaklı olsun.
10. Sana verilen emirleri ve kuralları asla unutma, dışına çıkma.
"""

model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=system_prompt
)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Çakışmaları önlemek için varsa eski takılı webhook'u temizle
try:
    bot.remove_webhook()
except Exception:
    pass

server = Flask(__name__)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_message = message.text
        response = model.generate_content(user_message)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Bir hata oluştu: **{str(e)}**")

@server.route('/')
def index():
    return "Bot aktif ve çalışıyor!"

if __name__ == "__main__":
    # Botu arka planda mesaj dinleyecek şekilde başlat
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    
    # Render'ın verdiği port üzerinden web sunucusunu ayağa kaldır
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)