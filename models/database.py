"""
מודלים למסד נתונים
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from config import MONGODB_URI, DATABASE_NAME


class Database:
    """מנהל חיבור למונגו"""
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance
    
    def connect(self):
        """יצירת חיבור למסד נתונים"""
        if self._client is None:
            self._client = MongoClient(MONGODB_URI)
            self._db = self._client[DATABASE_NAME]
            self._create_indexes()
        return self._db
    
    def _create_indexes(self):
        """יצירת אינדקסים"""
        posts = self._db.posts
        posts.create_index([("post_id", ASCENDING)], unique=True)
        posts.create_index([("discovered_at", DESCENDING)])
        posts.create_index([("status", ASCENDING)])
        posts.create_index([("group_name", ASCENDING)])
    
    @property
    def posts(self):
        """גישה לקולקציית posts"""
        if self._db is None:
            self.connect()
        return self._db.posts
    
    @property
    def groups(self):
        """גישה לקולקציית groups"""
        if self._db is None:
            self.connect()
        return self._db.groups
    
    def close(self):
        """סגירת החיבור"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None


class Post:
    """מודל פוסט מפייסבוק"""
    
    STATUS_NEW = "new"
    STATUS_SAVED = "saved"
    STATUS_CONTACTED = "contacted"
    STATUS_NOT_RELEVANT = "not_relevant"
    STATUS_ARCHIVED = "archived"
    
    def __init__(self, db: Database = None):
        self.db = db or Database()
        self.collection = self.db.posts
    
    def create(self, post_data: Dict[str, Any]) -> Optional[str]:
        """יצירת פוסט חדש"""
        post = {
            "post_id": post_data["post_id"],
            "group_name": post_data["group_name"],
            "group_url": post_data.get("group_url", ""),
            "author": post_data.get("author", "לא ידוע"),
            "author_profile": post_data.get("author_profile", ""),
            "text": post_data["text"],
            "timestamp": post_data.get("timestamp", datetime.utcnow()),
            "discovered_at": datetime.utcnow(),
            "status": self.STATUS_NEW,
            "notes": "",
            "post_url": post_data.get("post_url", ""),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            result = self.collection.insert_one(post)
            return str(result.inserted_id)
        except Exception as e:
            print(f"שגיאה ביצירת פוסט: {e}")
            return None
    
    def exists(self, post_id: str) -> bool:
        """בדיקה אם פוסט קיים"""
        return self.collection.find_one({"post_id": post_id}) is not None
    
    def update_status(self, post_id: str, status: str, notes: str = None) -> bool:
        """עדכון סטטוס פוסט"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if notes:
            update_data["notes"] = notes
        
        result = self.collection.update_one(
            {"post_id": post_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def get_stats(self) -> Dict[str, int]:
        """סטטיסטיקות פוסטים"""
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        results = list(self.collection.aggregate(pipeline))
        stats = {item["_id"]: item["count"] for item in results}
        stats["total"] = sum(stats.values())
        
        return stats
    
    def get_recent(self, limit: int = 10, status: str = None) -> list:
        """קבלת פוסטים אחרונים"""
        query = {}
        if status:
            query["status"] = status
        
        posts = self.collection.find(query).sort(
            "discovered_at", DESCENDING
        ).limit(limit)
        
        return list(posts)


class Group:
    """מודל קבוצת פייסבוק"""
    
    def __init__(self, db: Database = None):
        self.db = db or Database()
        self.collection = self.db.groups
    
    def update_stats(self, group_url: str, group_name: str, posts_found: int):
        """עדכון סטטיסטיקות קבוצה"""
        self.collection.update_one(
            {"url": group_url},
            {
                "$set": {
                    "name": group_name,
                    "last_checked": datetime.utcnow()
                },
                "$inc": {
                    "total_posts_found": posts_found
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow(),
                    "is_active": True
                }
            },
            upsert=True
        )
    
    def get_all(self) -> list:
        """קבלת כל הקבוצות"""
        return list(self.collection.find({"is_active": True}))
