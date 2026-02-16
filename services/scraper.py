"""
שירות סקרייפינג של פייסבוק - גרסה מתוקנת
===========================================
שינויים עיקריים מהגרסה המקורית:
1. שימוש ב-m.facebook.com (מובייל) - HTML פשוט בהרבה
2. גלילה + חילוץ בלולאה (scroll-then-parse) - לא מפספס פוסטים
3. סלקטורים מרובים עם fallback - עמיד לשינויי פייסבוק
4. Debug logging מקיף - screenshots + HTML dumps
5. בדיקת לוגין אמיתית (לא רק URL check)
6. חילוץ טקסט משופר עם ניקוי
"""
import os
import re
import time
import random
import hashlib
import gc
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    StaleElementReferenceException, WebDriverException
)
import undetected_chromedriver as uc

from config import (
    FB_EMAIL, FB_PASSWORD, FB_GROUPS,
    POSTS_PER_GROUP, GROUPS_PER_CYCLE, HEADLESS_MODE
)
from utils.logger import get_logger

logger = get_logger(__name__)

# תיקיית debug - screenshots ו-HTML dumps
DEBUG_DIR = Path(os.getenv("DEBUG_DIR", "/tmp/fb_debug"))
# Disable debug mode in production to save memory (screenshots + HTML dumps)
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"


class HumanBehavior:
    """התנהגות דמוית אדם למניעת זיהוי"""

    @staticmethod
    def random_delay(min_sec: float = 2, max_sec: float = 8):
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    @staticmethod
    def scroll_down(driver, amount: int = 800):
        """גלילה למטה"""
        driver.execute_script(f"window.scrollBy(0, {amount})")
        time.sleep(random.uniform(1.0, 2.5))

    @staticmethod
    def scroll_to_bottom(driver):
        """גלילה לתחתית הדף"""
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(random.uniform(1.5, 3.0))

    @staticmethod
    def random_read_time():
        return random.uniform(1.5, 4)


