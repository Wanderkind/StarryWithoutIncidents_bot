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
        "👋 Hello! I track how many days have passed without an incident.\n\n"
        "✅ Use /status to check the current count.\n"
        "⚠️ Admins can use /reset to reset the counter.\n"
        "📅 Use /setdaily to schedule daily updates."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the number of days without an incident."""
    days = get_days_without_incident()
    await update.message.reply_text(f"📅 Days without an incident: **{days}**")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the chat."""
    chat = update.effective_chat
    user = update.effective_user
    bot = context.bot
    
    member = await bot.get_chat_member(chat.id, user.id)
    return member.status in {ChatMember.ADMINISTRATOR, ChatMember.CREATOR}

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset the incident counter (admin-only)."""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only an admin can reset the incident count.")
        return
    
    incident_data["last_reset"] = str(datetime.date.today())
    save_data(incident_data)
    await update.message.reply_text("🔴 Incident recorded. Counter reset to **0**.")

async def send_daily_status(context: CallbackContext):
    """Send a daily update message to the group."""
    chat_id = context.job.chat_id
    days = get_days_without_incident()
    await context.bot.send_message(chat_id=chat_id, text=f"📅 Days without an incident: **{days}**")

async def set_daily_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule the bot to send a daily update at 9:00 AM."""
    chat_id = update.message.chat_id
    job_queue = context.job_queue

    # Remove existing job for this chat (if any)
    existing_jobs = job_queue.get_jobs_by_name(str(chat_id))
    for job in existing_jobs:
        job.schedule_removal()

    # Schedule a new job
    job_queue.run_daily(
        send_daily_status, 
        time=datetime.time(hour=9, minute=0), 
        chat_id=chat_id, 
        name=str(chat_id)
    )

    await update.message.reply_text("✅ Daily updates scheduled at **9:00 AM**.")

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
    app.add_handler(CommandHandler("setdaily", set_daily_update))

    logging.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
