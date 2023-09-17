import os
import logging
from datetime import datetime as dt
from typing import Final

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
from db.laundryDB import LaundryDB
from forecast import Forecast
from util.weekday import is_equal

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

BOT_USERNAME: Final = "@canilababot"

SELECTING_ACTION, SET_DAYS, ADDING_DAYS = map(chr, range(3))
EXIT = ConversationHandler.END

"""
    ADD SET LOCATION FUNCTIONALITY
    - Add location=(lon,lat) to database
    - Ask location from user on /start
    - Add location as an attribute of Forecast object
        - lon, lat as variables into OPEN_METEO_API url
    
    WHERE WE LEFT OFF:
    - Restructuring DBHelper
        - decouple setup()
        - add_user() error handling
        - cleanup getters, up/setters, deleters

    - What if laundrydays of user is empty? What happens during the daily notif?
        - Try getting days, and if does not exist, do nothing basically
        - Error handling

    - Restructure Forecast object
        - attr, properties
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO Prompt user to select location in start prompt

    user_id = update.message.chat_id
    user_name = update.message.from_user.first_name

    db = LaundryDB()
    db.add_user(user_id)

    if db.get_lat(user_id) == None:
        db.close()
        keyboard = [
            [
                KeyboardButton(text="Share location", request_location=True),
            ],
            [
                KeyboardButton(text="Don't share location", request_location=False),
            ],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        text: str = f"--------------\n👕👖👗\n\nHello {user_name}! I am the Laba Bot. 👋\nStart by sharing your location so I can get the weather."
        await update.message.reply_text(text, reply_markup=reply_markup)

    else:
        db.close()
        text: str = f"--------------\n👕👖👗\n\nHello {user_name}! I am the Laba Bot. 👋\nClick on the menu to see my commands."
        await update.message.reply_text(text)

    # await context.bot.send_message(text, reply_markup=reply_markup)


async def save_user_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    lon: float = update.message.location.longitude
    lat: float = update.message.location.latitude

    db = LaundryDB()
    db.save_location(user_id, lon, lat)
    db.close()

    await context.bot.send_message(
        chat_id=user_id,
        text="Successfully saved your location. Click on the menu to see my commands 😄.",
        reply_markup=ReplyKeyboardRemove(selective=True),
    )


async def default_user_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    db = LaundryDB()
    db.save_location(user_id, 121.1222, 14.5786)
    db.close()

    await context.bot.send_message(
        chat_id=user_id,
        text="Saved your location to the default location. The default location is in Cainta, PH.\n\nClick on the menu to see my commands 😄.",
        reply_markup=ReplyKeyboardRemove(selective=True),
    )


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    db = LaundryDB()
    lon: float = db.get_lon(user_id)
    lat: float = db.get_lat(user_id)
    db.close()

    forecast = Forecast(lon, lat)
    response_str: str = forecast.now()
    await update.message.reply_text(response_str)


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    db = LaundryDB()
    lon: float = db.get_lon(user_id)
    lat: float = db.get_lat(user_id)
    db.close()

    forecast = Forecast(lon, lat)
    response_str: str = forecast.today()
    await update.message.reply_text(response_str)


async def laundrydays_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    db = LaundryDB()
    set_days = db.get_day(user_id)

    if set_days == None:
        keyboard = [
            [
                InlineKeyboardButton("Set", callback_data="setdays"),
                InlineKeyboardButton("Exit", callback_data="exit"),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        text: str = "Set laundry days to be notified if you can laba on those days."

    else:
        keyboard = [
            [
                InlineKeyboardButton("Update", callback_data="setdays"),
                InlineKeyboardButton("Clear", callback_data="clear"),
            ],
            [
                InlineKeyboardButton("Exit", callback_data="exit"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(
            keyboard,
        )
        text: str = f"Your laundry days are set to {set_days[0]}."

    db.close()
    await update.message.reply_text(text, reply_markup=reply_markup)
    return SELECTING_ACTION


async def setdays(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # nested conversation

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("Mon", callback_data="Mon"),
            InlineKeyboardButton("Tue", callback_data="Tue"),
            InlineKeyboardButton("Wed", callback_data="Wed"),
        ],
        [
            InlineKeyboardButton("Thu", callback_data="Thu"),
            InlineKeyboardButton("Fri", callback_data="Fri"),
            InlineKeyboardButton("Sat", callback_data="Sat"),
        ],
        [
            InlineKeyboardButton("Sun", callback_data="Sun"),
            InlineKeyboardButton("Exit", callback_data="exit"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    week_dict = {
        "Mon": False,
        "Tue": False,
        "Wed": False,
        "Thu": False,
        "Fri": False,
        "Sat": False,
        "Sun": False,
    }

    context.user_data["week_dict"] = week_dict

    await query.edit_message_text(
        "Choose your laundry days.", reply_markup=reply_markup
    )
    logger.info(context.user_data)

    return SET_DAYS


async def choosing_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    logger.info(f"Data received:\t{query.data}")

    if query.data == "exit":
        await query.edit_message_text("Exited.")
        return EXIT

    day = query.data

    # Add/remove checkmark of button if pressed.
    context.user_data["week_dict"][day] = not context.user_data["week_dict"][day]

    # Populate inline keyboard buttons.
    keyboard = []
    buttons = []
    week_dict = context.user_data["week_dict"]

    for k, v in week_dict.items():
        if v == True:
            buttons.append(InlineKeyboardButton(f"✅ {k}", callback_data=k))
        else:
            buttons.append(InlineKeyboardButton(f"{k}", callback_data=k))

    # Add Save and Exit buttons at the end.
    buttons.append(InlineKeyboardButton("Save", callback_data="save"))
    buttons.append(InlineKeyboardButton("Exit", callback_data="exit"))

    # Prepare and set button placement, alignment.
    keyboard = [buttons[i : i + 3] for i in range(0, 9, 3)]

    reply_markup = InlineKeyboardMarkup(keyboard)

    logger.info(context.user_data)

    await query.edit_message_text(
        "Choose your laundry days.", reply_markup=reply_markup
    )
    return ADDING_DAYS


async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    week_dict = context.user_data["week_dict"]

    db = LaundryDB()
    db.save(user_id, week_dict)
    db.close()

    await query.edit_message_text("Saved laundry days.")
    logger.info("Saved laundry days.")

    return EXIT


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    db = LaundryDB()
    db.delete_entry(user_id)
    db.close()

    await query.edit_message_text("Cleared laundry days.")

    return EXIT


async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Exited.")

    return EXIT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")

    return EXIT


async def today_notify(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    db = LaundryDB()

    lon: float = db.get_lon(user_id)
    lat: float = db.get_lat(user_id)

    db.close()

    forecast = Forecast(lon, lat)
    response_str: str = forecast.today()
    await context.bot.send_message(chat_id=user_id, text=response_str)


async def notify(context: ContextTypes.DEFAULT_TYPE):
    # Get laundry days with laundryDB
    logger.info("Notifying users...")

    db = LaundryDB()
    data = db.dump()
    db.close()

    # Will be a problem in the future if database scales
    for row in data:
        user_id = row[0]
        laundrydays = row[1]

        if laundrydays == None:
            logger.warning(f"User {user_id} does not have laundry days.")
        else:
            if is_equal(laundrydays):
                logger.info(f"User {user_id} notified successfully.")
                await today_notify(user_id, context)

    logger.info("All users notified successfully.")


# Responses
def handle_response(text: str) -> str:  # How bot replies
    text = text.lower()

    return text


# Messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    text = text.lower()

    # Logger
    logger.info(f'User {update.message.chat.id} in {message_type}: "{text}"')

    if message_type == "group":  # If bot is in a group chat
        if BOT_USERNAME in text:  # If bot is mentioned
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            response: str = handle_response(new_text)
        else:
            return

    else:  # If bot is in a private chat
        response: str = handle_response(text)

        if "can i laba" in text:
            await now_command(update, context)

        if "don't share location" in text:
            await default_user_location(update, context)

        else:
            logger.info(f"Bot: {response}")
            await update.message.reply_text(response)


# Error


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(
        f"Update {update} caused error \n{context.error.with_traceback}\n{context.error}"
    )


def main():
    load_dotenv()

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    logger.info("Starting...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    job_queue = app.job_queue
    # notify_job = job_queue.run_daily(notify, dt.time(hour=6, minute=0))
    notify_job = job_queue.run_repeating(notify, interval=50, first=10)

    # CallbackQueryHandler(A, B) : If B is received from a button, A will be called

    # Nested Conversation
    set_days_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(choosing_day, pattern="^[A-z]{1}[a-z]{2}$ || ^exit$")
        ],
        states={
            ADDING_DAYS: [
                CallbackQueryHandler(choosing_day, pattern="^[A-z]{1}[a-z]{2}$"),
                CallbackQueryHandler(save, "save"),
                CallbackQueryHandler(exit, "exit"),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        map_to_parent={EXIT: EXIT},
    )

    # Top Level
    laundrydays_convhandler = ConversationHandler(
        entry_points=[CommandHandler("laundrydays", laundrydays_command)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(setdays, "setdays"),
                CallbackQueryHandler(clear, "clear"),
                CallbackQueryHandler(exit, "exit"),
            ],
            SET_DAYS: [set_days_conv],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("now", now_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.LOCATION, save_user_location))

    # Conversations
    app.add_handler(laundrydays_convhandler)

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polling
    logger.info("Polling...")
    app.run_polling(poll_interval=1, allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
