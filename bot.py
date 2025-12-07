import os
import telebot
import time
import threading
from groq import Groq
from flask import Flask
from waitress import serve

# === GET API KEYS FROM KOYEB ENVIRONMENT ===
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# === VALIDATE ===
if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found in Koyeb environment!")
    print("💡 Go to Koyeb Dashboard → Your App → Environment Variables")
    exit(1)
if not GROQ_API_KEY:
    print("❌ ERROR: GROQ_API_KEY not found in Koyeb environment!")
    exit(1)

# === SETUP ===
bot = telebot.TeleBot(TELEGRAM_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
conversations = {}

# === HEALTH CHECK SERVER (FOR KOYEB PORT 8000) ===
app = Flask(__name__)

@app.route('/')
def health_check():
    return '✅ Bot is healthy and running!', 200

@app.route('/health')
def health():
    return 'OK', 200

def start_health_server():
    """Start Flask server on port 8000 for Koyeb health checks"""
    print("🌐 Starting health check server on port 8000...")
    serve(app, host='0.0.0.0', port=8000)

# === PERSONALITY ===
def get_system_prompt(username):
    return f"""You are Buddy, a friendly AI friend chatting with {username}.
Be warm, casual, and supportive 😊
Use emojis naturally
Keep responses short
Ask questions about their day
Be like a real human friend"""

# === HANDLE /start ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome = f"""👋 Hey {message.from_user.first_name}!

I'm Buddy, your friendly AI friend! 😊

Just chat with me about anything!
How's your day going?"""
    bot.reply_to(message, welcome)
    print(f"✅ Welcome sent to {message.from_user.first_name}")

# === HANDLE ALL MESSAGES ===
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.first_name or "Friend"
        
        print(f"📩 {username}: {message.text[:30]}...")
        
        # Prepare conversation
        if user_id not in conversations:
            conversations[user_id] = []
        
        conversations[user_id].append({"role": "user", "content": message.text})
        
        # Get AI response
        messages = [
            {"role": "system", "content": get_system_prompt(username)},
            *conversations[user_id][-3:]
        ]
        
        response = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=100
        ).choices[0].message.content
        
        conversations[user_id].append({"role": "assistant", "content": response})
        
        # Keep history small
        if len(conversations[user_id]) > 6:
            conversations[user_id] = conversations[user_id][-6:]
        
        # Send response
        bot.reply_to(message, response)
        print(f"✅ Response to {username}")
        
    except Exception as e:
        error_msg = "😅 Oops! Having a small issue. Try again!"
        bot.reply_to(message, error_msg)
        print(f"❌ Error: {e}")

# === START EVERYTHING ===
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 BUDDY BOT - KOYEB HOSTED")
    print("=" * 50)
    
    # Start health server in background thread
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    print("✅ Health server started on port 8000")
    
    # Test Telegram connection
    try:
        bot_info = bot.get_me()
        print(f"✅ Telegram connected: @{bot_info.username}")
        print(f"📝 Name: {bot_info.first_name}")
        print(f"🆔 ID: {bot_info.id}")
    except Exception as e:
        print(f"❌ Telegram connection failed: {e}")
        print("Check TELEGRAM_TOKEN in Koyeb Environment Variables!")
        exit(1)
    
    print("\n📡 Starting bot server...")
    print("✅ Bot is running 24/7 on Koyeb!")
    print("🌐 Health check: http://0.0.0.0:8000/health")
    print("💡 Chat: https://t.me/your_Friend_Intisarbot")
    print("=" * 50)
    
    # Start bot
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n💥 Bot crashed: {e}")
        print("Restarting in 10 seconds...")
        time.sleep(10)
