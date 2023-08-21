from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# from weather import now
from weatheroop import Forecast
from config import TELEGRAM_TOKEN

BOT_USERNAME: Final = '@canilababot'

# Commands

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am the Laba Bot.')

async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    forecast = Forecast()
    response_str: str = forecast.now()
    await update.message.reply_text(response_str)


# Responses

def handle_response(text: str) -> str:
    text = text.lower()

    return text

# Messages

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message_type: str = update.message.chat.type
    text: str = update.message.text
    
    # Logger
    print(f'User {update.message.chat.id} in {message_type}: "{text}"')

    if message_type == 'group': # If bot is in a group chat
        if BOT_USERNAME in text: # If bot is mentioned
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    
    else: # If bot is in a private chat
        response: str = handle_response(text)

    print(f'Bot: {response}')

    await update.message.reply_text(response)

# Error

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting...')
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('now', now_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polling
    print('Polling...')
    app.run_polling(poll_interval=5)