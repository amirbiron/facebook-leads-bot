# 🚀 התחלה מהירה - 5 דקות

## ⚡ פריסה על Render (מומלץ)

### 1. הכנה (5 דקות)

#### א. MongoDB
1. היכנס ל-[MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. לחץ "Build a Database" → "Free" → "Create"
3. בחר שם למשתמש וסיסמה
4. לחץ "Create User"
5. ב-"Where would you like to connect from?" → "Add My Current IP Address"
6. לחץ "Finish and Close"
7. לחץ "Connect" → "Connect your application"
8. העתק את ה-Connection String (שים לב להחליף `<password>`)

#### ב. Telegram Bot
1. פתח את [@BotFather](https://t.me/botfather) בטלגרם
2. שלח: `/newbot`
3. בחר שם: `My Leads Finder Bot`
4. בחר username: `myleadsfinder_bot`
5. העתק את ה-**Token**

#### ג. Chat ID
1. שלח הודעה כלשהי לבוט החדש שלך
2. פתח בדפדפן:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
3. חפש `"chat":{"id":123456789` והעתק את המספר

#### ד. חשבון פייסבוק
1. צור חשבון פייסבוק חדש (לא האישי!)
2. הצטרף לקבוצות רלוונטיות
3. העתק את ה-URL של כל קבוצה

### 2. פריסה על Render (2 דקות)

1. Fork/העלה את הקוד ל-GitHub
2. היכנס ל-[Render](https://render.com)
3. לחץ "New +" → "Background Worker"
4. חבר את ה-repository
5. Render יזהה את `render.yaml` אוטומטית
6. הוסף Environment Variables:

```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=987654321
MONGODB_URI=mongodb+srv://user:pass@cluster...
FB_EMAIL=bot@example.com
FB_PASSWORD=password123
FB_GROUPS=https://facebook.com/groups/group1,https://facebook.com/groups/group2
POSITIVE_KEYWORDS=מחפש מפתח,דרוש מפתח,צריך בוט,אוטומציה
NEGATIVE_KEYWORDS=בחינם,התנדבות,סטודנט
```

7. לחץ "Create Background Worker"
8. המתן ~5 דקות לבנייה

### 3. בדיקה (1 דקה)

1. פתח את הבוט בטלגרם
2. שלח: `/start`
3. אמור לקבל: "🤖 Facebook Leads Finder Bot"
4. שלח: `/status`
5. אמור לראות סטטיסטיקות

### 4. המתן ללידים! 🎉

הבוט יתחיל לסרוק אוטומטית כל 3 שעות.
כשימצא פוסט רלוונטי - תקבל התראה!

---

## 🔧 התאמות מומלצות

### מילות מפתח לפי תחום

**פיתוח בוטים:**
```
POSITIVE_KEYWORDS=בוט,bot,טלגרם בוט,telegram bot,אוטומציה,automation,מפתח בוט
```

**פיתוח web:**
```
POSITIVE_KEYWORDS=אתר,website,פיתוח אתר,web developer,דרוש מפתח,מחפש מפתח
```

**כללי:**
```
POSITIVE_KEYWORDS=מחפש מפתח,דרוש מפתח,צריך בוט,מישהו יודע לעשות,עזרה בפיתוח,פייתון,python
```

### קבוצות מומלצות

- פרילנסרים ישראל
- עסקים קטנים ובינוניים
- סטארטאפים ישראלים
- דרושים טכנולוגיה
- קהילת המפתחים

---

## 📱 שימוש בבוט

### פקודות יומיומיות

```
/status     - מה קורה? כמה לידים?
/pause      - אני עסוק, תפסיק לסרוק
/resume     - המשך לעבוד!
```

### כשמגיעה התראה

```
🔥 פוסט חדש בפייסבוק!

👤 ישראל ישראלי
📍 קבוצה: פרילנסרים ישראל

💬 "מחפש מפתח שיכול לבנות בוט..."

⏰ פורסם: לפני 3 דקות

[🔗 פתח בפייסבוק] [💾 שמור] [🗑 לא רלוונטי]
```

**מה לעשות:**
1. לחץ "פתח בפייסבוק"
2. קרא את הפוסט המלא
3. אם רלוונטי - הגב מהר!
4. לחץ "שמור" או "לא רלוונטי"

---

## ⚠️ טיפים חשובים

### ✅ כדאי
- השתמש בחשבון פייסבוק נפרד
- התחבר לחשבון לפחות פעם ביום ידנית
- בדוק שהקבוצות פעילות
- התאם מילות מפתח לפי התוצאות

### ❌ לא כדאי
- להשתמש בחשבון האישי
- להגדיר יותר מדי קבוצות בבת אחת
- להפעיל `HEADLESS_MODE=false` ב-Render (יקר!)
- לספאם את הקבוצות

---

## 🐛 בעיות נפוצות

### לא מקבל התראות?
1. בדוק Logs ב-Render
2. שלח `/status` - רואה פוסטים חדשים?
3. בדוק שמילות המפתח נכונות

### "MongoDB connection error"?
1. בדוק את ה-Connection String
2. ב-MongoDB Atlas → Network Access → Add IP: `0.0.0.0/0`

### "Telegram Unauthorized"?
1. בדוק שה-Token נכון
2. וודא שאין רווחים לפני/אחרי ב-Environment Variables

---

**זה הכל! תהנה מלידים חדשים! 🎯**
