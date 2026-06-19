"""
客户服务模块
管理客户画像和跟进记录
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import sqlite3
from pathlib import Path
from loguru import logger

from config.settings import settings


class CustomerProfile:
    """
    客户画像数据模型
    """
    
    def __init__(
        self,
        customer_id: str,
        customer_name: Optional[str] = None,
        industry: Optional[str] = None,
        company_size: Optional[str] = None,
        customer_level: Optional[str] = None,  # A/B/C/D 分级
        contact_person: Optional[str] = None,
        contact_phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
        total_purchase_amount: float = 0.0,
        purchase_count: int = 0,
        last_purchase_date: Optional[str] = None,
        credit_rating: Optional[str] = None,  # 信用评级
        tags: Optional[List[str]] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.industry = industry
        self.company_size = company_size
        self.customer_level = customer_level
        self.contact_person = contact_person
        self.contact_phone = contact_phone
        self.email = email
        self.address = address
        self.total_purchase_amount = total_purchase_amount
        self.purchase_count = purchase_count
        self.last_purchase_date = last_purchase_date
        self.credit_rating = credit_rating
        self.tags = tags or []
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "industry": self.industry,
            "company_size": self.company_size,
            "customer_level": self.customer_level,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "email": self.email,
            "address": self.address,
            "total_purchase_amount": self.total_purchase_amount,
            "purchase_count": self.purchase_count,
            "last_purchase_date": self.last_purchase_date,
            "credit_rating": self.credit_rating,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class FollowUpRecord:
    """
    跟进记录数据模型
    """
    
    def __init__(
        self,
        record_id: Optional[str] = None,
        customer_id: str = "",
        follow_up_type: str = "",  # call/meeting/email/wechat/other
        content: str = "",
        result: Optional[str] = None,
        next_follow_up_date: Optional[str] = None,
        created_by: Optional[str] = None,
        created_at: Optional[str] = None
    ):
        self.record_id = record_id or f"FUR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hash(customer_id) % 10000}"
        self.customer_id = customer_id
        self.follow_up_type = follow_up_type
        self.content = content
        self.result = result
        self.next_follow_up_date = next_follow_up_date
        self.created_by = created_by
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "record_id": self.record_id,
            "customer_id": self.customer_id,
            "follow_up_type": self.follow_up_type,
            "content": self.content,
            "result": self.result,
            "next_follow_up_date": self.next_follow_up_date,
            "created_by": self.created_by,
            "created_at": self.created_at
        }


class CustomerService:
    """
    客户服务类
    提供客户画像和跟进记录的 CRUD 操作
    """
    
    def __init__(self):
        """初始化客户服务"""
        self.db_path = Path(settings.SQLITE_DB_PATH)
        self._init_tables()
        logger.info("客户服务初始化完成")
    
    def _init_tables(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 创建客户画像表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customer_profiles (
                    customer_id TEXT PRIMARY KEY,
                    customer_name TEXT,
                    industry TEXT,
                    company_size TEXT,
                    customer_level TEXT,
                    contact_person TEXT,
                    contact_phone TEXT,
                    email TEXT,
                    address TEXT,
                    total_purchase_amount REAL DEFAULT 0.0,
                    purchase_count INTEGER DEFAULT 0,
                    last_purchase_date TEXT,
                    credit_rating TEXT,
                    tags TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # 创建跟进记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follow_up_records (
                    record_id TEXT PRIMARY KEY,
                    customer_id TEXT,
                    follow_up_type TEXT,
                    content TEXT,
                    result TEXT,
                    next_follow_up_date TEXT,
                    created_by TEXT,
                    created_at TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customer_profiles(customer_id)
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_id ON follow_up_records(customer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_follow_up_date ON follow_up_records(created_at)")
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            logger.error(f"初始化客户表失败: {str(e)}")
    
    def get_customer_profile(self, customer_id: str) -> Optional[CustomerProfile]:
        """
        获取客户画像
        
        Args:
            customer_id: 客户ID
            
        Returns:
            客户画像对象，不存在返回 None
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM customer_profiles WHERE customer_id = ?
            """, (customer_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return CustomerProfile(
                    customer_id=row[0],
                    customer_name=row[1],
                    industry=row[2],
                    company_size=row[3],
                    customer_level=row[4],
                    contact_person=row[5],
                    contact_phone=row[6],
                    email=row[7],
                    address=row[8],
                    total_purchase_amount=row[9],
                    purchase_count=row[10],
                    last_purchase_date=row[11],
                    credit_rating=row[12],
                    tags=eval(row[13]) if row[13] else [],
                    created_at=row[14],
                    updated_at=row[15]
                )
            
            return None
            
        except sqlite3.Error as e:
            logger.error(f"获取客户画像失败: {str(e)}")
            return None
    
    def save_customer_profile(self, profile: CustomerProfile):
        """
        保存客户画像（新增或更新）
        
        Args:
            profile: 客户画像对象
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            profile.updated_at = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO customer_profiles (
                    customer_id, customer_name, industry, company_size, customer_level,
                    contact_person, contact_phone, email, address,
                    total_purchase_amount, purchase_count, last_purchase_date,
                    credit_rating, tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.customer_id,
                profile.customer_name,
                profile.industry,
                profile.company_size,
                profile.customer_level,
                profile.contact_person,
                profile.contact_phone,
                profile.email,
                profile.address,
                profile.total_purchase_amount,
                profile.purchase_count,
                profile.last_purchase_date,
                profile.credit_rating,
                str(profile.tags),
                profile.created_at,
                profile.updated_at
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"客户画像保存成功: {profile.customer_id}")
            
        except sqlite3.Error as e:
            logger.error(f"保存客户画像失败: {str(e)}")
    
    def add_follow_up_record(self, record: FollowUpRecord):
        """
        添加跟进记录
        
        Args:
            record: 跟进记录对象
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO follow_up_records (
                    record_id, customer_id, follow_up_type, content,
                    result, next_follow_up_date, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.record_id,
                record.customer_id,
                record.follow_up_type,
                record.content,
                record.result,
                record.next_follow_up_date,
                record.created_by,
                record.created_at
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"跟进记录添加成功: {record.record_id}")
            
        except sqlite3.Error as e:
            logger.error(f"添加跟进记录失败: {str(e)}")
    
    def get_follow_up_records(self, customer_id: str, limit: int = 20) -> List[FollowUpRecord]:
        """
        获取客户跟进记录列表
        
        Args:
            customer_id: 客户ID
            limit: 返回数量限制
            
        Returns:
            跟进记录列表
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM follow_up_records
                WHERE customer_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (customer_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            records = []
            for row in rows:
                records.append(FollowUpRecord(
                    record_id=row[0],
                    customer_id=row[1],
                    follow_up_type=row[2],
                    content=row[3],
                    result=row[4],
                    next_follow_up_date=row[5],
                    created_by=row[6],
                    created_at=row[7]
                ))
            
            return records
            
        except sqlite3.Error as e:
            logger.error(f"获取跟进记录失败: {str(e)}")
            return []
    
    def update_customer_purchase(self, customer_id: str, amount: float):
        """
        更新客户购买记录
        
        Args:
            customer_id: 客户ID
            amount: 购买金额
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 获取当前客户数据
            cursor.execute("""
                SELECT total_purchase_amount, purchase_count FROM customer_profiles
                WHERE customer_id = ?
            """, (customer_id,))
            
            row = cursor.fetchone()
            if row:
                new_total = row[0] + amount
                new_count = row[1] + 1
                
                cursor.execute("""
                    UPDATE customer_profiles
                    SET total_purchase_amount = ?, purchase_count = ?,
                        last_purchase_date = ?, updated_at = ?
                    WHERE customer_id = ?
                """, (new_total, new_count, datetime.now().isoformat(), datetime.now().isoformat(), customer_id))
                
                conn.commit()
                logger.info(f"客户购买记录更新成功: {customer_id}, 新增金额: {amount}")
            
            conn.close()
            
        except sqlite3.Error as e:
            logger.error(f"更新客户购买记录失败: {str(e)}")
    
    def get_customer_summary(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        获取客户综合信息（画像 + 最近跟进记录）
        
        Args:
            customer_id: 客户ID
            
        Returns:
            客户综合信息
        """
        profile = self.get_customer_profile(customer_id)
        if not profile:
            return None
        
        records = self.get_follow_up_records(customer_id, limit=5)
        
        return {
            "profile": profile.to_dict(),
            "recent_follow_ups": [r.to_dict() for r in records],
            "total_follow_ups": len(self.get_follow_up_records(customer_id))
        }


# 全局客户服务实例
customer_service = CustomerService()


def get_customer_service() -> CustomerService:
    """
    获取客户服务实例
    
    Returns:
        客户服务实例
    """
    return customer_service