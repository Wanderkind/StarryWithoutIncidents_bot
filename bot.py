import os
import logging
import datetime
import json
from telegram import Update, ChatMember
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    ContextTypes
)

# Time at which report is sent daily (KST)
hr, mn = 8, 0

# Load bot token from environment variables (Railway uses this)
TOKEN = os.getenv("BOT_TOKEN")

# Set up logging (useful for debugging)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Load or initialize the incident data
DATA_FILE = "incident_data.json"

def load_data():
    """Load incident data from a file (or create a new record)."""
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_reset": str(datetime.date.today())}

def save_data(data):
    """Save incident data to a file."""
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)

incident_data = load_data()

def get_days_without_incident():
    """Calculate the number of days since the last recorded incident."""
    last_reset = datetime.date.fromisoformat(incident_data["last_reset"])
    today = datetime.date.today()
    return (today - last_reset).days

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the bot starts."""
    await update.message.reply_text(
        "👋 안녕하세요! 춤별혼의 무사고 운영을 기원하는 ☆춤별혼 무사고봇☆입니다.\n\n"
        f"📅 무사고 레포트는 매일 {hr:02d}시 {mn:02d}분에 자동으로 전송됩니다."
        "✅ 현재 무사고 일수를 확인하려면 /status를 입력하세요.\n"
        "⚠️ 사고 발생 시 관리자는 /reset를 입력해 카운터를 리셋할 수 있습니다.\n"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the number of days without an incident."""
    days = get_days_without_incident()
    await update.message.reply_text(f"✅ 춤별혼 무사고 [{days:03d}일차]")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the chat."""
    chat = update.effective_chat
    user = update.effective_user
    bot = context.bot
    
    member = await bot.get_chat_member(chat.id, user.id)
    return member.status in {ChatMember.ADMINISTRATOR, ChatMember.OWNER}

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset the incident counter (admin-only)."""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ 관리자만 카운터를 리셋할 수 있습니다.")
        return
    
    incident_data["last_reset"] = str(datetime.date.today())
    save_data(incident_data)
    await update.message.reply_text("🔴 사고가 발생했습니다. 현재 춤별혼 무사고 [000일차]입니다.")

async def send_daily_status(context: CallbackContext):
    """Send a daily update message to the group."""
    chat_id = context.job.chat_id
    days = get_days_without_incident()
    await context.bot.send_message(chat_id=chat_id, text=f"✅ 춤별혼 무사고 [{days:03d}일차]")

def main():
    """Run the bot."""
    if not TOKEN:
        logging.error("❌ BOT_TOKEN environment variable is missing!")
        return
    
    app = Application.builder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("reset", reset))

    logging.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
