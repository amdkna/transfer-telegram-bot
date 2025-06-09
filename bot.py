#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sqlite3
import os
import calendar
from datetime import datetime
import pytz
import json

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ParseMode,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    CallbackQueryHandler,
)
from telegram.utils.helpers import escape_markdown

from dotenv import load_dotenv

# ----------------------------
# 1. Load environment variables
# ----------------------------
load_dotenv()

BOT_TOKEN  = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")       # e.g., "-1001234567890" or "@my_channel"
DB_PATH    = os.getenv("DB_PATH", "ads.db")

if not BOT_TOKEN or not CHANNEL_ID:
    raise RuntimeError("لطفاً BOT_TOKEN و CHANNEL_ID را در فایل .env تنظیم کنید.")

# ----------------------------
# 2. Load message templates and bot messages
# ----------------------------
# preview_template.txt should contain placeholders:
#   {role}, {source}, {destination}, {flight_date}, {description}, {user_id}
with open("preview_template.txt", "r", encoding="utf-8") as f:
    PREVIEW_TEMPLATE = f.read()

# message_template.txt should contain placeholders:
#   {role}, {source}, {destination}, {flight_date}, {description}, {user_id}
with open("message_template.txt", "r", encoding="utf-8") as f:
    MESSAGE_TEMPLATE = f.read()

# Load bot messages from messages.json
with open("messages.json", "r", encoding="utf-8") as f:
    MESSAGES = json.load(f)

# ----------------------------
# 3. Enable logging
# ----------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------
# 4. Define conversation states
# ----------------------------
CHOOSING_ROLE, TYPING_SOURCE, TYPING_DESTINATION, SELECTING_DATE, TYPING_DESCRIPTION, CONFIRMATION = range(6)

# ----------------------------
# 5. SQLite helper functions
# ----------------------------
def init_db():
    """
    Create the SQLite database file and 'ads' table if it does not exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            flight_date TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

def save_ad_to_db(ad_data: dict):
    """
    Insert a new ad into the 'ads' table.
    Expects ad_data with keys:
      - role
      - source
      - destination
      - flight_date
      - description
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO ads (role, source, destination, flight_date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            ad_data["role"],
            ad_data["source"],
            ad_data["destination"],
            ad_data["flight_date"],
            ad_data["description"],
        ),
    )
    conn.commit()
    conn.close()

# ----------------------------
# 6. Calendar-building function
# ----------------------------
def build_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    """
    Build an InlineKeyboardMarkup for the given month and year.
    The first row is the Month-Year label (callback_data="IGNORE").
    The second row are the weekday abbreviations (callback_data="IGNORE").
    Subsequent rows show each day as a button with callback_data="DAY-YYYY-MM-DD",
    blank for days outside the month, and skip past dates.
    The final row has "<" and ">" buttons to navigate months.
    """
    keyboard = []

    # 1) Month-Year header
    header_text = f"{calendar.month_name[month]} {year}"
    keyboard.append([InlineKeyboardButton(header_text, callback_data="IGNORE")])

    # 2) Weekday names
    week_days = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
    keyboard.append([InlineKeyboardButton(day, callback_data="IGNORE") for day in week_days])

    # 3) Days of the month
    month_matrix = calendar.monthcalendar(year, month)
    for week in month_matrix:
        row = []
        for day in week:
            if day == 0:
                # Empty cell
                row.append(InlineKeyboardButton(" ", callback_data="IGNORE"))
            else:
                today = datetime.now(pytz.timezone("Asia/Baku")).date()
                candidate = datetime(year, month, day).date()
                if candidate < today:
                    # Past dates are non-clickable placeholders
                    row.append(InlineKeyboardButton(" ", callback_data="IGNORE"))
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    row.append(
                        InlineKeyboardButton(str(day), callback_data=f"DAY-{date_str}")
                    )
        keyboard.append(row)

    # 4) Navigation row (“<” and “>” for previous/next month)
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1

    keyboard.append([
        InlineKeyboardButton("<", callback_data=f"PREV-{prev_year}-{prev_month}"),
        InlineKeyboardButton(">", callback_data=f"NEXT-{next_year}-{next_month}")
    ])

    return InlineKeyboardMarkup(keyboard)

