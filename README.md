# 🤖 Facebook Leads Finder Bot

מערכת אוטומטית לחיפוש לידים מקבוצות פייסבוק ישראליות עם התראות בזמן אמת לטלגרם.

## 🎯 מה המערכת עושה?

- 🔍 סורקת קבוצות פייסבוק שהגדרת כל 30-60 דקות
- 🎯 מזהה פוסטים של אנשים שמחפשים מפתחים/בוטים לפי מילות מפתח
- 📱 שולחת התראה מיידית לטלגרם עם כפתורי פעולה
- 💾 שומרת הכל במונגו למעקב
- 🔐 Anti-detection - התנהגות דמוית אדם

## 📋 דרישות

- Python 3.11+
- MongoDB (MongoDB Atlas מומלץ)
- Telegram Bot Token
- חשבון פייסבוק נפרד (לא האישי!)
- Render Account (לפריסה)

## ⚡ התקנה מהירה

### 1. שכפול הפרויקט
```bash
git clone <repository-url>
cd facebook-leads-bot
```

### 2. התקנת תלויות (לפיתוח מקומי)
```bash
pip install -r requirements.txt
```

### 3. הגדרת משתני סביבה
העתק את `.env.example` ל-`.env` ומלא את הפרטים:

```bash
cp .env.example .env
```

ערוך את `.env`:
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=987654321

# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=facebook_leads

# Facebook Account (חשבון נפרד!)
FB_EMAIL=bot_account@example.com
FB_PASSWORD=your_secure_password

# Groups to Monitor
FB_GROUPS=https://www.facebook.com/groups/freelancers-israel,https://www.facebook.com/groups/tech-jobs

# Keywords
POSITIVE_KEYWORDS=מחפש מפתח,דרוש מפתח,צריך בוט,טלגרם בוט,אוטומציה,פייתון
NEGATIVE_KEYWORDS=בחינם,התנדבות,סטודנט,עיצוב גרפי
```

## 🚀 הפעלה על Render

### שלב 1: יצירת MongoDB
1. צור חשבון ב-[MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. צור Cluster חינמי
3. העתק את ה-Connection String
4. הוסף את ה-IP של Render לרשימת ההיתרים (או 0.0.0.0/0 לפיתוח)

### שלב 2: יצירת Telegram Bot
1. שלח `/newbot` ל-[@BotFather](https://t.me/botfather)
2. בחר שם לבוט
3. העתק את ה-Token
4. לקבלת Chat ID: שלח הודעה לבוט שלך ואז פתח:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```

### שלב 3: פריסה על Render
1. צור חשבון ב-[Render](https://render.com)
2. לחץ "New +" → "Background Worker"
3. חבר את ה-GitHub repository
4. Render יזהה את `render.yaml` אוטומטית
5. הוסף את משתני הסביבה:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `MONGODB_URI`
   - `FB_EMAIL`
   - `FB_PASSWORD`
   - `FB_GROUPS`
   - `POSITIVE_KEYWORDS`
   - `NEGATIVE_KEYWORDS`
6. לחץ "Create Background Worker"

### שלב 4: בדיקה
שלח `/start` לבוט בטלגרם - אמור לקבל הודעת קבלה.

## 📱 פקודות זמינות בבוט

```
/start - התחלה
/status - סטטיסטיקות ומצב המערכת
/groups - קבוצות מנוטרות
/keywords - מילות מפתח נוכחיות
/pause - השהיית הניטור
/resume - המשך ניטור
/help - עזרה
```

## 🔧 התאמה אישית

### שינוי תדירות הסריקה
ב-`.env`:
```env
CHECK_INTERVAL_MINUTES=45  # כל 45 דקות
```

### הוספת מילות מפתח
ב-`.env`:
```env
POSITIVE_KEYWORDS=מחפש מפתח,דרוש מפתח,... (הוסף עוד)
NEGATIVE_KEYWORDS=בחינם,התנדבות,... (הוסף עוד)
```

### הוספת קבוצות נוספות
ב-`.env`:
```env
FB_GROUPS=url1,url2,url3  # הפרד בפסיקים
```

## ⚙️ הפעלה מקומית (פיתוח)

```bash
# התקנת תלויות
pip install -r requirements.txt

# הפעלה
python main.py
```

**שים לב:** להפעלה מקומית צריך Chrome מותקן.

## 🔒 אבטחה והגנה

### ⚠️ חשוב מאוד!

1. **חשבון פייסבוק נפרד**
   - אל תשתמש בחשבון האישי שלך
   - צור חשבון חדש ונפרד עבור הבוט

2. **התנהגות זהירה**
   - הבוט רץ עם `HEADLESS_MODE=true` ב-Render
   - יש המתנות אקראיות בין פעולות
   - גלילה איטית ודמוית אדם
   - בודק רק 1-2 קבוצות בכל ריצה

3. **Rate Limiting**
   - ברירת מחדל: כל 45 דקות
   - אפשר להגדיל ל-60 דקות לבטיחות נוספת

4. **IP ומיקום**
   - Render משתמש ב-IP אמריקאי
   - עדיף להשתמש בחשבון פייסבוק שהתחבר מארה"ב

## 📊 מבנה הפרויקט

```
facebook-leads-bot/
├── config/              # הגדרות
│   ├── __init__.py
│   └── config.py
├── models/              # מודלים למסד נתונים
│   ├── __init__.py
│   └── database.py
├── services/            # שירותים עיקריים
│   ├── __init__.py
│   ├── scraper.py       # סקרייפר פייסבוק
│   ├── keywords.py      # התאמת מילות מפתח
│   └── telegram_bot.py  # בוט טלגרם
├── utils/               # כלי עזר
│   ├── __init__.py
│   └── logger.py
├── main.py              # נקודת כניסה ראשית
├── requirements.txt     # תלויות
├── Dockerfile          # לפריסה
├── render.yaml         # הגדרות Render
└── README.md
```

## 🐛 פתרון בעיות

### הבוט לא מגיב
1. בדוק שה-Token נכון ב-Render Environment Variables
2. שלח `/start` לבוט
3. בדוק Logs ב-Render

### אין התראות על פוסטים
1. בדוק ב-Logs אם יש שגיאות
2. וודא שהקבוצות נכונות ב-`FB_GROUPS`
3. בדוק שמילות המפתח רלוונטיות

### התחברות לפייסבוק נכשלת
1. וודא שהפרטים נכונים
2. נסה להתחבר מהחשבון ידנית מ-IP אמריקאי
3. ייתכן שפייסבוק דורשת אימות - התחבר ידנית

### MongoDB Connection Error
1. בדוק שה-Connection String נכון
2. וודא שה-IP של Render מותר ב-Network Access
3. או הוסף `0.0.0.0/0` (לא מומלץ לפרודקשן אמיתי)

## 📈 שיפורים עתידיים

- [ ] Dashboard Web מלא
- [ ] מערכת Scoring לפוסטים
- [ ] ניהול Keywords דינמי דרך הבוט
- [ ] תמיכה ב-Instagram
- [ ] API לאינטגרציה עם CRM
- [ ] בדיקת היסטוריה ב-WhatsApp

## ⚖️ תנאי שימוש

- השימוש במערכת הוא באחריותך בלבד
- פייסבוק לא מעודד scraping - השתמש בזהירות
- המערכת ליעדים אישיים בלבד
- אל תפרסם מידע רגיש מהפוסטים

## 📞 תמיכה

אם נתקלת בבעיה או צריך עזרה, פתח Issue ב-GitHub.

## 📄 רישיון

MIT License - עשה מה שאתה רוצה, באחריותך.

---

**בהצלחה! 🚀**
