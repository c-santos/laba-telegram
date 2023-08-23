from typing import Final

from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from assets import start
from config import TELEGRAM_TOKEN
from weatheroop import Forecast

BOT_USERNAME: Final = '@canilababot'

# Commands


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Prompt user to select location in start prompt
    await update.message.reply_text(start.text)


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    forecast = Forecast()
    response_str: str = forecast.now()
    await update.message.reply_text(response_str)


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    forecast = Forecast()
    response_str: str = forecast.today()
    await update.message.reply_text(response_str)

# TODO Allow user to set location
# async def setlocation_command()

# TODO Allow user to set laundry days where they will be notified in the morning (calls /today command)
# async def setlaundrydays_command()


# Responses


def handle_response(text: str) -> str:  # How bot replies
    text = text.lower()

    return text

# Messages


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message_type: str = update.message.chat.type
    text: str = update.message.text

    # Logger
    print(f'User {update.message.chat.id} in {message_type}: "{text}"')

    if message_type == 'group':  # If bot is in a group chat
        if BOT_USERNAME in text:  # If bot is mentioned
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return

    else:  # If bot is in a private chat
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
    app.add_handler(CommandHandler('today', today_command))
    # app.add_handler(CommandHandler('setlocation', setlocation_command))
    # app.add_handler(CommandHandler('setlaundrydays', setlaundrydays_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polling
    print('Polling...')
    app.run_polling(poll_interval=5)
