import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client['telegram_bot']
user_collection = db['users']

# Telegram bot token from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Add a new user to the MongoDB database
def add_user(user_id, username):
    user_collection.update_one(
        {'user_id': user_id},
        {'$set': {'user_id': user_id, 'username': username}},
        upsert=True
    )

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    add_user(user_id, username)
    await update.message.reply_text(f"Hello {username}, welcome to the bot!")

# Help command
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Use /start to start the bot!')

# Broadcast command (only for admin)
async def broadcast(update: Update, context: CallbackContext) -> None:
    # Ensure the user is the admin
    admin_id = os.getenv("ADMIN_ID")
    if str(update.message.from_user.id) == admin_id:
        message = ' '.join(context.args)  # Capture arguments passed to /broadcast
        if not message:
            await update.message.reply_text("Please provide a message to broadcast.")
            return

        users = user_collection.find()
        for user in users:
            await context.bot.send_message(chat_id=user['user_id'], text=message)
        await update.message.reply_text("Message broadcasted!")
    else:
        await update.message.reply_text("You are not authorized to broadcast.")

# Main function to handle bot and commands
async def main():
    # Create an Application object
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("broadcast", broadcast))

    # Start polling for updates from Telegram
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
