from typing import Final

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, ConversationHandler, filters, CallbackQueryHandler)

from assets import days
from config import TELEGRAM_TOKEN
from weatheroop import Forecast
from laundryDB import LaundryDB

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

BOT_USERNAME: Final = '@canilababot'
# Connect to database

# Commands

SELECTING_ACTION, SET_DAYS, ADDING_DAYS, EXIT = 0, 1, 2, 3


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO Prompt user to select location in start prompt

    user_id = update.message.chat_id
    user_name = update.message.from_user.first_name

    text: str = f'--------------\n👕👖👗\n\nHello {user_name}! I am the Laba Bot. 👋\nClick on the menu to access my commands.'

    await update.message.reply_text(text)


async def get_user_location(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print(update.message.location)
    await update.message.reply_text('Location received.')


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    forecast = Forecast()
    response_str: str = forecast.now()
    await update.message.reply_text(response_str)


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    forecast = Forecast()
    response_str: str = forecast.today()
    await update.message.reply_text(response_str)


async def laundrydays_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id

    db = LaundryDB()
    set_days = db.get_day(user_id)

    if set_days == None:
        keyboard = [
            [
                InlineKeyboardButton('Set', callback_data='setdays'),
                InlineKeyboardButton('Exit', callback_data='exit')
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        text: str = 'Set laundry days to be notified if you can laba on those days.'

    else:
        keyboard = [
            [
                InlineKeyboardButton('Update', callback_data='setdays'),
                InlineKeyboardButton('Clear', callback_data='clear')
            ],
            [
                InlineKeyboardButton('Exit', callback_data='exit'),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard, )
        text: str = f'Your laundry days are set to {set_days}.'

    db.close()
    await update.message.reply_text(text, reply_markup=reply_markup)
    return SELECTING_ACTION


async def setdays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # nested conversation

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton('Mon', callback_data='Mon'),
            InlineKeyboardButton('Tue', callback_data='Tue'),
            InlineKeyboardButton('Wed', callback_data='Wed'),
        ],
        [
            InlineKeyboardButton('Thu', callback_data='Thu'),
            InlineKeyboardButton('Fri', callback_data='Fri'),
            InlineKeyboardButton('Sat', callback_data='Sat'),
        ],
        [
            InlineKeyboardButton('Sun', callback_data='Sun'),
            InlineKeyboardButton('Save', callback_data='save'),
            InlineKeyboardButton('Exit', callback_data='exit'),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # user_data.update({REPEAT: False})
    week_dict = {
        'Mon': False,
        'Tue': False,
        'Wed': False,
        'Thu': False,
        'Fri': False,
        'Sat': False,
        'Sun': False
    }

    context.user_data['week_dict'] = week_dict

    await query.edit_message_text('Choose your laundry days.', reply_markup=reply_markup)
    print(context.user_data)

    return SET_DAYS


async def choosing_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    day = query.data

    print(f'Data received:\t{day}')

    # Add/remove checkmark of button if pressed.
    context.user_data['week_dict'][day] = not context.user_data['week_dict'][day]

    # Populate inline keyboard buttons.
    keyboard = []
    buttons = []
    week_dict = context.user_data['week_dict']

    for k, v in week_dict.items():
        if v == True:
            buttons.append(InlineKeyboardButton(
                f'✅ {k}', callback_data=k))
        else:
            buttons.append(InlineKeyboardButton(
                f'{k}', callback_data=k))

    # Add Save and Exit buttons at the end.
    buttons.append(InlineKeyboardButton('Save', callback_data='save'))
    buttons.append(InlineKeyboardButton('Exit', callback_data='exit'))

    # Prepare and set button placement, alignment.
    keyboard = [buttons[i:i+3] for i in range(0, 9, 3)]

    reply_markup = InlineKeyboardMarkup(keyboard)

    print(context.user_data)

    await query.edit_message_text('Choose your laundry days.', reply_markup=reply_markup)
    return ADDING_DAYS


async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    week_dict = context.user_data['week_dict']
    print('Saving laundry days...')

    db = LaundryDB()
    db.save(user_id, week_dict)
    db.close()

    await query.edit_message_text('Saved laundry days.')

    return EXIT


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    db = LaundryDB()
    db.delete_day(user_id)
    db.close()

    await query.edit_message_text('Cleared laundry days.')

    return EXIT


async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('Exited.')
    return EXIT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Cancelled.')
    
    return ConversationHandler.END



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

        if 'can i laba' in text:
            await now_command(update, context)
        else:
            print(f'Bot: {response}')
            await update.message.reply_text(response)


# Error
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(
        f'Update {update} caused error \n{context.error.with_traceback}\n{context.error}')

if __name__ == '__main__':
    print('Starting...')
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    set_days_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            choosing_day, pattern="^[A-z]{1}[a-z]{2}$")],
        states={
            ADDING_DAYS: [
                CallbackQueryHandler(
                    choosing_day, pattern="^[A-z]{1}[a-z]{2}$"),
                # [CallbackQueryHandler(choosing_days, '^[a-z]{3}$')]
                CallbackQueryHandler(save, 'save'),
                CallbackQueryHandler(exit, 'exit')
            ],
            EXIT: [
                CallbackQueryHandler(cancel, 'save'),
                CallbackQueryHandler(cancel, 'exit'),
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        map_to_parent={
            EXIT: EXIT
        }
    )

    # Top Level
    laundrydays_convhandler = ConversationHandler(
        entry_points=[CommandHandler('laundrydays', laundrydays_command)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(setdays, 'setdays'),
                CallbackQueryHandler(clear, 'clear'),
                CallbackQueryHandler(exit, 'exit')
            ],
            SET_DAYS: [set_days_conv],
            EXIT: [CommandHandler('cancel', cancel)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('now', now_command))
    app.add_handler(CommandHandler('today', today_command))
    app.add_handler(CommandHandler('cancel', cancel))

    # Conversations
    app.add_handler(laundrydays_convhandler)

    # Messages
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polling
    print('Polling...')
    app.run_polling(poll_interval=1)