class FacebookScraper:
    """סורק פוסטים מפייסבוק - גרסת מובייל"""

    # --- סלקטורים מרובים עם fallback ---
    # פייסבוק משנים את המבנה תדיר, אז מנסים כמה אפשרויות
    POST_SELECTORS = [
        # מובייל - article element
        'article',
        # מובייל - story divs
        'div[data-ft]',
        # מובייל - post containers
        'div.story_body_container',
        # דסקטופ fallback
        'div[role="article"]',
        # generic feed items
        'div[data-ad-preview="message"]',
    ]

    POST_TEXT_SELECTORS = [
        # מובייל - טקסט ראשי של פוסט
        'div.story_body_container p',
        'div[data-ft] p',
        'div.story_body_container span',
        'div[data-ft] div > span',
        # דסקטופ fallback
        'div[data-ad-comet-preview="message"]',
        'div[dir="auto"]',
    ]

    POST_LINK_SELECTORS = [
        # מובייל - לינק לפוסט
        'a[href*="/groups/"][href*="/permalink/"]',
        'a[href*="/story.php"]',
        'a[href*="/posts/"]',
        'abbr a',
    ]

    AUTHOR_SELECTORS = [
        # מובייל
        'h3 a',
        'strong a',
        'header a',
        # דסקטופ fallback
        'a[role="link"] strong span',
    ]

    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        self.behavior = HumanBehavior()
        self._use_mobile = True  # ברירת מחדל: מובייל
        self._seen_post_hashes: Set[str] = set()

        if DEBUG_MODE:
            DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # Debug helpers
    # ============================================================

    def _debug_screenshot(self, name: str):
        """צילום מסך לדיבוג"""
        if not DEBUG_MODE or not self.driver:
            return
        try:
            path = DEBUG_DIR / f"{name}_{int(time.time())}.png"
            self.driver.save_screenshot(str(path))
            logger.debug(f"📸 Screenshot שמור: {path}")
        except Exception as e:
            logger.debug(f"לא ניתן לשמור screenshot: {e}")

    def _debug_html(self, name: str, max_chars: int = 5000):
        """שמירת HTML לדיבוג"""
        if not DEBUG_MODE or not self.driver:
            return
        try:
            html = self.driver.page_source
            path = DEBUG_DIR / f"{name}_{int(time.time())}.html"
            with open(path, "w", encoding="utf-8") as f:
                f.write(html[:50000])
            logger.debug(f"📄 HTML שמור: {path} ({len(html)} תווים)")

            # לוג של ה-title וה-URL
            title = self.driver.title
            url = self.driver.current_url
            logger.info(f"🔍 Page title: {title}")
            logger.info(f"🔍 Page URL: {url}")

            # בדיקה מהירה אם יש תוכן בדף
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            logger.info(f"🔍 Body text length: {len(body_text)} chars")
            if len(body_text) < 500:
                logger.warning(f"⚠️ תוכן דל בדף! תחילת body: {body_text[:300]}")
        except Exception as e:
            logger.debug(f"לא ניתן לשמור HTML: {e}")

    def _post_hash(self, text: str) -> str:
        """יוצר hash ייחודי לפוסט למניעת כפילויות"""
        clean = re.sub(r'\s+', ' ', text.strip())[:200]
        return hashlib.md5(clean.encode('utf-8')).hexdigest()

    # ============================================================
    # Driver setup
    # ============================================================

    def setup_driver(self):
        """הגדרת דפדפן"""
        try:
            options = uc.ChromeOptions()

            if HEADLESS_MODE:
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')

            # === AGGRESSIVE MEMORY OPTIMIZATION FOR 512MB LIMIT ===
            options.add_argument('--window-size=420,900')  # גודל מובייל
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--lang=he-IL')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-notifications')
            
            # Memory optimization flags (critical for 512MB limit)
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-webgl')
            options.add_argument('--disable-3d-apis')
            options.add_argument('--disable-accelerated-2d-canvas')
            options.add_argument('--disable-accelerated-video-decode')
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-breakpad')
            options.add_argument('--disable-component-extensions-with-background-pages')
            options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
            options.add_argument('--disable-ipc-flooding-protection')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-sync')
            options.add_argument('--enable-features=NetworkService,NetworkServiceInProcess')
            options.add_argument('--force-color-profile=srgb')
            options.add_argument('--hide-scrollbars')
            options.add_argument('--mute-audio')
            options.add_argument('--disable-client-side-phishing-detection')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-hang-monitor')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-prompt-on-repost')
            options.add_argument('--metrics-recording-only')
            options.add_argument('--no-pings')
            options.add_argument('--password-store=basic')
            options.add_argument('--use-mock-keychain')
            options.add_argument('--disable-setuid-sandbox')
            
            # Memory limits
            options.add_argument('--js-flags=--max-old-space-size=256')  # Limit JS heap
            
            # Disable loading of images, CSS, and JS to save even more memory
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2,  # Disable images
                    'javascript': 1,  # Enable JS (needed for Facebook)
                },
                'profile.managed_default_content_settings': {
                    'images': 2
                },
                'disk-cache-size': 4096
            }
            options.add_experimental_option('prefs', prefs)
            
            # Additional memory limits
            options.add_argument('--max-old-space-size=256')  # Limit V8 memory

            chrome_bin = os.getenv("CHROME_BIN")
            if chrome_bin:
                options.binary_location = chrome_bin

            # User agent מובייל
            if self._use_mobile:
                options.add_argument(
                    'user-agent=Mozilla/5.0 (Linux; Android 13; Pixel 7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Mobile Safari/537.36'
                )
            else:
                options.add_argument(
                    'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                )

            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(45)

            logger.info("✅ דפדפן הוגדר בהצלחה (מצב: %s)",
                        "מובייל" if self._use_mobile else "דסקטופ")
            return True

        except Exception as e:
            logger.error(f"❌ שגיאה בהגדרת דפדפן: {e}")
            return False

    # ============================================================
    # Login
    # ============================================================

    def login(self) -> bool:
        """התחברות לפייסבוק"""
        try:
            base_url = "https://m.facebook.com" if self._use_mobile else "https://www.facebook.com"
            logger.info(f"מתחבר לפייסבוק ({base_url})...")

            self.driver.get(f"{base_url}/login")
            self.behavior.random_delay(3, 5)
            self._debug_screenshot("01_login_page")

            # --- סגירת cookie banner אם יש ---
            self._dismiss_cookie_banner()

            # --- מציאת שדות התחברות ---
            email_field = self._find_login_field("email")
            password_field = self._find_login_field("pass")

            if not email_field or not password_field:
                logger.error("❌ לא נמצאו שדות התחברות!")
                self._debug_screenshot("01_login_fields_missing")
                self._debug_html("01_login_fields_missing")
                return False

            # הזנת פרטים כמו אדם
            self._type_like_human(email_field, FB_EMAIL)
            self.behavior.random_delay(0.5, 1.5)
            self._type_like_human(password_field, FB_PASSWORD)
            self.behavior.random_delay(0.5, 1.5)

            # לחיצה על כפתור התחברות
            login_btn = self._find_login_button()
            if login_btn:
                login_btn.click()
            else:
                # fallback: submit הטופס
                password_field.submit()

            self.behavior.random_delay(5, 8)
            self._debug_screenshot("02_after_login")
            self._debug_html("02_after_login")

            # --- בדיקת לוגין אמיתית ---
            if self._verify_login():
                self.is_logged_in = True
                logger.info("✅ התחברות הצליחה!")
                return True
            else:
                logger.error("❌ התחברות נכשלה - ייתכן שיש checkpoint/2FA")
                self._debug_screenshot("02_login_failed")
                self._debug_html("02_login_failed")
                return False

        except Exception as e:
            logger.error(f"❌ שגיאה בהתחברות: {e}")
            self._debug_screenshot("02_login_exception")
            return False

    def _dismiss_cookie_banner(self):
        """סגירת cookie popup אם מופיע"""
        try:
            for selector in [
                '[data-cookiebanner="accept_button"]',
                'button[title="Allow all cookies"]',
                'button[title="אפשר את כל העוגיות"]',
                'button[value="1"][name="accept"]',
            ]:
                btns = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if btns:
                    btns[0].click()
                    logger.debug("סגרתי cookie banner")
                    self.behavior.random_delay(1, 2)
                    return
        except Exception:
            pass

    def _find_login_field(self, field_name: str):
        """מציאת שדה בטופס לוגין עם fallback"""
        selectors = [
            (By.ID, field_name),
            (By.NAME, field_name),
            (By.CSS_SELECTOR, f'input[name="{field_name}"]'),
            (By.CSS_SELECTOR, f'input[id="{field_name}"]'),
        ]
        for by, selector in selectors:
            try:
                elem = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((by, selector))
                )
                return elem
            except TimeoutException:
                continue
        return None

    def _find_login_button(self):
        """מציאת כפתור התחברות"""
        selectors = [
            (By.NAME, "login"),
            (By.CSS_SELECTOR, 'button[name="login"]'),
            (By.CSS_SELECTOR, 'input[type="submit"]'),
            (By.CSS_SELECTOR, 'button[type="submit"]'),
            (By.CSS_SELECTOR, 'button[data-testid="royal_login_button"]'),
        ]
        for by, selector in selectors:
            try:
                return self.driver.find_element(by, selector)
            except NoSuchElementException:
                continue
        return None

    def _type_like_human(self, element, text: str):
        """הקלדה דמוית אדם"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

    def _verify_login(self) -> bool:
        """בדיקה אמיתית אם ההתחברות הצליחה"""
        url = self.driver.current_url.lower()

        # אם נשארנו בדף לוגין = נכשל
        if any(x in url for x in ['login', 'checkpoint', 'recover', 'captcha']):
            logger.warning(f"⚠️ URL מרמז על כישלון: {url}")
            return False

        # בדיקה שיש אלמנטים שמעידים על חשבון מחובר
        logged_in_indicators = [
            'a[href*="/me"]',
            'a[href*="/profile"]',
            'input[name="q"]',          # שדה חיפוש
            'div[role="navigation"]',    # תפריט ניווט
            'a[href="/notifications/"]', # לינק התראות (מובייל)
        ]

        for sel in logged_in_indicators:
            try:
                self.driver.find_element(By.CSS_SELECTOR, sel)
                logger.debug(f"נמצא אינדיקטור חיבור: {sel}")
                return True
            except NoSuchElementException:
                continue

        # fallback: בדיקת body text
        try:
            body = self.driver.find_element(By.TAG_NAME, "body").text
            # אם יש "Log In" או "התחבר" בולט = עדיין לא מחוברים
            if "Log In" in body[:200] or "התחבר" in body[:200]:
                return False
            # אם יש מספיק תוכן = כנראה מחוברים
            if len(body) > 500:
                return True
        except Exception:
            pass

        logger.warning("⚠️ לא ניתן לאמת התחברות בוודאות")
        return False

    # ============================================================
    # Group scraping
    # ============================================================

    def scrape_group(self, group_url: str) -> List[Dict]:
        """סקרייפינג של קבוצה אחת"""
        posts = []

        try:
            # המרה ל-URL מובייל אם צריך
            mobile_url = self._to_mobile_url(group_url)
            logger.info(f"📌 סורק קבוצה: {mobile_url}")

            self.driver.get(mobile_url)
            self.behavior.random_delay(4, 7)
            self._debug_screenshot(f"03_group_{self._group_slug(group_url)}")
            self._debug_html(f"03_group_{self._group_slug(group_url)}")

            # --- בדיקה שהדף נטען כראוי ---
            if not self._verify_group_page():
                logger.warning(f"⚠️ דף הקבוצה לא נטען כראוי: {group_url}")
                return posts

            group_name = self._extract_group_name()

            # --- גלילה + חילוץ בלולאה ---
            posts = self._scroll_and_extract(group_name, group_url)

            logger.info(f"📊 חולצו {len(posts)} פוסטים מהקבוצה '{group_name}'")

        except Exception as e:
            logger.error(f"❌ שגיאה בסקרייפינג קבוצה {group_url}: {e}")
            self._debug_screenshot("error_group")

        return posts

    def _to_mobile_url(self, url: str) -> str:
        """המרת URL לגרסת מובייל"""
        if self._use_mobile:
            return url.replace("www.facebook.com", "m.facebook.com") \
                       .replace("web.facebook.com", "m.facebook.com")
        return url

    def _group_slug(self, url: str) -> str:
        """חילוץ slug מ-URL לצורך שמות קבצים"""
        parts = url.rstrip('/').split('/')
        return parts[-1] if parts else "unknown"

    def _verify_group_page(self) -> bool:
        """בדיקה שדף הקבוצה נטען"""
        url = self.driver.current_url.lower()

        # אם הופנינו ללוגין
        if 'login' in url:
            logger.error("❌ הופנינו חזרה ללוגין! הסשן פג")
            return False

        # אם הדף ריק או שגיאה
        try:
            body = self.driver.find_element(By.TAG_NAME, "body").text
            if len(body) < 100:
                logger.warning(f"⚠️ דף ריק ({len(body)} תווים)")
                return False

            # בדיקה שזה באמת דף קבוצה
            if "groups" not in url and "group" not in url:
                logger.warning(f"⚠️ URL לא נראה כמו קבוצה: {url}")
                return False

            return True
        except Exception as e:
            logger.error(f"שגיאה בבדיקת דף: {e}")
            return False

    def _extract_group_name(self) -> str:
        """חילוץ שם הקבוצה"""
        try:
            title = self.driver.title
            if title:
                # הסרת " | Facebook" מהסוף
                name = title.split('|')[0].strip()
                if name and name != "Facebook":
                    return name
        except Exception:
            pass

        # fallback: חיפוש ב-h1
        try:
            h1 = self.driver.find_element(By.TAG_NAME, "h1")
            return h1.text.strip() or "קבוצה לא ידועה"
        except Exception:
            return "קבוצה לא ידועה"

    # ============================================================
    # Scroll & Extract Loop
    # ============================================================

    def _scroll_and_extract(self, group_name: str, group_url: str) -> List[Dict]:
        """
        הלב של הסקרייפר: גלילה → חילוץ → גלילה → חילוץ
        כל סיבוב מחלץ את הפוסטים שעל המסך, ואז גולל הלאה.
        פוסטים כפולים מסוננים לפי hash.
        """
        all_posts = []
        # Reduced scrolls to save memory (was 8, now 4)
        max_scrolls = 4
        no_new_count = 0

        for scroll_num in range(max_scrolls):
            # חילוץ פוסטים מהמסך הנוכחי
            new_posts = self._extract_visible_posts(group_name, group_url)

            added = 0
            for post in new_posts:
                h = self._post_hash(post['text'])
                if h not in self._seen_post_hashes:
                    self._seen_post_hashes.add(h)
                    all_posts.append(post)
                    added += 1

            logger.debug(f"גלילה {scroll_num + 1}/{max_scrolls}: "
                         f"+{added} חדשים (סה\"כ {len(all_posts)})")

            # אם לא מצאנו פוסטים חדשים 2 פעמים ברצף → מפסיקים
            if added == 0:
                no_new_count += 1
                if no_new_count >= 2:
                    logger.debug("אין פוסטים חדשים, מפסיק גלילה")
                    break
            else:
                no_new_count = 0

            # עצירה אם הגענו למכסה
            if len(all_posts) >= POSTS_PER_GROUP:
                break

            # גלילה למטה
            self.behavior.scroll_down(self.driver, random.randint(600, 1200))

            # המתנה לטעינת תוכן חדש
            time.sleep(random.uniform(2, 4))

        return all_posts[:POSTS_PER_GROUP]

    def _extract_visible_posts(self, group_name: str, group_url: str) -> List[Dict]:
        """חילוץ כל הפוסטים הגלויים כרגע על המסך"""
        posts = []

        # ננסה כל סלקטור עד שנמצא פוסטים
        post_elements = []
        used_selector = None

        for selector in self.POST_SELECTORS:
            try:
                found = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if found:
                    post_elements = found
                    used_selector = selector
                    break
            except Exception:
                continue

        if not post_elements:
            # fallback אחרון: חיפוש לפי XPath - כל div שמכיל טקסט משמעותי
            try:
                post_elements = self.driver.find_elements(
                    By.XPATH,
                    '//div[string-length(normalize-space(.)) > 50 '
                    'and not(ancestor::nav) '
                    'and not(ancestor::header) '
                    'and count(.//p | .//span[@dir]) > 0]'
                )
                used_selector = "XPath fallback"
            except Exception:
                pass

        if post_elements:
            logger.debug(f"נמצאו {len(post_elements)} אלמנטים עם: {used_selector}")
        else:
            logger.warning("⚠️ לא נמצאו אלמנטי פוסטים כלל!")
            self._debug_screenshot("no_posts_found")
            self._debug_html("no_posts_found")
            return posts

        for elem in post_elements:
            try:
                post_data = self._extract_single_post(elem, group_name, group_url)
                if post_data:
                    posts.append(post_data)
            except StaleElementReferenceException:
                continue
            except Exception as e:
                logger.debug(f"שגיאה בחילוץ פוסט בודד: {e}")
                continue

        return posts

    def _extract_single_post(self, elem, group_name: str, group_url: str) -> Optional[Dict]:
        """חילוץ מידע מפוסט בודד (Selenium element, לא BeautifulSoup)"""
        try:
            # --- טקסט ---
            text = self._extract_post_text(elem)
            if not text or len(text) < 15:
                return None

            # סינון אלמנטים שהם לא באמת פוסטים
            noise_indicators = [
                'suggested for you', 'מומלץ עבורך',
                'join group', 'הצטרף לקבוצה',
                'write something', 'כתוב משהו',
                'create a post', 'יצירת פוסט',
            ]
            text_lower = text.lower()
            if any(noise in text_lower for noise in noise_indicators):
                return None

            # --- מזהה ---
            post_id = self._extract_post_id_selenium(elem)
            if not post_id:
                post_id = f"fb_{self._post_hash(text)[:12]}"

            # --- מחבר ---
            author = self._extract_author_selenium(elem)

            # --- URL ---
            post_url = self._extract_post_url_selenium(elem, group_url)

            return {
                "post_id": post_id,
                "group_name": group_name,
                "group_url": group_url,
                "author": author,
                "author_profile": "",
                "text": text,
                "timestamp": datetime.utcnow(),
                "post_url": post_url,
            }

        except Exception as e:
            logger.debug(f"שגיאה בחילוץ נתוני פוסט: {e}")
            return None

    def _extract_post_text(self, elem) -> str:
        """חילוץ טקסט מפוסט - מנסה כמה שיטות"""
        # שיטה 1: חיפוש סלקטורים ספציפיים
        for selector in self.POST_TEXT_SELECTORS:
            try:
                text_elems = elem.find_elements(By.CSS_SELECTOR, selector)
                if text_elems:
                    texts = [e.text.strip() for e in text_elems if e.text.strip()]
                    if texts:
                        return ' '.join(texts[:5])
            except Exception:
                continue

        # שיטה 2: כל ה-text content של האלמנט
        try:
            full_text = elem.text.strip()
            if full_text and len(full_text) > 15:
                # ניקוי: הסרת שורות כפולות, רווחים מיותרים
                lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                # לקיחת השורות הראשונות (בד"כ הטקסט של הפוסט)
                # דילוג על שורות קצרות מאוד בהתחלה (שם, זמן)
                content_lines = []
                for line in lines:
                    if len(line) > 10:
                        content_lines.append(line)
                    if len(content_lines) >= 5:
                        break
                if content_lines:
                    return ' '.join(content_lines)
        except Exception:
            pass

        return ""

    def _extract_post_id_selenium(self, elem) -> Optional[str]:
        """חילוץ מזהה פוסט"""
        try:
            # חיפוש לינק עם permalink
            links = elem.find_elements(By.CSS_SELECTOR, 'a[href]')
            for link in links:
                href = link.get_attribute('href') or ''
                # חילוץ ID מה-URL
                for pattern in [
                    r'/permalink/(\d+)',
                    r'/posts/(\d+)',
                    r'story_fbid=(\d+)',
                    r'fbid=(\d+)',
                ]:
                    match = re.search(pattern, href)
                    if match:
                        return match.group(1)
        except Exception:
            pass

        # fallback: attribute של האלמנט
        for attr in ['data-ft', 'id', 'data-testid']:
            try:
                val = elem.get_attribute(attr)
                if val:
                    return str(val)[:50]
            except Exception:
                continue

        return None

    def _extract_author_selenium(self, elem) -> str:
        """חילוץ שם מחבר"""
        for selector in self.AUTHOR_SELECTORS:
            try:
                author_elem = elem.find_element(By.CSS_SELECTOR, selector)
                name = author_elem.text.strip()
                if name and len(name) > 1:
                    return name
            except NoSuchElementException:
                continue
            except Exception:
                continue
        return "לא ידוע"

    def _extract_post_url_selenium(self, elem, group_url: str) -> str:
        """חילוץ URL של הפוסט"""
        for selector in self.POST_LINK_SELECTORS:
            try:
                link = elem.find_element(By.CSS_SELECTOR, selector)
                href = link.get_attribute('href')
                if href:
                    # ניקוי URL
                    if href.startswith('/'):
                        base = "https://m.facebook.com" if self._use_mobile \
                            else "https://www.facebook.com"
                        href = base + href
                    # הסרת tracking params
                    href = href.split('?')[0] if '?' in href and 'permalink' in href else href
                    return href
            except NoSuchElementException:
                continue
            except Exception:
                continue
        return group_url

    # ============================================================
    # Main flow
    # ============================================================

    def scrape_all_groups(self) -> List[Dict]:
        """סקרייפינג של כל הקבוצות"""
        all_posts = []

        if not self.setup_driver():
            return all_posts

        try:
            if not self.login():
                return all_posts

            # בחירת קבוצות אקראיות למחזור הזה
            groups_to_scrape = random.sample(
                FB_GROUPS,
                min(GROUPS_PER_CYCLE, len(FB_GROUPS))
            )

            for i, group_url in enumerate(groups_to_scrape):
                posts = self.scrape_group(group_url)
                all_posts.extend(posts)
                
                # Periodic garbage collection to free memory
                if (i + 1) % 1 == 0:  # After each group
                    gc.collect()
                    logger.debug(f"ניקוי זיכרון אחרי קבוצה {i + 1}")

                # המתנה בין קבוצות (לא אחרי האחרונה)
                if i < len(groups_to_scrape) - 1:
                    delay = random.uniform(10, 20)
                    logger.debug(f"ממתין {delay:.0f} שניות לפני הקבוצה הבאה...")
                    time.sleep(delay)

        except Exception as e:
            logger.error(f"❌ שגיאה כללית בסקרייפינג: {e}")

        finally:
            self.close()

        return all_posts

    def close(self):
        """סגירת הדפדפן עם ניקוי זיכרון אגרסיבי"""
        if self.driver:
            try:
                # Close all windows first
                for handle in self.driver.window_handles:
                    try:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                    except Exception:
                        pass
                
                # Quit the driver
                self.driver.quit()
                logger.info("דפדפן נסגר")
            except Exception as e:
                logger.debug(f"שגיאה בסגירת דפדפן: {e}")
            finally:
                self.driver = None
                self.is_logged_in = False
                
                # Clear seen posts to free memory
                self._seen_post_hashes.clear()
                
                # Force garbage collection
                gc.collect()
                logger.debug("זיכרון נוקה")
