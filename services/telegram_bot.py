"""
בוט טלגרם לשליחת התראות וניהול
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes
)

from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, 
    TIMEZONE, CHECK_INTERVAL_MINUTES
)
from models import Post, Database
from services.keywords import KeywordsMatcher
from utils.logger import get_logger

logger = get_logger(__name__)


class TelegramBot:
    """בוט טלגרם"""
    
    def __init__(self):
        self.app = None
        self.db = Database()
        self.post_model = Post(self.db)
        self.keywords_matcher = KeywordsMatcher()
        self.is_paused = False
    
    async def setup(self):
        """הגדרת הבוט"""
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # רישום handlers
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("groups", self.cmd_groups))
        self.app.add_handler(CommandHandler("keywords", self.cmd_keywords))
        self.app.add_handler(CommandHandler("pause", self.cmd_pause))
        self.app.add_handler(CommandHandler("resume", self.cmd_resume))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        
        # Callback handlers לכפתורים
        self.app.add_handler(
            CallbackQueryHandler(self.handle_callback)
        )
        
        logger.info("בוט טלגרם הוגדר בהצלחה")
    
    async def start(self):
        """הפעלת הבוט"""
        if not self.app:
            await self.setup()

        # Important: starting the Application alone does NOT start receiving updates.
        # We must start polling (or webhook) via the Updater to make commands like /start work.
        await self.app.initialize()
        await self.app.start()

        if not getattr(self.app, "updater", None):
            logger.warning("Telegram Application has no updater; incoming commands will not be received")
        else:
            await self.app.updater.start_polling(drop_pending_updates=True)

        logger.info("בוט טלגרם פועל (polling)")
    
    async def stop(self):
        """עצירת הבוט"""
        if self.app:
            if getattr(self.app, "updater", None):
                await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            logger.info("בוט טלגרם נעצר")
    
    # ===== פקודות =====
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /start"""
        message = (
            "🤖 *Facebook Leads Finder Bot*\n\n"
            "הבוט פעיל ומחפש לידים עבורך!\n\n"
            "📋 פקודות זמינות:\n"
            "/status - סטטיסטיקות\n"
            "/groups - קבוצות מנוטרות\n"
            "/keywords - מילות מפתח\n"
            "/pause - השהיית ניטור\n"
            "/resume - המשך ניטור\n"
            "/help - עזרה"
        )
        await update.message.reply_text(
            message, 
            parse_mode='Markdown'
        )
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /status"""
        stats = self.post_model.get_stats()
        
        status_emoji = "✅" if not self.is_paused else "⏸"
        status_text = "פעיל" if not self.is_paused else "מושהה"
        
        message = (
            f"{status_emoji} *סטטוס מערכת*\n\n"
            f"📊 *סטטיסטיקות פוסטים:*\n"
            f"• סה\"כ: {stats.get('total', 0)}\n"
            f"• חדשים: {stats.get('new', 0)}\n"
            f"• שמורים: {stats.get('saved', 0)}\n"
            f"• יצרתי קשר: {stats.get('contacted', 0)}\n"
            f"• לא רלוונטי: {stats.get('not_relevant', 0)}\n\n"
            f"⏰ *תדירות בדיקה:* כל {CHECK_INTERVAL_MINUTES} דקות\n"
            f"🔄 *סטטוס ניטור:* {status_text}"
        )
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown'
        )
    
    async def cmd_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /groups"""
        from config import FB_GROUPS
        
        message = "📍 *קבוצות מנוטרות:*\n\n"
        
        for idx, group_url in enumerate(FB_GROUPS, 1):
            # חילוץ שם מה-URL
            group_name = group_url.split('/')[-1] or f"קבוצה {idx}"
            message += f"{idx}. {group_name}\n"
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown'
        )
    
    async def cmd_keywords(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /keywords"""
        keywords_info = self.keywords_matcher.get_keywords_info()
        
        message = "🔑 *מילות מפתח:*\n\n"
        
        message += f"✅ *חיוביות* ({keywords_info['total_positive']}):\n"
        for kw in keywords_info['positive'][:10]:
            message += f"• {kw}\n"
        
        if keywords_info['total_positive'] > 10:
            message += f"... ועוד {keywords_info['total_positive'] - 10}\n"
        
        message += f"\n❌ *שליליות* ({keywords_info['total_negative']}):\n"
        for kw in keywords_info['negative'][:10]:
            message += f"• {kw}\n"
        
        if keywords_info['total_negative'] > 10:
            message += f"... ועוד {keywords_info['total_negative'] - 10}\n"
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown'
        )
    
    async def cmd_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /pause"""
        self.is_paused = True
        await update.message.reply_text(
            "⏸ הניטור הושהה. השתמש ב-/resume להמשך."
        )
    
    async def cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /resume"""
        self.is_paused = False
        await update.message.reply_text(
            "✅ הניטור התחדש!"
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת /help"""
        message = (
            "📚 *עזרה*\n\n"
            "*פקודות זמינות:*\n"
            "/start - התחלה\n"
            "/status - סטטיסטיקות מערכת\n"
            "/groups - רשימת קבוצות מנוטרות\n"
            "/keywords - מילות מפתח נוכחיות\n"
            "/pause - השהיית ניטור\n"
            "/resume - המשך ניטור\n"
            "/help - הודעה זו\n\n"
            "*כפתורי פעולה בהתראות:*\n"
            "🔗 פתח - פתיחת הפוסט בפייסבוק\n"
            "💾 שמור - שמירת הפוסט למעקב\n"
            "🗑 לא רלוונטי - סימון כלא רלוונטי"
        )
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown'
        )
    
    # ===== התראות =====
    
    async def send_new_post_alert(self, post_data: Dict):
        """שליחת התראה על פוסט חדש"""
        try:
            # יצירת הודעה מעוצבת
            message = self._format_post_message(post_data)
            
            # יצירת כפתורים
            keyboard = self._create_post_buttons(post_data)
            
            # שליחת ההודעה
            await self.app.bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown',
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            logger.info(f"התראה נשלחה על פוסט: {post_data['post_id']}")
            
        except Exception as e:
            logger.error(f"שגיאה בשליחת התראה: {e}")
    
    def _format_post_message(self, post_data: Dict) -> str:
        """עיצוב הודעת פוסט"""
        # חישוב זמן מאז הפרסום
        time_ago = self._get_time_ago(post_data.get('timestamp'))
        
        # חיתוך טקסט ארוך
        text = post_data['text']
        if len(text) > 300:
            text = text[:300] + "..."
        
        message = (
            "🔥 *פוסט חדש בפייסבוק!*\n\n"
            f"👤 {post_data['author']}\n"
            f"📍 קבוצה: {post_data['group_name']}\n\n"
            f"💬 \"{text}\"\n\n"
            f"⏰ פורסם: {time_ago}"
        )
        
        return message
    
    def _create_post_buttons(self, post_data: Dict) -> InlineKeyboardMarkup:
        """יצירת כפתורים לפוסט"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔗 פתח בפייסבוק", 
                    url=post_data['post_url']
                )
            ],
            [
                InlineKeyboardButton(
                    "💾 שמור", 
                    callback_data=f"save_{post_data['post_id']}"
                ),
                InlineKeyboardButton(
                    "🗑 לא רלוונטי", 
                    callback_data=f"not_relevant_{post_data['post_id']}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """טיפול בלחיצות על כפתורים"""
        query = update.callback_query
        await query.answer()
        
        # פירוק ה-callback_data
        action, post_id = query.data.split('_', 1)
        
        if action == "save":
            self.post_model.update_status(post_id, Post.STATUS_SAVED)
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("💾 הפוסט נשמר!")
            
        elif action == "not":  # not_relevant
            # צריך לטפל ב-not_relevant_POST_ID
            _, post_id = query.data.split('_', 2)[1:]
            self.post_model.update_status(post_id, Post.STATUS_NOT_RELEVANT)
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("🗑 הפוסט סומן כלא רלוונטי")
    
    def _get_time_ago(self, timestamp: Optional[datetime]) -> str:
        """חישוב זמן שעבר"""
        if not timestamp:
            return "לא ידוע"
        
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)
        
        # המרת timestamp ל-aware datetime
        if timestamp.tzinfo is None:
            timestamp = pytz.utc.localize(timestamp)
        timestamp = timestamp.astimezone(tz)
        
        delta = now - timestamp
        
        if delta < timedelta(minutes=1):
            return "לפני פחות מדקה"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f"לפני {minutes} דקות"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f"לפני {hours} שעות"
        else:
            days = delta.days
            return f"לפני {days} ימים"
