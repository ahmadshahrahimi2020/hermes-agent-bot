import os
import sys
import logging
import asyncio
import urllib.request
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
ALLOWED_USER = int(os.getenv("TELEGRAM_ALLOWED_USERS", "1015253171"))

# In-memory conversation history per chat
chat_history = {}

def call_gemini(user_id, prompt):
    history = chat_history.setdefault(user_id, [])
    history.append({"role": "user", "parts": [{"text": prompt}]})
    # Keep last 15 turns
    if len(history) > 15:
        history = history[-15:]
        chat_history[user_id] = history

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": history,
        "systemInstruction": {
            "parts": [{
                "text": "تو هوش مصنوعی هرمس (Hermes Agent) هستی، دستیار هوشمند و اختصاصی احمد رحیمی. پاسخ‌هایت را به زبان فارسی، بسیار هوشمندانه، دقیق، محترمانه و صمیمی بده. در هر زمینه‌ای از برنامه‌نویسی تا پاسخ به سوالات به او کمک کن."
            }]
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            reply = data['candidates'][0]['content']['parts'][0]['text']
            history.append({"role": "model", "parts": [{"text": reply}]})
            return reply
    except Exception as e:
        return f"خطا در ارتباط با هوش مصنوعی: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER:
        await update.message.reply_text("⛔ دسترسی به این ربات اختصاصی محدود به مالک آن است.")
        return
    await update.message.reply_text("سلام احمد عزیز! 🚀\nمن هوش مصنوعی هرمس هستم که روی فضای ابری مستقر شده‌ام و ۲۴ ساعته آنلاین و آماده خدمت به شما هستم. هر سوال یا کاری داری بفرما!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER:
        return
    
    user_text = update.message.text
    if not user_text:
        return
    
    # Send typing status
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    loop = asyncio.get_running_loop()
    reply = await loop.run_in_executor(None, call_gemini, update.effective_user.id, user_text)
    
    await update.message.reply_text(reply)

if __name__ == '__main__':
    print("Hermes Cloud Bot Starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
