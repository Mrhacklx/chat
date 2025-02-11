import logging
import os
import socket
import re
import threading
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackContext, filters
from pymongo import MongoClient
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client['telegram_bot']
user_collection = db['users']
api_collection = db['api_id']
user_channels_collection = db['user_channels']  # New collection for storing user channels


# MongoDB Indexes
user_collection.create_index([('user_id', 1)], unique=True)
api_collection.create_index([('user_id', 1)], unique=True)
user_channels_collection.create_index([('user_id', 1)], unique=True)  # Index for user channels

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
def add_user_channel(user_id, channel_id):
    try:
        user_channels_collection.update_one(
            {'user_id': user_id},
            {'$set': {'user_id': user_id, 'channel_id': channel_id}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error adding user channel: {e}")

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
            await update.message.reply_text("Please provide a message to broadcast.\n like this /broadcast message")
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
            await update.message.reply_text("Please provide a message to broadcast.\n like this /broadcast_api message")
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

# Handle regular messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data = api_collection.find_one({"user_id": user_id})

    if not user_data or not user_data.get("api_id"):
        await update.message.reply_text("⚠️ You haven't connected your API key yet. Please use /connect [API_KEY].")
        return

    api_key = user_data["api_id"]
    message_text = update.message.caption or update.message.text or ""

    link_regex = r"(https?://[^\s]+)"
    links = re.findall(link_regex, message_text)

    if not links:
        await update.message.reply_text("Please send a valid link to shorten.")
        return

    shortened_links = []  # To store the formatted shortened links
    for idx, link in enumerate(links, start=1):  # Enumerate to create Link 1, Link 2, etc.
        if "/s/" in link:
            link1 = re.sub(r'^.*\/s/', '/s/', link)
            long_url = link1.replace("/s/", "https://terabis.blogspot.com/?url=")

            # Shorten the link using the user's API key
            api_url = f"https://bisgram.com/api?api={api_key}&url={long_url}"
            response = requests.get(api_url)

            if response.json().get("status") == "success":
                shortened_url = response.json().get("shortenedUrl")
                shortened_links.append(f"video {idx} 👇👇\n{shortened_url}")
            # If the response status is not "success", do nothing (invalid link)
        else:
            # If the link is invalid, we do nothing and skip it silently
            continue

    if shortened_links:
        # Format the response text with all the shortened links
        response_text = "🔰 𝙁𝙐𝙇𝙇 𝙑𝙄𝘿𝙀𝙊 🎥\n\n" + "\n\n".join(shortened_links) + "\n\n♡     ❍     ⌲ \nLike React Share"
        
        # Send the response based on the media type
        if update.message.photo:
            await update.message.reply_photo(update.message.photo[-1].file_id, caption=response_text)
        elif update.message.video:
            await update.message.reply_video(update.message.video.file_id, caption=response_text)
        else:
            await update.message.reply_text(response_text)

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
      
async def forward_message_to_user(update: Update, context: CallbackContext) -> None:
    if is_admin(update.message.from_user.id):  # Only allow admin to forward messages
        admin_message = update.message
        users = user_channels_collection.find()  # Get all users and their registered channels
        
        for user in users:
            channel_id = user.get('channel_id')
            if admin_message.text:
                await context.bot.send_message(chat_id=channel_id, text=admin_message.text)
            elif admin_message.photo:
                await context.bot.send_photo(chat_id=channel_id, photo=admin_message.photo[-1].file_id)
            elif admin_message.video:
                await context.bot.send_video(chat_id=channel_id, video=admin_message.video.file_id)
        
        await update.message.reply_text("Message has been forwarded to all registered user channels!")
    else:
        await update.message.reply_text("You are not authorized to forward messages.")
# /set_channel command handler (to allow user to register a channel)
async def set_channel(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if len(context.args) < 1:
        await update.message.reply_text("Please provide a channel ID using: /set_channel your_channel_id")
        return
    
    channel_id = context.args[0]
    add_user_channel(user_id, channel_id)
    await update.message.reply_text(f"Your channel {channel_id} has been registered for forwarding messages.")


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
    application.add_handler(CommandHandler("set_channel", set_channel))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO, handle_message))

    # Start polling for updates from Telegram
    application.run_polling()

if __name__ == '__main__':
    main()
