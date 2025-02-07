import logging
import os
import socket
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from pymongo import MongoClient, errors
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB setup
try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client['telegram_bot']
    user_collection = db['users']
    api_collection = db['api_id']
    logging.info("MongoDB connected successfully.")
except errors.PyMongoError as e:
    logging.error(f"Error connecting to MongoDB: {e}")
    exit(1)

# Telegram bot token from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to add a new user to MongoDB
def add_user(user_id, username):
    try:
        user_collection.update_one(
            {'user_id': user_id},
            {'$set': {'user_id': user_id, 'username': username}},
            upsert=True
        )
    except errors.PyMongoError as e:
        logging.error(f"Error adding user {user_id}: {e}")

# Function to add user and API to MongoDB
def add_user_api(user_id, api_id):
    try:
        api_collection.update_one(
            {'user_id': user_id},
            {'$set': {'user_id': user_id, 'api_id': api_id}},
            upsert=True
        )
    except errors.PyMongoError as e:
        logging.error(f"Error adding API for user {user_id}: {e}")

# /start command handler
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    add_user(user_id, username)
    user = api_collection.find_one({"user_id": user_id})
    
    try:
        if user:
            await update.message.reply(f"📮 Hello {update.message.from_user.first_name}, \nYou are now successfully connected to our Terabis platform.\n\nSend Terabox link for converting")
        else:
            await update.message.reply(
                f"📮 Hello {update.message.from_user.first_name},\n\n"
                f"🌟 I am a bot to Convert Your Terabox link to Your Links Directly to your Bisgram.com Account.\n\n"
                f"You can login to your account by clicking on the button below, and entering your api key.\n\n"
                f"💠 You can find your API key at https://bisgram.com/member/tools/api\n\n"
                f"ℹ Send me /help to get How to Use the Bot Guide.\n\n"
                f"🎬 Check out the video tutorial: https://t.me/terabis/11"
            )
    except AttributeError:
        # Handle the case when message object is None or doesn't have a reply method
        logging.error(f"Error: Unable to send reply to user {user_id} due to missing message object.")
    except Exception as e:
        logging.error(f"Error in /start command for user {user_id}: {e}")
        if update.message:
            await update.message.reply("⚠️ An error occurred while processing your request.")
        else:
            logging.error("Message object is missing, unable to send reply.")

# /help command handler
async def help_command(update: Update, context: CallbackContext) -> None:
    try:
        await update.message.reply("For any confusion or help, contact @ayushx2026_bot"
        )
    except Exception as e:
        logging.error(f"Error in /help command: {e}")
        await update.message.reply("⚠️ An error occurred while processing your request.")

# /broadcast command handler (only for admin)
async def broadcast(update: Update, context: CallbackContext) -> None:
    try:
        # Ensure the user is the admin
        admin_id = os.getenv("ADMIN_ID")
        if str(update.message.from_user.id) == admin_id:
            message = ' '.join(context.args)  # Capture arguments passed to /broadcast
            if not message:
                await update.message.reply_text("Please provide a message to broadcast.\n like this /broadcast massage")
                return

            users = user_collection.find()
            for user in users:
                try:
                    await context.bot.send_message(chat_id=user['user_id'], text=message)
                except Exception as e:
                    logging.error(f"Error sending broadcast to user {user['user_id']}: {e}")
            await update.message.reply_text("Message broadcasted!")
        else:
            await update.message.reply_text("You are not authorized to broadcast.")
    except Exception as e:
        logging.error(f"Error in /broadcast command: {e}")
        await update.message.reply_text("⚠️ An error occurred while processing your request.")

# /broadcast_api command handler (only for admin) (api id connected)
async def broadcast_api(update: Update, context: CallbackContext) -> None:
    try:
        # Ensure the user is the admin
        admin_id = os.getenv("ADMIN_ID")
        if str(update.message.from_user.id) == admin_id:
            message = ' '.join(context.args)  # Capture arguments passed to /broadcast_api
            if not message:
                await update.message.reply_text("Please provide a message to broadcast.\n like this /broadcast_api massage")
                return

            users = api_collection.find()
            for user in users:
                try:
                    await context.bot.send_message(chat_id=user['user_id'], text=message)
                except Exception as e:
                    logging.error(f"Error sending broadcast to user {user['user_id']}: {e}")
            await update.message.reply_text("Message broadcasted!")
        else:
            await update.message.reply_text("You are not authorized to broadcast.")
    except Exception as e:
        logging.error(f"Error in /broadcast_api command: {e}")
        await update.message.reply_text("⚠️ An error occurred while processing your request.")

# Command: /disconnect
async def disconnect(update: Update, context: CallbackContext):
    try:
        user_id = update.message.from_user.id
        user = api_collection.find_one({"user_id": user_id})
        if user:
            api_collection.delete_one({"user_id": user_id})
            await update.message.reply("✅ Your API key has been disconnected successfully.")
        else:
            await update.message.reply("⚠️ You have not connected an API key yet.")
    except Exception as e:
        logging.error(f"Error in /disconnect command for user {update.message.from_user.id}: {e}")
        await update.message.reply("⚠️ An error occurred while processing your request.")

# Command: /commands
async def commands(update: Update, context: CallbackContext):
    try:
        await update.message.reply(
            "🤖 *Link Shortener Bot Commands:*\n"
            "- /connect [API_KEY] - Connect your API key.\n"
            "- /disconnect - Disconnect your API key.\n"
            "- /view - View your connected API key.\n"
            "- /help - How to connect to website."
        )
    except Exception as e:
        logging.error(f"Error in /commands command: {e}")
        await update.message.reply("⚠️ An error occurred while processing your request.")

# Command: /view
async def view(update: Update, context: CallbackContext):
    try:
        user_id = update.message.from_user.id
        user = api_collection.find_one({"user_id": user_id})
        if user and "api_id" in user:
            await update.message.reply(f"✅ Your connected API key: `{user['api_id']}`", parse_mode='Markdown')
        else:
            await update.message.reply("⚠️ No API key is connected. Use /connect to link one.")
    except Exception as e:
        logging.error(f"Error in /view command for user {update.message.from_user.id}: {e}")
        await update.message.reply("⚠️ An error occurred while processing your request.")

# Simple TCP Health Check Server
def health_check_server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', 8000))  # Bind to all available interfaces on port 8000
            s.listen(1)
            logging.info("Health check server listening on port 8000...")
            while True:
                conn, addr = s.accept()
                with conn:
                    logging.info('Health check received from %s', addr)
                    conn.sendall(b"OK")
    except Exception as e:
        logging.error(f"Error in health check server: {e}")

# MongoDB Connection Test (Optional: Check if the MongoDB connection is working)
def test_mongo_connection():
    try:
        client.admin.command('ping')
        logging.info("MongoDB connection successful")
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}")
        exit(1)

# Main function to run the bot and the health check server
def main():
    # Test MongoDB connection (optional)
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
    application.add_handler(CommandHandler("disconnect", disconnect))
    application.add_handler(CommandHandler("commands", commands))
    application.add_handler(CommandHandler("view", view))
    
    # Start polling for updates from Telegram
    application.run_polling()

if __name__ == '__main__':
    main()
