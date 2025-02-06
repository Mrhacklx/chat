import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Enable logging for better debugging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the start command handler
async def start(update: Update, context):
    await update.message.reply_text('Hello! Welcome to the bot.')

# Define the connect command handler
async def connect(update: Update, context):
    await update.message.reply_text('Connecting...')

# Define the disconnect command handler
async def disconnect(update: Update, context):
    await update.message.reply_text('Disconnecting...')

# Define the help command handler
async def help_command(update: Update, context):
    help_text = """
    Here are some commands you can use:
    /start - Start the bot
    /connect - Connect
    /disconnect - Disconnect
    /help - Get help
    /commands - List all commands
    /view - View your status
    """
    await update.message.reply_text(help_text)

# Define the commands command handler
async def commands(update: Update, context):
    await update.message.reply_text('Here is a list of available commands: /start, /connect, /disconnect, /help')

# Define the view command handler
async def view(update: Update, context):
    await update.message.reply_text('Viewing your status...')

# Define the message handler for media messages
async def handle_media_message(update: Update, context):
    # Handle media messages, for example:
    if update.message.photo:
        await update.message.reply_text("Nice photo!")
    else:
        await update.message.reply_text("Sorry, I can only handle photo messages for now.")

# Main function to set up and run the bot
async def main():
    # Create the Application instance using your bot's token
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    # Add handlers for different commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("connect", connect))
    application.add_handler(CommandHandler("disconnect", disconnect))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("commands", commands))
    application.add_handler(CommandHandler("view", view))
    application.add_handler(MessageHandler(filters.TEXT, handle_media_message))  # Handling text messages

    try:
        # Initialize the bot and start the polling loop
        await application.initialize()  # Ensure that initialization is properly awaited
        await application.run_polling()  # Start polling for messages
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        # Shutdown the application gracefully
        await application.shutdown()  # Ensure the application shuts down properly

# If running as the main script
if __name__ == '__main__':
    try:
        asyncio.run(main())  # This is for environments that don't manage event loops
    except RuntimeError:
        pass  # In case we're already in an event loop (e.g., cloud environment)
