"""
记忆实体结构

定义记忆的数据结构和基础操作
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.common_tools import generate_uuid, get_current_time, format_datetime
from utils.logger import get_logger


logger = get_logger("MemoryEntity")


@dataclass
class MemoryEntity:
    """
    记忆实体类
    
    定义记忆的完整数据结构
    """
    
    memory_id: str = field(default_factory=generate_uuid)
    user_id: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    emotion_tag: str = ""
    weight: float = 1.0
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    expire_type: str = "session"
    status: str = "active"
    memory_type: str = "short_term"
    embedding: Optional[List[float]] = None
    access_count: int = 0
    last_access_time: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    created_at: str = field(default_factory=lambda: format_datetime())
    updated_at: str = field(default_factory=lambda: format_datetime())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 字典数据
        """
        return {
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "content": self.content,
            "tags": self.tags,
            "emotion_tag": self.emotion_tag,
            "weight": self.weight,
            "timestamp": self.timestamp,
            "expire_type": self.expire_type,
            "status": self.status,
            "memory_type": self.memory_type,
            "embedding": self.embedding,
            "access_count": self.access_count,
            "last_access_time": self.last_access_time,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        """
        转换为JSON字符串
        
        Returns:
            str: JSON字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntity':
        """
        从字典创建实体
        
        Args:
            data: 字典数据
        
        Returns:
            MemoryEntity: 记忆实体
        """
        return cls(
            memory_id=data.get("memory_id", generate_uuid()),
            user_id=data.get("user_id", ""),
            content=data.get("content", ""),
            tags=data.get("tags", []),
            emotion_tag=data.get("emotion_tag", ""),
            weight=data.get("weight", 1.0),
            timestamp=data.get("timestamp", int(datetime.now().timestamp())),
            expire_type=data.get("expire_type", "session"),
            status=data.get("status", "active"),
            memory_type=data.get("memory_type", "short_term"),
            embedding=data.get("embedding"),
            access_count=data.get("access_count", 0),
            last_access_time=data.get("last_access_time", int(datetime.now().timestamp())),
            created_at=data.get("created_at", format_datetime()),
            updated_at=data.get("updated_at", format_datetime()),
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MemoryEntity':
        """
        从JSON字符串创建实体
        
        Args:
            json_str: JSON字符串
        
        Returns:
            MemoryEntity: 记忆实体
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update(self, **kwargs) -> None:
        """
        更新实体属性
        
        Args:
            **kwargs: 要更新的属性
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = format_datetime()
        logger.debug(f"记忆更新: {self.memory_id}")
    
    def access(self) -> None:
        """
        记录访问
        """
        self.access_count += 1
        self.last_access_time = int(datetime.now().timestamp())
        self.updated_at = format_datetime()
        logger.debug(f"记忆访问: {self.memory_id}, 访问次数: {self.access_count}")
    
    def is_expired(self) -> bool:
        """
        检查是否过期
        
        Returns:
            bool: 是否过期
        """
        if self.status == "expired":
            return True
        
        current_time = int(datetime.now().timestamp())
        expire_seconds = {
            "session": 3600,
            "daily": 86400,
            "weekly": 86400 * 7,
            "monthly": 86400 * 30,
            "permanent": 86400 * 365 * 10,
        }
        
        expire_time = expire_seconds.get(self.expire_type, 3600)
        return (current_time - self.timestamp) > expire_time
    
    def calculate_decay_weight(self, decay_rate: float = 0.01) -> float:
        """
        计算时间衰减后的权重
        
        Args:
            decay_rate: 衰减率
        
        Returns:
            float: 衰减后的权重
        """
        current_time = int(datetime.now().timestamp())
        time_diff = current_time - self.timestamp
        days = time_diff / 86400
        
        decayed_weight = self.weight * (1 - decay_rate) ** days
        return max(0.1, decayed_weight)
    
    def add_tag(self, tag: str) -> None:
        """
        添加标签
        
        Args:
            tag: 标签
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = format_datetime()
            logger.debug(f"添加标签: {tag}")
    
    def remove_tag(self, tag: str) -> None:
        """
        移除标签
        
        Args:
            tag: 标签
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = format_datetime()
            logger.debug(f"移除标签: {tag}")
    
    def set_embedding(self, embedding: List[float]) -> None:
        """
        设置向量
        
        Args:
            embedding: 向量
        """
        self.embedding = embedding
        self.updated_at = format_datetime()
        logger.debug(f"设置向量: 维度={len(embedding)}")
    
    def __repr__(self) -> str:
        return f"MemoryEntity(id={self.memory_id}, type={self.memory_type}, weight={self.weight:.2f})"


def create_memory(
    user_id: str,
    content: str,
    tags: Optional[List[str]] = None,
    emotion_tag: str = "",
    memory_type: str = "short_term",
    expire_type: str = "session",
    weight: float = 1.0,
    metadata: Optional[Dict[str, Any]] = None,
) -> MemoryEntity:
    """
    创建记忆实体
    
    Args:
        user_id: 用户ID
        content: 内容
        tags: 标签列表
        emotion_tag: 情感标签
        memory_type: 记忆类型
        expire_type: 过期类型
        weight: 权重
        metadata: 元数据
    
    Returns:
        MemoryEntity: 记忆实体
    """
    memory = MemoryEntity(
        user_id=user_id,
        content=content,
        tags=tags or [],
        emotion_tag=emotion_tag,
        memory_type=memory_type,
        expire_type=expire_type,
        weight=weight,
        metadata=metadata or {},
    )
    logger.info(f"创建记忆: {memory.memory_id}")
    return memory
