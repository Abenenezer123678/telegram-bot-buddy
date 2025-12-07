import os
import telebot
import time
import threading
import socket
from groq import Groq

# === GET API KEYS ===
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# === VALIDATE ===
if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    exit(1)
if not GROQ_API_KEY:
    print("❌ ERROR: GROQ_API_KEY not found!")
    exit(1)

# === SIMPLE HEALTH SERVER (for Koyeb port 8000) ===
def health_server():
    """Super simple TCP server that just says OK"""
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 8000))
        server.listen(5)
        print("✅ Health server started on port 8000")
        
        while True:
            client, addr = server.accept()
            # Send minimal HTTP response
            response = b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK'
            client.send(response)
            client.close()
    except Exception as e:
        print(f"⚠️ Health server error: {e}")

# === START HEALTH SERVER IN BACKGROUND ===
health_thread = threading.Thread(target=health_server, daemon=True)
health_thread.start()

# === SETUP BOT ===
bot = telebot.TeleBot(TELEGRAM_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
conversations = {}

# === PERSONALITY ===
def get_system_prompt(username):
    return f"""You are Buddy, a friendly AI friend chatting with {username}.
Be warm and friendly 😊
Use emojis sometimes
Keep responses short
Ask about their day"""

# === HANDLE /start ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome = f"""👋 Hey {message.from_user.first_name}!
    
I'm Buddy, your friendly AI friend! 😊
    
How's your day going?"""
    bot.reply_to(message, welcome)
    print(f"✅ Welcome to {message.from_user.first_name}")

# === HANDLE MESSAGES ===
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.first_name or "Friend"
        
        print(f"📩 {username}: {message.text[:20]}...")
        
        # Simple conversation
        if user_id not in conversations:
            conversations[user_id] = []
        
        # Prepare messages
        messages = [
            {"role": "system", "content": get_system_prompt(username)},
            {"role": "user", "content": message.text}
        ]
        
        # Get response
        response = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=80
        ).choices[0].message.content
        
        # Send
        bot.reply_to(message, response)
        print(f"✅ Response to {username}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        bot.reply_to(message, "😅 One moment...")

# === START ===
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 BUDDY BOT - SIMPLE VERSION")
    print("=" * 50)
    
    # Test connection
    try:
        bot_info = bot.get_me()
        print(f"✅ Connected: @{bot_info.username}")
        print(f"📝 Name: {bot_info.first_name}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        exit(1)
    
    print("\n📡 Bot is running!")
    print("💡 Chat: https://t.me/your_Friend_Intisarbot")
    print("=" * 50)
    
    # Start bot
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
