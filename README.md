# 001-Telegram-Bot

A simple Telegram bot to post flight and cargo ads to a channel via an interactive conversation flow. Built with Python, SQLite, and fully containerized with Docker.

## 🎯 Features

* **Role Selection**: Choose between *Passenger* (`مسافر هستم`) or *Cargo* (`بار برای حمل دارم`).
* **Interactive Inputs**: Enter source, destination, and description through conversational prompts.
* **Inline Calendar**: Select your flight date using a calendar UI.
* **Ad Preview**: View a formatted preview before confirming.
* **Persistent Storage**: Ads are saved in a local SQLite database (`ads.db`).
* **Channel Posting**: On confirmation, ads are sent to your configured Telegram channel.

## 📁 Project Structure

```
001-telegram-bot/
├── .dockerignore           # Docker ignore rules
├── .env.example            # Example environment variables (rename to .env)
├── .gitignore
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose setup
├── LICENSE
├── README.md               # ← You are here
├── README_fa.md            # Farsi README
├── ads.db                  # SQLite database (auto-created)
├── bot.py                  # Main bot application
├── install.bat             # Windows installer script
├── message_template.txt    # Final message template
├── messages.json           # Bot UI and error messages
├── preview_template.txt    # Ad preview template
├── requirements.txt        # Python dependencies
└── ads.db                  # SQLite file (auto-created)
```

> ℹ️ `folder_hierarchy.txt` has been removed from the project; it is no longer part of the repository.

## 🚀 Prerequisites

* **Python 3.8+** (if running locally)
* **Docker & Docker Compose** (for containerized setup)

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/001-telegram-bot.git
cd 001-telegram-bot
```

### 2. Configuration

1. Rename `.env.example` to `.env`:

   ```bash
   mv .env.example .env
   ```
2. Open `.env` and set:

   ```ini
   BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
   CHANNEL_ID=YOUR_CHANNEL_ID  # e.g., -1001234567890 or @your_channel
   DB_PATH=ads.db              # Path to SQLite DB (default: ads.db)
   ```

> ⚠️ The `.env` file is not tracked by Git. Do **not** commit your real tokens.

### 3. Windows Installation

Double-click or run from PowerShell:

```powershell
.\\install.bat
```

This will set up a virtual environment and install dependencies.

### 4. Ubuntu / Linux Installation

*(Coming soon in `install.sh`.)*

## 🏃 Usage

### Local (Python)

```bash
# Activate your venv (Windows PowerShell example):
.\"venv\Scripts\Activate.ps1
# Or on Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python bot.py
```

### Docker & Docker Compose

```bash
docker-compose up -d --build
```

Your bot will start and connect to Telegram via your configured token.

## 🔧 Customization

* **Message Templates**: Edit `preview_template.txt` and `message_template.txt` to change the ad format.
* **Bot Messages**: Modify `messages.json` for UI text, prompts, and error messages.
* **Logic Changes**: For new conversation flows or commands, feel free to request custom logic by emailing me.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 📬 Contact

For feature requests, custom logic, or questions, email: **[amdkna@gmail.com](mailto:amdkna@gmail.com)**
