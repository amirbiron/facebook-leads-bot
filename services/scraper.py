"""
שירות סקרייפינג של פייסבוק
"""
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

from config import (
    FB_EMAIL, FB_PASSWORD, FB_GROUPS, 
    POSTS_PER_GROUP, HEADLESS_MODE
)
from utils.logger import get_logger

logger = get_logger(__name__)


class HumanBehavior:
    """התנהגות דמוית אדם למניעת זיהוי"""
    
    @staticmethod
    def random_delay(min_sec: float = 2, max_sec: float = 8):
        """המתנה אקראית"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    @staticmethod
    def scroll_slowly(driver, scrolls: int = 3):
        """גלילה איטית"""
        for _ in range(scrolls):
            scroll_amount = random.randint(200, 400)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(0.5, 1.5))
    
    @staticmethod
    def random_read_time():
        """זמן קריאה אקראי"""
        return random.uniform(1.5, 4)


class FacebookScraper:
    """סורק פוסטים מפייסבוק"""
    
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        self.behavior = HumanBehavior()
    
    def setup_driver(self):
        """הגדרת דפדפן"""
        try:
            options = uc.ChromeOptions()
            
            if HEADLESS_MODE:
                options.add_argument('--headless')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--lang=he-IL')
            
            # User agent אמיתי
            options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            
            logger.info("דפדפן הוגדר בהצלחה")
            return True
            
        except Exception as e:
            logger.error(f"שגיאה בהגדרת דפדפן: {e}")
            return False
    
    def login(self) -> bool:
        """התחברות לפייסבוק"""
        try:
            logger.info("מתחבר לפייסבוק...")
            
            self.driver.get("https://www.facebook.com")
            self.behavior.random_delay(3, 5)
            
            # מציאת שדות התחברות
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            password_field = self.driver.find_element(By.ID, "pass")
            
            # הזנת פרטים כמו אדם
            for char in FB_EMAIL:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            self.behavior.random_delay(1, 2)
            
            for char in FB_PASSWORD:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            self.behavior.random_delay(1, 2)
            
            # לחיצה על כפתור התחברות
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            self.behavior.random_delay(5, 8)
            
            # בדיקה אם התחברנו בהצלחה
            if "login" not in self.driver.current_url.lower():
                self.is_logged_in = True
                logger.info("התחברות הצליחה!")
                return True
            else:
                logger.error("התחברות נכשלה")
                return False
                
        except Exception as e:
            logger.error(f"שגיאה בהתחברות: {e}")
            return False
    
    def scrape_group(self, group_url: str) -> List[Dict]:
        """סקרייפינג של קבוצה אחת"""
        posts = []
        
        try:
            logger.info(f"סורק קבוצה: {group_url}")
            
            self.driver.get(group_url)
            self.behavior.random_delay(4, 7)
            
            # גלילה לטעינת פוסטים
            self.behavior.scroll_slowly(self.driver, scrolls=5)
            self.behavior.random_delay(2, 4)
            
            # חילוץ HTML
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')
            
            # חילוץ שם הקבוצה
            group_name = self._extract_group_name(soup)
            
            # חיפוש פוסטים
            post_elements = self._find_post_elements(soup)
            
            logger.info(f"נמצאו {len(post_elements)} פוסטים בקבוצה")
            
            for idx, post_elem in enumerate(post_elements[:POSTS_PER_GROUP]):
                try:
                    post_data = self._extract_post_data(
                        post_elem, group_name, group_url
                    )
                    
                    if post_data:
                        posts.append(post_data)
                        logger.debug(f"פוסט {idx + 1} חולץ בהצלחה")
                    
                    # המתנה קצרה בין פוסטים
                    if idx < len(post_elements) - 1:
                        time.sleep(self.behavior.random_read_time())
                        
                except Exception as e:
                    logger.warning(f"שגיאה בחילוץ פוסט {idx + 1}: {e}")
                    continue
            
            logger.info(f"חולצו {len(posts)} פוסטים מהקבוצה")
            
        except Exception as e:
            logger.error(f"שגיאה בסקרייפינג קבוצה: {e}")
        
        return posts
    
    def _extract_group_name(self, soup: BeautifulSoup) -> str:
        """חילוץ שם הקבוצה"""
        try:
            # ניסיון למצוא את שם הקבוצה
            title = soup.find('title')
            if title:
                return title.text.split('|')[0].strip()
            return "קבוצה לא ידועה"
        except:
            return "קבוצה לא ידועה"
    
    def _find_post_elements(self, soup: BeautifulSoup) -> List:
        """מציאת אלמנטים של פוסטים"""
        # פייסבוק משתמש במבנה מורכב - צריך להתאים לפי המבנה האמיתי
        # זה דוגמה בסיסית שתצטרך התאמה
        posts = []
        
        # חיפוש כל ה-div עם role="article" (פוסטים)
        articles = soup.find_all('div', {'role': 'article'})
        posts.extend(articles)
        
        return posts
    
    def _extract_post_data(
        self, post_elem, group_name: str, group_url: str
    ) -> Optional[Dict]:
        """חילוץ מידע מפוסט בודד"""
        try:
            # חילוץ טקסט הפוסט
            text = self._extract_text(post_elem)
            if not text or len(text) < 10:
                return None
            
            # חילוץ מזהה פוסט
            post_id = self._extract_post_id(post_elem)
            if not post_id:
                post_id = f"unknown_{hash(text[:50])}"
            
            # חילוץ מחבר
            author = self._extract_author(post_elem)
            
            # חילוץ זמן
            timestamp = self._extract_timestamp(post_elem)
            
            # חילוץ URL של הפוסט
            post_url = self._extract_post_url(post_elem, group_url)
            
            return {
                "post_id": post_id,
                "group_name": group_name,
                "group_url": group_url,
                "author": author,
                "author_profile": "",
                "text": text,
                "timestamp": timestamp,
                "post_url": post_url
            }
            
        except Exception as e:
            logger.warning(f"שגיאה בחילוץ נתוני פוסט: {e}")
            return None
    
    def _extract_text(self, post_elem) -> str:
        """חילוץ טקסט הפוסט"""
        text_parts = []
        
        # חיפוש כל אלמנטי הטקסט
        for text_elem in post_elem.find_all(['p', 'span', 'div']):
            text = text_elem.get_text(strip=True)
            if text and len(text) > 3:
                text_parts.append(text)
        
        return ' '.join(text_parts[:5])  # מגביל לטקסט הראשי
    
    def _extract_post_id(self, post_elem) -> Optional[str]:
        """חילוץ מזהה פוסט"""
        # חיפוש data-ft או תכונות אחרות עם ID
        for attr in ['data-ft', 'id', 'data-testid']:
            if post_elem.has_attr(attr):
                return str(post_elem[attr])
        return None
    
    def _extract_author(self, post_elem) -> str:
        """חילוץ שם המחבר"""
        try:
            author_elem = post_elem.find('a', href=True)
            if author_elem:
                return author_elem.get_text(strip=True)
        except:
            pass
        return "לא ידוע"
    
    def _extract_timestamp(self, post_elem) -> datetime:
        """חילוץ זמן הפרסום"""
        # ברירת מחדל - זמן נוכחי
        return datetime.utcnow()
    
    def _extract_post_url(self, post_elem, group_url: str) -> str:
        """חילוץ URL של הפוסט"""
        try:
            # חיפוש קישור לפוסט
            link = post_elem.find('a', href=True)
            if link and '/posts/' in link['href']:
                href = link['href']
                if href.startswith('/'):
                    return f"https://www.facebook.com{href}"
                return href
        except:
            pass
        return group_url
    
    def scrape_all_groups(self) -> List[Dict]:
        """סקרייפינג של כל הקבוצות"""
        all_posts = []
        
        if not self.setup_driver():
            return all_posts
        
        try:
            if not self.login():
                return all_posts
            
            # סקרייפינג של 1-2 קבוצות אקראיות בכל פעם
            groups_to_scrape = random.sample(
                FB_GROUPS, 
                min(2, len(FB_GROUPS))
            )
            
            for group_url in groups_to_scrape:
                posts = self.scrape_group(group_url)
                all_posts.extend(posts)
                
                # המתנה בין קבוצות
                if group_url != groups_to_scrape[-1]:
                    self.behavior.random_delay(10, 20)
            
        except Exception as e:
            logger.error(f"שגיאה כללית בסקרייפינג: {e}")
        
        finally:
            self.close()
        
        return all_posts
    
    def close(self):
        """סגירת הדפדפן"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("דפדפן נסגר")
            except:
                pass
            self.driver = None
            self.is_logged_in = False
