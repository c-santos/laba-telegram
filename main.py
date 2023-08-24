import re
from typing import Final

from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, ConversationHandler, filters)

from assets import days, start
from config import TELEGRAM_TOKEN
from weatheroop import Forecast

import sqlite3

BOT_USERNAME: Final = '@canilababot'

# Connect to database
conn = sqlite3.connect("user_config.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_laundry_days (
               user_id TEXT PRIMARY KEY,
               reminder_days TEXT
                )
               ''')

# Commands


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO Prompt user to select location in start prompt

    user_id = update.message.chat_id

    cursor.execute(
        'SELECT * FROM user_laundry_days WHERE user_id = ?', (user_id,))

    user_config = cursor.fetchone()

    if user_config:
        print(f'Your laundry days are set to {user_config[1]}')
    else:
        print('You currently don\'t have any laundry days set. Use the /setlaundrydays command to set laundry days and automatically be sent a message if you can laba today.')

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
# async def setlocation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_location = update.message.location
#     print(user_location)
#     await update.message.reply_text(user_location)


async def setlaundrydays_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO Allow user to set through buttons or user input

    # update.message essentially is the message sent by the user. So in this case, '/setlaundrydays'
    user_id = update.message.chat_id

    # Check current laundry days of user
    reminder_days = cursor.execute(
        'SELECT reminder_days FROM user_laundry_days WHERE user_id=?', (user_id,)).fetchone()

    reminder_days = ''.join(map(str, reminder_days))
    print(reminder_days, type(reminder_days))

    output: str = f'Laundry day/s currently set to {reminder_days}.\n\n'

    if not reminder_days:
        output += 'When do you want to be notified?\nType /cancel if you want to cancel.'
    else:
        output += 'Enter new days if you want to update your laundry days.\nType /cancel if you want to cancel.'

    output += '\n\nFollow the format: M, T, W, Th, F, Sa, Su\n\nYou may add more than one laundry day. Separate the days by a space.\n\nExample: "M Th Sa" (case insensitive)'

    await update.message.reply_text(output)

    return 1


async def get_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO Rejecting bad input

    user_input = update.message.text.lower()
    user_id = update.message.chat_id

    if user_input in ['cancel', '/cancel', 'q']:
        await update.message.reply_text("Setting laundry days cancelled.")
        return cancel()

    user_input = user_input.split()
    user_input = list(set(user_input))
    print(user_input, type(user_input))

    for day in user_input:
        if day not in days.day_to_int.keys():
            await update.message.reply_text('Invalid input. Try again.')
            return 1

    days_int: list[int] = days.convert_to_int(user_input)
    list.sort(days_int)
    days_str = days.convert_to_day(days_int)

    print('days_int', days_int)
    print('days_str', days_str)

    user_input = ' '.join(days_str)
    # user_input = ' '.join(user_input)

    # Check if user has existing laundry days
    cursor.execute(
        'SELECT * FROM user_laundry_days WHERE user_id=?', (user_id,))

    if cursor.fetchone():
        cursor.execute(
            'UPDATE user_laundry_days SET reminder_days=? WHERE user_id=?', (user_input, user_id,))
    else:
        cursor.execute(
            'INSERT INTO user_laundry_days (user_id, reminder_days) VALUES (?, ?)', (user_id, user_input,))

    conn.commit()

    user_config = cursor.execute(
        'SELECT * FROM user_laundry_days WHERE user_id=?', (user_id,))

    print(user_config.fetchone())

    await update.message.reply_text(f'Laundry day/s set to {user_input}.')

    return ConversationHandler.END


async def check_laundry_days(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id

    reminder_days = cursor.execute(
        'SELECT reminder_days FROM user_laundry_days WHERE user_id=?', (user_id,)).fetchone()

    reminder_days = ' '.join(map(str, reminder_days))
    print(reminder_days, type(reminder_days))

    output: str = f'Laundry day/s currently set to {reminder_days}.'

    await update.message.reply_text(output)

    return reminder_days


# TODO Add way to clear laundry days
# async def clearlaundrydays_command():
#   await update.message.reply_text('Laundry days cleared successfully. You will no longer be notified.')

def cancel():
    return ConversationHandler.END


# TODO Check every morning if current day is reminder day. Send message if it is.
# def do_reminders():


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
    print(f'Update {update} caused error \n{context.error}')

if __name__ == '__main__':
    print('Starting...')
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands

    setlaundrydays_convhandler = ConversationHandler(
        entry_points=[CommandHandler(
            'setlaundrydays', setlaundrydays_command)],

        states={
            1: [MessageHandler(filters.TEXT, get_days)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('now', now_command))
    app.add_handler(CommandHandler('today', today_command))
    # app.add_handler(CommandHandler('setlocation', setlocation_command))
    # app.add_handler(CommandHandler('cancel', cancel))
    app.add_handler(CommandHandler('checklaundrydays', check_laundry_days))
    app.add_handler(setlaundrydays_convhandler)

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polling
    print('Polling...')
    app.run_polling(poll_interval=3)
