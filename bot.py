import os
import logging
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

# Simple integer counter for tracking days without an incident
incident_days = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the bot starts."""
    await update.message.reply_text(
        "👋 Hello! I track how many days have passed without an incident.\n\n"
        "✅ Use /status to check the current count.\n"
        "⚠️ Admins can use /reset to reset the counter.\n"
        "📅 Daily updates are sent automatically."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the number of days without an incident."""
    await update.message.reply_text(f"📅 Days without an incident: **{incident_days}**")

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is an admin in the chat."""
    chat = update.effective_chat
    user = update.effective_user
    bot = context.bot
    
    member = await bot.get_chat_member(chat.id, user.id)
    return member.status in {ChatMember.ADMINISTRATOR, ChatMember.OWNER}

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset the incident counter (admin-only)."""
    global incident_days

    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only an admin can reset the incident count.")
        return
    
    incident_days = 0
    await update.message.reply_text("🔴 Incident recorded. Counter reset to **0**.")

async def increment_counter(context: CallbackContext):
    """Increase the counter by 1 every day and send a daily message."""
    global incident_days
    incident_days += 1
    chat_id = context.job.chat_id
    await context.bot.send_message(chat_id=chat_id, text=f"📅 Days without an incident: **{incident_days}**")

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

    # Schedule the daily increment and message (default: 8:00 AM KST)
    app.job_queue.run_daily(
        increment_counter, 
        time=datetime.time(hour=23, minute=0),  # Change time as needed
        chat_id=chat_id,
        name=str(chat_id)
    )

    logging.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
