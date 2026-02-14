"""
הגדרות ראשיות של המערכת
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# MongoDB
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'facebook_leads')

# Facebook
FB_EMAIL = os.getenv('FB_EMAIL')
FB_PASSWORD = os.getenv('FB_PASSWORD')
FB_GROUPS = os.getenv('FB_GROUPS', '').split(',')

# Scraper
CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', 180))
POSTS_PER_GROUP = int(os.getenv('POSTS_PER_GROUP', 10))
GROUPS_PER_CYCLE = int(os.getenv('GROUPS_PER_CYCLE', 5))
QUIET_HOURS_START = int(os.getenv('QUIET_HOURS_START', 2))  # 02:00
QUIET_HOURS_END = int(os.getenv('QUIET_HOURS_END', 7))      # 07:00
HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'

# Keywords
POSITIVE_KEYWORDS = [
    kw.strip() for kw in os.getenv('POSITIVE_KEYWORDS', '').split(',') if kw.strip()
]
NEGATIVE_KEYWORDS = [
    kw.strip() for kw in os.getenv('NEGATIVE_KEYWORDS', '').split(',') if kw.strip()
]

# General
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Jerusalem')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Validation
def validate_config():
    """בדיקת תקינות הגדרות"""
    errors = []
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("חסר TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        errors.append("חסר TELEGRAM_CHAT_ID")
    if not MONGODB_URI:
        errors.append("חסר MONGODB_URI")
    if not FB_EMAIL:
        errors.append("חסר FB_EMAIL")
    if not FB_PASSWORD:
        errors.append("חסר FB_PASSWORD")
    if not FB_GROUPS or FB_GROUPS == ['']:
        errors.append("חסר FB_GROUPS")
    if not POSITIVE_KEYWORDS:
        errors.append("חסר POSITIVE_KEYWORDS")

    # Quiet hours validation (local time in TIMEZONE)
    if not (0 <= QUIET_HOURS_START <= 23):
        errors.append("QUIET_HOURS_START חייב להיות בין 0 ל-23")
    if not (0 <= QUIET_HOURS_END <= 23):
        errors.append("QUIET_HOURS_END חייב להיות בין 0 ל-23")
    
    if errors:
        raise ValueError(f"שגיאות בהגדרות:\n" + "\n".join(errors))
    
    return True
