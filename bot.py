import requests
import re
import logging
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
import time

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token from @BotFather
TELEGRAM_TOKEN = "7864653740:AAHurlXDx8zskTzQV2e8_ESo0SXFE3_bH8Q"
CHAT_ID = "1116300387"

bot = Bot(token=TELEGRAM_TOKEN)

# Global variable to store the last known version
last_version = None


def extract_version_from_text(text):
    """Tìm phiên bản ứng dụng từ HTML bằng regex"""
    match = re.search(r'"softwareVersion"\s*:\s*"([^"]+)"', text)
    if match:
        return match.group(1)
    return None


def get_mcdonalds_app_version():
    """Kiểm tra phiên bản hiện tại và gửi thông báo nếu có cập nhật"""
    global last_version
    url = "https://apkcombo.com/vi/mcdonald-s/com.mcdonalds.mobileapp/"

    try:
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        bot.send_message(chat_id=CHAT_ID, text="Version Now: {last_version}")
        bot.send_message(chat_id=CHAT_ID, text="Checking Version of MCDonals App...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        version_info = extract_version_from_text(response.text)

        if version_info:
            version = version_info.strip()
            bot.send_message(chat_id=CHAT_ID, text="Version Found: {version}")
            
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
                return version
            else:
                logger.info(f"No version change. Current version: {version}")
        else:
            logger.warning("Could not extract version from response.")

    except Exception as e:
        logger.error(f"Error fetching McDonald's app version: {e}")

    return None


def start_scheduler():
    """Khởi động lịch kiểm tra định kỳ"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(get_mcdonalds_app_version, 'interval', minutes=1)  # kiểm tra mỗi 10 phút
    scheduler.start()
    logger.info("Scheduler started.")


def main():
    logger.info("Starting McDonald's app version checker...")
    get_mcdonalds_app_version()  # initial check
    start_scheduler()

    # Keep the script running
    while True:
        time.sleep(60)


if __name__ == '__main__':
    main()
