"""
מערכת לוגים
"""
import logging
import sys
from config import LOG_LEVEL


def get_logger(name: str) -> logging.Logger:
    """יצירת logger"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # הגדרת רמת לוג
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(level)
        
        # Handler לקונסול
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # פורמט עם תמיכה בעברית
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger
