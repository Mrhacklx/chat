import logging
import os
import socket
import threading
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client['telegram_bot']
user_collection = db['users']
api_collection = db['api_id']

# MongoDB Indexes
user_collection.create_index([('user_id', 1)], unique=True)
api_collection.create_index([('user_id', 1)], unique=True)

# Telegram bot token from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper function to check if user is admin
def is_admin(user_id):
    return str(user_id) == os.getenv("ADMIN_ID")

# Function to add a new user to MongoDB
def add_user(user_id, username):
    try:
        user_collection.update_one(
            {'user_id': user_id},
            {'$set': {'user_id': user_id, 'username': username}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error adding user: {e}")

# Function to add user and API to MongoDB
def add_user_api(user_id, api_id):
    try:
        api_collection.update_one(
            {'user_id': user_id},
            {'$set': {'user_id': user_id, 'api_id': api_id}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error adding user API: {e}")

# Validate API ID
async def validate_api_id(api_id):
    try:
        test_url = "https://example.com"  # Replace with a valid URL for testing
        api_url = f"https://bisgram.com/api?api={api_id}&url={test_url}"
        response = requests.get(api_url)
        if response.json().get("status") == "success":
            return True
        return False
    except Exception as error:
        logger.error(f"Error validating API key: {error}")
        return False

# /start command handler
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    add_user(user_id, username)
    user = api_collection.find_one({"user_id": user_id})

    if user:
        await update.message.reply_text(f"📮 Hello {update.message.from_user.first_name}, \nYou are now successfully connected to our Terabis platform.\n\nSend Terabox link for converting")
    else:
        await update.message.reply_text(
            f"📮 Hello {update.message.from_user.first_name},\n\n"
            f"🌟 I am a bot to Convert Your Terabox link to Your Links Directly to your Bisgram.com Account.\n\n"
            f"You can login to your account by clicking on the button below, and entering your api key.\n\n"
            f"💠 You can find your API key at https://bisgram.com/member/tools/api\n\n"
            f"ℹ Send me /help to get How to Use the Bot Guide.\n\n"
            f"🎬 Check out the video tutorial: https://t.me/terabis/11"
        )

# /help command handler
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "How to Connect:\n"
        "1. Go to Bisgram.com\n"
        "2. Create an Account\n"
        "3. Click on the menu bar (top left side)\n"
        "4. Click on *Tools > Developer API*\n"
        "5. Copy the API token\n"
        "6. Use this command: /connect YOUR_API_KEY\n"
        "Example: /connect 8268d7f25na2c690bk25d4k20fbc63p5p09d6906\n\n"
        "🎬 Check out the video tutorial: \nhttps://t.me/terabis/11\n\n"
        "For any confusion or help, contact @ayushx2026_bot"
    )

# /broadcast command handler (only for admin)
async def broadcast(update: Update, context: CallbackContext) -> None:
    if is_admin(update.message.from_user.id):
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text("Please provide a message to broadcast.\n like this /broadcast massage")
            return

        users = user_collection.find()
        for user in users:
            await context.bot.send_message(chat_id=user['user_id'], text=message)
        await update.message.reply_text("Message broadcasted!")
    else:
        await update.message.reply_text("You are not authorized to broadcast.")

# /broadcast command handler (only for admin) (api id connected)
async def broadcast_api(update: Update, context: CallbackContext) -> None:
    if is_admin(update.message.from_user.id):
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text("Please provide a message to broadcast.\n like this /broadcast_api massage")
            return

        users = api_collection.find()
        for user in users:
            await context.bot.send_message(chat_id=user['user_id'], text=message)
        await update.message.reply_text("Message broadcasted!")
    else:
        await update.message.reply_text("You are not authorized to broadcast.")

# Command: /connect
async def connect(update: Update, context: CallbackContext) -> None:
    message_parts = update.message.text.split(" ")
    if len(message_parts) < 2 or not message_parts[1].strip():
        return await update.message.reply_text("❌ Please provide a valid API key. Example: /connect YOUR_API_KEY\n\nFor API help, use /help")

    api_id = message_parts[1]
    user_id = update.message.from_user.id

    if await validate_api_id(api_id):
        add_user_api(user_id, api_id)
        await update.message.reply_text("✅ API key connected successfully! Send Terabox link for converting")
    else:
        await update.message.reply_text("❌ Invalid API key. Please try again.\n\nHow to connect /help")

# Command: /disconnect
async def disconnect(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    user = api_collection.find_one({"user_id": user_id})
    if user:
        api_collection.delete_one({"user_id": user_id})
        await update.message.reply_text("✅ Your API key has been disconnected successfully.")
    else:
        await update.message.reply_text("⚠️ You have not connected an API key yet.")

# Command: /commands
async def commands(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🤖 *Link Shortener Bot Commands:*\n"
        "- /connect [API_KEY] - Connect your API key.\n"
        "- /disconnect - Disconnect your API key.\n"
        "- /view - View your connected API key.\n"
        "- /help - How to connect to website."
    )

# Command: /view
async def view(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user = api_collection.find_one({"user_id": user_id})
    if user and "api_id" in user:
        await update.message.reply_text(f"✅ Your connected API key: {user['api_id']}", parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ No API key is connected. Use /connect to link one.")

def handle_message(update: Update, context: CallbackContext):
  await update.message.reply_text("hi test")

# Simple TCP Health Check Server
def health_check_server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 8000))
            s.listen(1)
            logger.info("Health check server listening on port 8000...")
            while True:
                conn, addr = s.accept()
                with conn:
                    logger.info(f'Health check received from {addr}')
                    conn.sendall(b"OK")
    except Exception as e:
        logger.error(f"Health check server error: {e}")

# MongoDB Connection Test
def test_mongo_connection():
    try:
        client.admin.command('ping')
        logger.info("MongoDB connection successful")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")

# Main function to run the bot and the health check server
def main():
    # Test MongoDB connection
    test_mongo_connection()

    # Start the health check server in a separate thread
    health_thread = threading.Thread(target=health_check_server)
    health_thread.daemon = True
    health_thread.start()

    # Create an Application object
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("broadcast_api", broadcast_api))
    application.add_handler(CommandHandler("connect", connect))
    application.add_handler(CommandHandler("disconnect", disconnect))
    application.add_handler(CommandHandler("commands", commands))
    application.add_handler(CommandHandler("view", view))
    application.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.video | Filters.document, handle_message))
    
    # Start polling for updates from Telegram
    application.run_polling()

if __name__ == '__main__':
    main()
