"""
Facebook Leads Finder Bot
מערכת לחיפוש לידים מפייסבוק
"""
import asyncio
from datetime import datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import (
    config,
    CHECK_INTERVAL_MINUTES,
    TIMEZONE,
    QUIET_HOURS_START,
    QUIET_HOURS_END,
)
from models import Database, Post, Group
from services import FacebookScraper, KeywordsMatcher, TelegramBot
from utils.logger import get_logger

logger = get_logger(__name__)


class LeadsFinder:
    """המערכת הראשית"""
    
    def __init__(self):
        self.db = Database()
        self.post_model = Post(self.db)
        self.group_model = Group(self.db)
        self.scraper = FacebookScraper()
        self.keywords_matcher = KeywordsMatcher()
        self.telegram_bot = TelegramBot()
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    async def startup(self):
        """הפעלת המערכת"""
        try:
            logger.info("🚀 מתחיל הפעלת המערכת...")
            
            # בדיקת הגדרות
            config.validate_config()
            logger.info("✅ הגדרות תקינות")
            
            # התחברות למונגו
            self.db.connect()
            logger.info("✅ התחברות למונגו הצליחה")
            
            # הפעלת בוט טלגרם
            await self.telegram_bot.start()
            logger.info("✅ בוט טלגרם פועל")
            
            # הפעלת scheduler
            self.scheduler.add_job(
                self.scan_cycle,
                trigger=IntervalTrigger(minutes=CHECK_INTERVAL_MINUTES),
                id='scan_job',
                name='Facebook Scan',
                replace_existing=True
            )
            self.scheduler.start()
            logger.info(f"✅ Scheduler מוגדר לריצה כל {CHECK_INTERVAL_MINUTES} דקות")
            
            # ריצה ראשונה מיידית
            logger.info("▶️ מריץ סריקה ראשונית...")
            await self.scan_cycle()
            
            self.is_running = True
            logger.info("🎉 המערכת פועלת!")
            
        except Exception as e:
            logger.error(f"❌ שגיאה בהפעלת המערכת: {e}")
            raise
    
    async def scan_cycle(self):
        """מחזור סריקה אחד"""
        try:
            # Skip scanning during quiet hours (local time)
            tz = pytz.timezone(TIMEZONE)
            now_local = datetime.now(tz)
            start_h = QUIET_HOURS_START
            end_h = QUIET_HOURS_END
            in_quiet_hours = (
                (start_h < end_h and start_h <= now_local.hour < end_h)
                or (start_h > end_h and (now_local.hour >= start_h or now_local.hour < end_h))
            )
            if in_quiet_hours:
                logger.info(
                    f"🌙 שעות שקטות ({TIMEZONE}) {start_h:02d}:00-{end_h:02d}:00 - מדלג על סריקה (עכשיו {now_local:%H:%M})"
                )
                return

            if self.telegram_bot.is_paused:
                logger.info("⏸ הניטור מושהה - מדלג על הסריקה")
                return
            
            logger.info("=" * 50)
            logger.info(f"🔍 מתחיל מחזור סריקה - {now_local}")
            logger.info("=" * 50)
            
            # סריקת פייסבוק
            logger.info("📱 סורק קבוצות בפייסבוק...")
            all_posts = self.scraper.scrape_all_groups()
            logger.info(f"נמצאו {len(all_posts)} פוסטים סה\"כ")
            
            new_leads_count = 0
            
            # עיבוד פוסטים
            for post_data in all_posts:
                try:
                    # בדיקה אם כבר ראינו את הפוסט
                    if self.post_model.exists(post_data['post_id']):
                        logger.debug(f"פוסט {post_data['post_id']} כבר קיים")
                        continue
                    
                    # בדיקת רלוונטיות לפי keywords
                    match_result = self.keywords_matcher.is_relevant(
                        post_data['text']
                    )
                    
                    if not match_result['is_relevant']:
                        logger.debug("פוסט לא רלוונטי - מדלג")
                        continue
                    
                    # פוסט רלוונטי וחדש!
                    logger.info(f"🎯 פוסט רלוונטי חדש נמצא!")
                    
                    # שמירה במסד נתונים
                    post_id = self.post_model.create(post_data)
                    
                    if post_id:
                        # שליחת התראה לטלגרם
                        await self.telegram_bot.send_new_post_alert(post_data)
                        new_leads_count += 1
                        logger.info(f"✅ פוסט נשמר והתראה נשלחה")
                    
                except Exception as e:
                    logger.error(f"שגיאה בעיבוד פוסט: {e}")
                    continue
            
            logger.info("=" * 50)
            logger.info(f"✨ מחזור הסתיים - נמצאו {new_leads_count} לידים חדשים")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"❌ שגיאה במחזור סריקה: {e}")
    
    async def shutdown(self):
        """כיבוי מסודר"""
        logger.info("🛑 מכבה את המערכת...")
        
        self.is_running = False
        
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("✅ Scheduler נכבה")
        
        await self.telegram_bot.stop()
        logger.info("✅ בוט טלגרם נעצר")
        
        self.db.close()
        logger.info("✅ חיבור למונגו נסגר")
        
        logger.info("👋 המערכת כובתה")
    
    async def run_forever(self):
        """ריצה רציפה"""
        await self.startup()
        
        try:
            # שמירה על התהליך חי
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n⚠️ התקבל אות להפסקה")
        finally:
            await self.shutdown()


async def main():
    """נקודת כניסה ראשית"""
    finder = LeadsFinder()
    await finder.run_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 יציאה")
    except Exception as e:
        logger.error(f"❌ שגיאה קריטית: {e}")
        raise
