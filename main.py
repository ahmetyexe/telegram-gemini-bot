import os
import telebot
import google.generativeai as genai
from flask import Flask

# Bulut sunucusunun verdiği çevresel değişkenlerden token ve API key'i alıyoruz
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
# En güncel ve akıllı model
model = genai.GenerativeModel('gemini-2.5-flash')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
server = Flask(__name__)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_message = message.text
        response = model.generate_content(user_message)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Bir hata oluştu: {str(e)}")

# Render bulut sunucusunun botu ayakta tutması için gereken basit web kontrolü
@server.route('/')
def index():
    return "Bot aktif ve çalışıyor!"

if __name__ == "__main__":
    import threading
    # Botu arka planda çalıştır
    threading.Thread(target=bot.infinity_polling).start()
    # Sunucuyu port üzerinden ayağa kaldır
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)