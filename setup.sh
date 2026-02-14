#!/bin/bash

echo "🚀 Facebook Leads Finder Bot - Setup Script"
echo "============================================"
echo ""

# Check Python version
echo "📋 בודק גרסת Python..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.11"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "❌ נדרש Python $required_version ומעלה, נמצא $python_version"
    exit 1
fi
echo "✅ Python $python_version"

# Create virtual environment
echo ""
echo "🔧 יוצר סביבה וירטואלית..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ סביבה וירטואלית נוצרה"
else
    echo "ℹ️  סביבה וירטואלית כבר קיימת"
fi

# Activate virtual environment
echo ""
echo "🔌 מפעיל סביבה וירטואלית..."
source venv/bin/activate
echo "✅ סביבה וירטואלית פעילה"

# Install dependencies
echo ""
echo "📦 מתקין תלויות..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✅ תלויות הותקנו"

# Create .env from example
echo ""
if [ ! -f ".env" ]; then
    echo "📝 יוצר קובץ .env..."
    cp .env.example .env
    echo "✅ קובץ .env נוצר"
    echo ""
    echo "⚠️  חשוב! ערוך את הקובץ .env והזן את הפרטים שלך:"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - TELEGRAM_CHAT_ID"
    echo "   - MONGODB_URI"
    echo "   - FB_EMAIL"
    echo "   - FB_PASSWORD"
    echo "   - FB_GROUPS"
else
    echo "ℹ️  קובץ .env כבר קיים"
fi

echo ""
echo "🎉 ההתקנה הושלמה!"
echo ""
echo "📌 הצעדים הבאים:"
echo "1. ערוך את הקובץ .env"
echo "2. הפעל: source venv/bin/activate"
echo "3. הפעל: python main.py"
echo ""
echo "או פרוס ישירות ל-Render! ראה README.md"
