import requests
import re
import os
import logging
import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Read from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("TELEGRAM_TOKEN and CHAT_ID environment variables must be set")

application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
bot = application.bot

last_version = None  # Global variable to store the last known version
last_heartbeat_date = datetime.min

async def broadcast(text):
    chat_ids = CHAT_ID.split('|')
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id=chat_id.strip(), text=text)
        except Exception as e:
            logger.warning(f"❌ Gửi thất bại đến {chat_id.strip()}: {e}")


def extract_version_from_text(text):
    """Extract app version from HTML using regex"""
    match = re.search(r'"softwareVersion"\s*:\s*"([^"]+)"', text)
    if match:
        return match.group(1)
    return None


async def get_mcdonalds_app_version():
    """Check current version and notify if updated"""
    global last_version, last_heartbeat_date
    url = "https://apkcombo.com/vi/mcdonald-s/com.mcdonalds.mobileapp/"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

        #await broadcast(text=f"✅ Checking McDonald's App version... (current: {last_version})")

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        version_info = extract_version_from_text(response.text)

        if version_info:
            version = version_info.strip()
            #await broadcast(text=f"🔍 Version Found: {version}")

            if version != last_version:
                if last_version is not None:
                    message = (
                        f"⚠️ McDonald's App Version Đã thay đổi!\n"
                        f"Old Version: {last_version}\n"
                        f"New Version: {version}"
                    )
                    await broadcast(text=message)

                else:
                    await broadcast(f"🚀 Bot đã khởi động. Version hiện tại: {version}")

                logger.info(f"New version detected: {version}")
                last_version = version
            else:
                logger.info("No version change.")
        else:
            logger.warning("Could not extract version from response.")

        # ✅ Gửi heartbeat nếu đã hơn 1h kể từ lần cuối
        now = datetime.now()
        if now - last_heartbeat_date >= timedelta(hours=12):
            await broadcast(f"✅ Bot vẫn đang hoạt động. Phiên bản hiện tại: {last_version}")
            last_heartbeat_date = now

    except Exception as e:
        logger.error(f"Error fetching McDonald's app version: {e}")
        await broadcast(text=f"❌ Error: {e}")


async def main():
    logger.info("🚀 Starting McDonald's App version checker...")

    # Initial check
    await get_mcdonalds_app_version()

    # Start async scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(get_mcdonalds_app_version, 'interval', minutes=1)
    scheduler.start()
    logger.info("Scheduler started.")

    # Keep running
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.wait_for_stop()


if __name__ == '__main__':
    asyncio.run(main())