# ----------------------------
# 7. Conversation handlers
# ----------------------------
def start(update: Update, context: CallbackContext) -> int:
    """
    Entry point for /start command.
    Clears any previous data and sends an inline keyboard for choosing role:
    'مسافر' (Passenger) or 'بار دارم' (Cargo).
    """
    # Clear previous user_data
    context.user_data.clear()
    for key in ("role", "source", "destination", "flight_date", "description"):
        context.user_data[key] = None

    # Inline buttons for role selection (Persian only)
    buttons = [
        [
            InlineKeyboardButton(MESSAGES["button_passenger"], callback_data="role_passenger"),
            InlineKeyboardButton(MESSAGES["button_cargo"], callback_data="role_cargo")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    update.message.reply_text(MESSAGES["welcome"], reply_markup=reply_markup)
    return CHOOSING_ROLE

def role_handler(update: Update, context: CallbackContext) -> int:
    """
    Handle the user's choice of role.
    Stores 'مسافر' or 'بار دارم' in user_data['role'], then asks for the source.
    """
    query = update.callback_query
    query.answer()

    data = query.data  # "role_passenger" or "role_cargo"
    if data == "role_passenger":
        context.user_data["role"] = MESSAGES["button_passenger"]
    else:
        context.user_data["role"] = MESSAGES["button_cargo"]

    query.edit_message_text(MESSAGES["prompt_source"])
    return TYPING_SOURCE

def type_source(update: Update, context: CallbackContext) -> int:
    """
    Store the 'source' (کشور، شهر) in user_data and prompt for destination.
    """
    text = update.message.text.strip()
    if not text:
        update.message.reply_text(MESSAGES["invalid_source"])
        return TYPING_SOURCE

    context.user_data["source"] = text
    update.message.reply_text(MESSAGES["prompt_destination"])
    return TYPING_DESTINATION

def type_destination(update: Update, context: CallbackContext) -> int:
    """
    Store the 'destination' (کشور، شهر) and display the calendar
    for the user to select the flight date.
    """
    text = update.message.text.strip()
    if not text:
        update.message.reply_text(MESSAGES["invalid_destination"])
        return TYPING_DESTINATION

    context.user_data["destination"] = text

    # Show the calendar for date picking (current month)
    now = datetime.now(pytz.timezone("Asia/Baku"))
    year, month = now.year, now.month

    update.message.reply_text(MESSAGES["prompt_calendar"])
    update.message.reply_text(
        MESSAGES["calendar_label_current"],
        reply_markup=build_calendar(year, month)
    )
    return SELECTING_DATE

def select_date(update: Update, context: CallbackContext) -> int:
    """
    Handle calendar callbacks: day selection or month navigation.
    If a day is selected, store it in 'flight_date' and ask for description.
    """
    query = update.callback_query
    query.answer()
    data = query.data  # e.g. "DAY-2025-06-15", "PREV-2025-05", "NEXT-2025-07", "IGNORE"

    if data.startswith("DAY-"):
        # User selected a specific day
        selected_date = data.split("-", maxsplit=1)[1]  # "YYYY-MM-DD"
        context.user_data["flight_date"] = selected_date

        # Confirm chosen date and ask for description
        date_text = MESSAGES["date_selected"].format(flight_date=selected_date)
        query.edit_message_text(date_text, parse_mode=ParseMode.MARKDOWN)
        query.message.reply_text(MESSAGES["prompt_description"])
        return TYPING_DESCRIPTION

    elif data.startswith("PREV-") or data.startswith("NEXT-"):
        # User navigated to another month
        parts = data.split("-")
        action = parts[0]  # "PREV" or "NEXT"
        year = int(parts[1])
        month = int(parts[2])

        new_calendar = build_calendar(year, month)
        query.edit_message_reply_markup(reply_markup=new_calendar)
        return SELECTING_DATE

    else:
        # data == "IGNORE" (weekday label or blank cell)
        return SELECTING_DATE

def type_description(update: Update, context: CallbackContext) -> int:
    """
    Store the 'description' in user_data and show a preview of the ad
    using preview_template.txt, including the user's @username or numeric ID.
    """
    text = update.message.text.strip()
    if not text:
        update.message.reply_text(MESSAGES["invalid_description"])
        return TYPING_DESCRIPTION

    context.user_data["description"] = text

    # Retrieve all stored fields
    role         = context.user_data["role"]
    source       = context.user_data["source"]
    destination  = context.user_data["destination"]
    flight_date  = context.user_data["flight_date"]
    description  = context.user_data["description"]

    # Determine the user's Telegram ID or username
    user = update.effective_user
    if user.username:
        tg_id = user.username
    else:
        tg_id = str(user.id)

    # Build the preview text from template
    preview_text = PREVIEW_TEMPLATE.format(
        role=role,
        source=source,
        destination=destination,
        flight_date=flight_date,
        description=description,
        user_id=tg_id,
    )

    # Inline buttons for confirmation
    buttons = [
        [
            InlineKeyboardButton(MESSAGES["button_yes"], callback_data="confirm_yes"),
            InlineKeyboardButton(MESSAGES["button_no"], callback_data="confirm_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    update.message.reply_text(preview_text, reply_markup=reply_markup)
    return CONFIRMATION

def confirm(update: Update, context: CallbackContext) -> int:
    """
    Handle the user's confirmation choice.
    If 'خیر' is clicked, cancel and end.
    If 'بله' is clicked, save the ad to the database and send the final message to the channel.
    """
    query = update.callback_query
    query.answer()

    choice = query.data  # "confirm_yes" or "confirm_no"

    if choice == "confirm_no":
        query.edit_message_text(MESSAGES["cancelled_no_send"])
        return ConversationHandler.END

    # If user clicked "بله":
    role         = context.user_data["role"]
    source       = context.user_data["source"]
    destination  = context.user_data["destination"]
    flight_date  = context.user_data["flight_date"]
    description  = context.user_data["description"]

    # Determine user's Telegram ID or username again
    user = update.effective_user
    if user.username:
        tg_id = user.username
    else:
        tg_id = str(user.id)

    ad_data = {
        "role":        role,
        "source":      source,
        "destination": destination,
        "flight_date": flight_date,
        "description": description,
        "user_id":     tg_id,
    }

    # 1) Save to SQLite
    save_ad_to_db(ad_data)

    # 2) Format the final message from the template (includes user_id)
    final_text = MESSAGE_TEMPLATE.format(
        role=role,
        source=source,
        destination=destination,
        flight_date=flight_date,
        description=description,
        user_id=tg_id,
    )

    # 3) Send to the channel
    # Escape any MarkdownV2 special characters before sending
    safe_text = escape_markdown(final_text, version=2)
    context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=safe_text,
        parse_mode=ParseMode.MARKDOWN_V2
    )


    # 4) Notify the user
    query.edit_message_text(MESSAGES["success_posted"])
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    """
    If the user sends /cancel at any time, end the conversation.
    """
    update.message.reply_text(MESSAGES["operation_cancelled"])
    return ConversationHandler.END

# ----------------------------
# 8. Main function
# ----------------------------
def main():
    """
    Initialize the database, set up the Updater and Dispatcher,
    register handlers, and start polling.
    """
    # 1) Initialize SQLite (creates ads.db if needed)
    init_db()

    # 2) Create Updater & Dispatcher
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # 3) Define ConversationHandler and states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # State 0: user clicks inline button to choose role
            CHOOSING_ROLE: [
                CallbackQueryHandler(role_handler, pattern="^role_")
            ],
            # State 1: user sends text for source
            TYPING_SOURCE: [
                MessageHandler(Filters.text & ~Filters.command, type_source)
            ],
            # State 2: user sends text for destination
            TYPING_DESTINATION: [
                MessageHandler(Filters.text & ~Filters.command, type_destination)
            ],
            # State 3: user picks a date from the calendar
            SELECTING_DATE: [
                CallbackQueryHandler(select_date, pattern="^DAY-|^PREV-|^NEXT-|^IGNORE$")
            ],
            # State 4: user sends description text
            TYPING_DESCRIPTION: [
                MessageHandler(Filters.text & ~Filters.command, type_description)
            ],
            # State 5: user confirms or cancels
            CONFIRMATION: [
                CallbackQueryHandler(confirm, pattern="^confirm_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # 4) Start polling
    updater.start_polling()
    logger.info("Bot started, polling for updates...")
    updater.idle()

if __name__ == "__main__":
    main()
