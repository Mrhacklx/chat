import logging, os, socket, threading
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client['telegram_bot']
user_collection = db['users']
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
admin_id = os.getenv("ADMIN_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_user(user_id, username):
    user_collection.update_one({'user_id': user_id}, {'$set': {'user_id': user_id, 'username': username}}, upsert=True)

async def start(update: Update, context: CallbackContext):
    user_id, username = update.message.from_user.id, update.message.from_user.username
    add_user(user_id, username)
    await update.message.reply_text(f"Hello {username}, welcome to the bot!")

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text('Use /start to start the bot!')

async def broadcast(update: Update, context: CallbackContext):
    if str(update.message.from_user.id) == admin_id:
        message = ' '.join(context.args)
        if not message:
            await update.message.reply_text("Please provide a message to broadcast.")
            return
        for user in user_collection.find():
            await context.bot.send_message(chat_id=user['user_id'], text=message)
        await update.message.reply_text("Message broadcasted!")
    else:
        await update.message.reply_text("You are not authorized to broadcast.")

def health_check_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 8000))
        s.listen(1)
        print("Health check server listening on port 8000...")
        while True:
            conn, _ = s.accept()
            with conn:
                conn.sendall(b"OK")

def main():
    try:
        client.admin.command('ping')
        print("MongoDB connection successful")
    except Exception as e:
        print(f"MongoDB connection error: {e}")

    threading.Thread(target=health_check_server, daemon=True).start()

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("broadcast", broadcast))

    application.run_polling()

if __name__ == '__main__':
    main()
