"""
שירות התאמת מילות מפתח
"""
from typing import Dict, List
from config import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS
from utils.logger import get_logger

logger = get_logger(__name__)


class KeywordsMatcher:
    """מזהה פוסטים רלוונטיים לפי מילות מפתח"""
    
    def __init__(self):
        self.positive_keywords = [kw.lower() for kw in POSITIVE_KEYWORDS]
        self.negative_keywords = [kw.lower() for kw in NEGATIVE_KEYWORDS]
    
    def is_relevant(self, text: str) -> Dict:
        """
        בדיקה אם הפוסט רלוונטי
        
        Returns:
            dict: {
                "is_relevant": bool,
                "matched_positive": List[str],
                "matched_negative": List[str]
            }
        """
        text_lower = text.lower()
        
        # חיפוש מילות מפתח חיוביות
        matched_positive = [
            kw for kw in self.positive_keywords 
            if kw in text_lower
        ]
        
        # חיפוש מילות מפתח שליליות
        matched_negative = [
            kw for kw in self.negative_keywords 
            if kw in text_lower
        ]
        
        # פוסט רלוונטי אם יש לפחות מילת מפתח חיובית אחת
        # ואין מילות מפתח שליליות
        is_relevant = (
            len(matched_positive) > 0 and 
            len(matched_negative) == 0
        )
        
        result = {
            "is_relevant": is_relevant,
            "matched_positive": matched_positive,
            "matched_negative": matched_negative
        }
        
        if is_relevant:
            logger.info(
                f"פוסט רלוונטי נמצא! "
                f"מילות מפתח: {', '.join(matched_positive)}"
            )
        else:
            if len(matched_negative) > 0:
                logger.debug(
                    f"פוסט נדחה בגלל מילות מפתח שליליות: "
                    f"{', '.join(matched_negative)}"
                )
            else:
                logger.debug("פוסט נדחה - אין מילות מפתח רלוונטיות")
        
        return result
    
    def get_keywords_info(self) -> Dict:
        """מידע על מילות המפתח הנוכחיות"""
        return {
            "positive": self.positive_keywords,
            "negative": self.negative_keywords,
            "total_positive": len(self.positive_keywords),
            "total_negative": len(self.negative_keywords)
        }
