import requests
import re
import os
import logging
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
import time

# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Read from environment
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHATID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("BOT_TOKEN and CHATID environment variables must be set")

bot = Bot(token=TELEGRAM_TOKEN)
last_version = None  # Global variable to store the last known version


def extract_version_from_text(text):
    """Extract app version from HTML using regex"""
    match = re.search(r'"softwareVersion"\s*:\s*"([^"]+)"', text)
    if match:
        return match.group(1)
    return None


def get_mcdonalds_app_version():
    """Check current version and notify if updated"""
    global last_version
    url = "https://apkcombo.com/vi/mcdonald-s/com.mcdonalds.mobileapp/"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

        bot.send_message(chat_id=CHAT_ID, text=f"✅ Checking McDonald's App version... (current: {last_version})")

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        version_info = extract_version_from_text(response.text)

        if version_info:
            version = version_info.strip()
            bot.send_message(chat_id=CHAT_ID, text=f"🔍 Version Found: {version}")

            if version != last_version:
                if last_version is not None:
                    message = (
                        f"⚠️ McDonald's App Version Changed!\n"
                        f"Old Version: {last_version}\n"
                        f"New Version: {version}"
                    )
                    bot.send_message(chat_id=CHAT_ID, text=message)

                logger.info(f"New version detected: {version}")
                last_version = version
            else:
                logger.info("No version change.")
        else:
            logger.warning("Could not extract version from response.")

    except Exception as e:
        logger.error(f"Error fetching McDonald's app version: {e}")
        bot.send_message(chat_id=CHAT_ID, text=f"❌ Error: {e}")


def start_scheduler():
    """Start periodic check scheduler"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(get_mcdonalds_app_version, 'interval', minutes=1)  # check every 1 minute
    scheduler.start()
    logger.info("Scheduler started.")


def main():
    logger.info("🚀 Starting McDonald's App version checker...")
    get_mcdonalds_app_version()
    start_scheduler()

    while True:
        time.sleep(60)


if __name__ == '__main__':
    main()
