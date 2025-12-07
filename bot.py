import os
import telebot
from groq import Groq

# Get keys
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# Setup
bot = telebot.TeleBot(TELEGRAM_TOKEN)
groq = Groq(api_key=GROQ_API_KEY)

# Handle /start
@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    bot.reply_to(message, f"👋 Hey {message.from_user.first_name}! I'm Buddy! 😊")

# Handle all messages
@bot.message_handler(func=lambda m: True)
def reply(message):
    try:
        # Simple AI response
        chat = groq.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"Be a friendly friend named Buddy. Reply to: {message.text}"
            }],
            model="llama-3.3-70b-versatile",
            max_tokens=50
        )
        
        response = chat.choices[0].message.content
        bot.reply_to(message, response)
        
        print(f"✅ Replied to {message.from_user.first_name}")
        
    except Exception as e:
        bot.reply_to(message, "😅 One sec...")
        print(f"Error: {e}")

# Start bot
print("🤖 Bot starting...")
bot.infinity_polling()
