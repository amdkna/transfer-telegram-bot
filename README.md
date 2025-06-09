# Telegram Travel Ads Bot

This repository contains a Telegram bot that allows users to post travel-related ads (either as a passenger or cargo) via a multi-step conversation. The bot stores the ad in a SQLite database and publishes a formatted message to a specified channel.

---

## Prerequisites

- Python 3.8 or higher
- A Telegram bot token (from @BotFather)
- A Telegram channel (public or private) where the bot has permission to post
- Docker and Docker Compose (optional, if you want to run the bot in a container)

---

## Files and Structure

```
.
├── bot.py
├── preview_template.txt
├── message_template.txt
├── requirements.txt
├── .env
├── ads.db              # (created automatically)
└── README.md
```

1. **bot.py**  
   Main Python script implementing the bot logic.

2. **preview_template.txt**  
   Template for showing the user a preview of their ad before final confirmation.  
   Placeholders:

   - `{role}`        : "مسافر" or "بار دارم"
   - `{source}`      : The text the user entered for source (کشور، شهر)
   - `{destination}` : The text the user entered for destination (کشور، شهر)
   - `{flight_date}` : Selected flight date (YYYY-MM-DD)
   - `{description}` : User’s description (or "ندارد")
   - `{user_id}`     : Telegram username (without @) or numeric ID

   **Example contents of `preview_template.txt`:**
   ```
   📢 پیش‌نمایش آگهی شما:

   • نوع حمل: {role}
   • مبدا: {source}
   • مقصد: {destination}
   • تاریخ پرواز: {flight_date}
   • توضیحات: {description}

   تماس: @{user_id}

   آیا از ارسال این آگهی مطمئن هستید؟
   ```

3. **message_template.txt**  
   Template for the final message posted to the channel.  
   Placeholders are identical to `preview_template.txt`.

   **Example contents of `message_template.txt`:**
   ```
   #{role}
   🛫 مبدا: {source}
   🛬 مقصد: {destination}
   ✈️  تاریخ پرواز: {flight_date}
   توضیحات:
   {description}

   📞 تماس: @{user_id}
   ```

4. **requirements.txt**  
   Python dependencies:
   ```
   python-telegram-bot==13.15
   python-dotenv==1.0.0
   pytz==2025.1
   ```

5. **.env**  
   Environment variables (example):
   ```
   BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ
   CHANNEL_ID=-1001234567890
   DB_PATH=ads.db
   ```

   - `BOT_TOKEN`: Your Telegram bot API token (retrieved from @BotFather).
   - `CHANNEL_ID`: The ID or username of the channel where ads are posted (e.g., `-1001234567890` or `@my_channel`).
   - `DB_PATH`  : (Optional) Path to the SQLite database file (default is `ads.db`).

6. **ads.db**  
   SQLite database file that is created automatically on first run. It contains a table `ads` with columns:
   - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
   - `role` (TEXT)
   - `source` (TEXT)
   - `destination` (TEXT)
   - `flight_date` (TEXT, format `YYYY-MM-DD`)
   - `description` (TEXT)
   - `created_at` (TIMESTAMP default CURRENT_TIMESTAMP)

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root (if not already present) with:

```
BOT_TOKEN=your_bot_token_here
CHANNEL_ID=your_channel_id_here
DB_PATH=ads.db
```

Ensure that the bot has permission to post in the specified channel (add the bot as an admin or give it posting rights).

### 3. Prepare template files

- **preview_template.txt**:  
  Must contain exactly the placeholders `{role}`, `{source}`, `{destination}`, `{flight_date}`, `{description}`, and `{user_id}`.  
  Example:
  ```
  📢 پیش‌نمایش آگهی شما:

  • نوع حمل: {role}
  • مبدا: {source}
  • مقصد: {destination}
  • تاریخ پرواز: {flight_date}
  • توضیحات: {description}

  تماس: @{user_id}

  آیا از ارسال این آگهی مطمئن هستید؟
  ```

- **message_template.txt**:  
  Must also contain the same placeholders.  
  Example:
  ```
  #{role}
  🛫 مبدا: {source}
  🛬 مقصد: {destination}
  ✈️  تاریخ پرواز: {flight_date}
  توضیحات:
  {description}

  📞 تماس: @{user_id}
  ```

You can modify or localize the templates freely as long as you keep the placeholders unchanged.

### 4. Run the bot

```bash
python bot.py
```

The bot will:

1. Initialize the SQLite database (`ads.db`) and create the `ads` table if it does not exist.
2. Start polling Telegram for updates.
3. When a user sends `/start`, walk them through:
   - Choosing “مسافر” or “بار دارم” (Passenger or Cargo)
   - Typing source (کشور، شهر)
   - Typing destination (کشور، شهر)
   - Selecting a flight date from an inline calendar (past dates are disabled)
   - Typing a description (or “ندارد” if none)
   - Viewing a preview of the ad (`preview_template.txt`), including their @username or ID
   - Confirming (بله) or canceling (خیر)

If confirmed, the ad is saved to `ads.db`, formatted with `message_template.txt`, and sent to the specified channel. The user then receives a “✅ آگهی شما در کانال منتشر شد. متشکریم!” message.

---

## Docker (Optional)

If you prefer to run the bot inside Docker:

1. Create a `Dockerfile`:

   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   CMD ["python", "bot.py"]
   ```

2. Create or update `docker-compose.yml`:

   ```yaml
   version: "3.8"

   services:
     telegram_bot:
       build: .
       env_file:
         - .env
       volumes:
         - ./ads.db:/app/ads.db
       restart: unless-stopped
   ```

3. Build and run:

   ```bash
   docker-compose build
   docker-compose up -d
   ```

---

## Customization

- **Add more fields**:  
  - Extend `context.user_data` with new keys (e.g., `"weight"`, `"price"`).  
  - Update both `preview_template.txt` and `message_template.txt` by adding new placeholders (e.g., `{weight}` or `{price}`).  
  - Adjust the Python code where `type_description()` builds `preview_text` and where `confirm()` builds `final_text`, to pass the additional fields into `.format()`.

- **Localization**:  
  - All user-facing messages in `bot.py` are in Persian. To support English or another language, extract text into a dictionary keyed by language code and select based on user preference.

- **Admin commands**:  
  - You can add handlers for commands like `/stats` or `/recent` that query the SQLite database and return summaries.

---

## License

MIT License
