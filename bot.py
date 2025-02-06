# Remove asyncio.run(main()) and directly call main()

import os
import json
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters  # Correct import for Filters
from flask import Flask, request
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))  # Mongo URI from environment variables
db = client['telegram_bot']  # Database name
user_collection = db['users']  # Collection for storing user data

# Function to save user data to MongoDB
def save_user_data(user_id, api_key):
    user_collection.update_one(
        {'user_id': user_id},
        {'$set': {'user_id': user_id, 'api_key': api_key}},
        upsert=True
    )

# Function to retrieve user data from MongoDB
def get_user_data(user_id):
    user = user_collection.find_one({'user_id': user_id})
    return user

# Validate API key
def validate_api_key(api_key):
    try:
        test_url = "https://example.com"  # Replace with a valid URL for testing
        api_url = f"https://bisgram.com/api?api={api_key}&url={test_url}"
        response = requests.get(api_url)
        return response.json().get('status') == 'success'
    except Exception as e:
        print("Error validating API key:", e)
        return False

# Define /start command handler
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = get_user_data(user_id)
    
    if user:
        await update.message.reply_text(f"📮 Hello {update.message.from_user.first_name}, \nYou are now successfully connected to our Terabis platform.\n\nSend a Tearbox link for converting.")
    else:
        await update.message.reply_text(f"📮 Hello {update.message.from_user.first_name},\n\n🌟 I am a bot to Convert Your Terabox link to Your Links Directly to your Bisgram.com Account.\n\nYou can login to your account by clicking on the button below, and entering your API key.\n\n💠 You can find your API key on https://bisgram.com/member/tools/api\n\nℹ Send me /help to get the guide.\n\n🎬 Check out the tutorial video: https://t.me/terabis/9")

# Define /connect command handler
async def connect(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        await update.message.reply_text("Please provide your API key. Example: /connect YOUR_API_KEY")
        return

    api_key = context.args[0]
    user_id = update.message.from_user.id

    if validate_api_key(api_key):
        save_user_data(user_id, api_key)
        await update.message.reply_text("✅ API key connected successfully! Send a Tearbox link for converting.")
    else:
        await update.message.reply_text("❌ Invalid API key. Please try again.\n\nHow to connect /help")

# Define /disconnect command handler
async def disconnect(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if get_user_data(user_id):
        user_collection.delete_one({'user_id': user_id})
        await update.message.reply_text("✅ Your API key has been disconnected successfully.")
    else:
        await update.message.reply_text("⚠️ You have not connected an API key yet.")

# Define /help command handler
async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        """
How to Connect:
1. Go to Bisgram.com
2. Create an Account
3. Click on the menu bar (top left side)
4. Click on *Tools > Developer API*
5. Copy the API token
6. Use this command: /connect YOUR_API_KEY
   Example: /connect 8268d7f25na2c690bk25d4k20fbc63p5p09d6906

🎬 Check out the tutorial video: 
   https://t.me/terabis/9

For any confusion or help, contact @ayushx2026_bot
        """
    )

# Define /commands handler
async def commands(update: Update, context: CallbackContext):
    await update.message.reply_text(
        """
🤖 *Link Shortener Bot Commands:*
- /connect [API_KEY] - Connect your API key.
- /disconnect - Disconnect your API key.
- /view - View your connected API key.
- /help - How to connect to website.
        """, parse_mode="Markdown"
    )

# Define /view command handler
async def view(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user = get_user_data(user_id)
    
    if user and 'api_key' in user:
        await update.message.reply_text(f"✅ Your connected API key: `{user['api_key']}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ No API key is connected. Use /connect to link one.")

# Define function to handle incoming media messages
async def handle_media_message(update: Update, context: CallbackContext):
    message_text = update.message.caption or update.message.text or ""

    # Regex to extract URLs
    link_regex = r"(https?:\/\/[^\s]+)"
    links = re.findall(link_regex, message_text)

    if links and any("tera" in link and "/s/" in link for link in links):
        extracted_link = next(link for link in links if "tera" in link and "/s/" in link)
        long_url = extracted_link.replace("/s/", "https://terabis.blogspot.com/?url=")

        # Further processing like shortening the link, handling the media, etc.
        # This part is similar to the JavaScript logic for shortening links and sending the response

    else:
        await update.message.reply_text("Please send a valid Terabox link.")

# Define Flask app for webhook
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = Update.de_json(json_str, bot)
    dispatcher.process_update(update)
    return 'OK'

# Set up the bot and dispatcher
async def main():
    # Initialize the bot with token from environment variable
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("connect", connect))
    application.add_handler(CommandHandler("disconnect", disconnect))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("commands", commands))
    application.add_handler(CommandHandler("view", view))
    application.add_handler(MessageHandler(filters.TEXT, handle_media_message))  # Correct filter import

    # Webhook setup for production
    bot = application.bot
    await bot.set_webhook(url=f"https://{os.getenv('WEBHOOK_URL')}/webhook")

    # Start the bot
    await application.run_polling()

# Run the bot (without asyncio.run in environments where event loops already run)
if __name__ == '__main__':
    main()  # Call the main function without asyncio.run()
