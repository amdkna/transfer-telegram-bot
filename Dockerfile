# ---------- Dockerfile ----------

# 1) Use official Python 3.11 slim image
FROM python:3.11-slim

# 2) Set environment variables to avoid Python buffering and bytecode files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 3) Create and switch to application directory
WORKDIR /app

# 4) Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5) Copy application code and templates
COPY bot.py /app/
COPY message_template.txt /app/
COPY preview_template.txt /app/
COPY messages.json /app/
COPY .env /app/

# 6) Create a folder for persistent data (SQLite DB)
RUN mkdir -p /data

# 7) No ports need exposing (bot uses polling)

# 8) Launch the bot
CMD ["python", "bot.py"]
