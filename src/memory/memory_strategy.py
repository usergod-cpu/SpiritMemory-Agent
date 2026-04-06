"""
三层记忆分流策略

实现热、温、冷三层记忆的分流和管理策略
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.redis_client import get_redis_client
from database.milvus_client import get_milvus_client
from database.mongo_client import get_mongo_client
from utils.logger import get_logger
from utils.common import format_datetime
from .memory_config import (
    MEMORY_STORAGE_CONFIG,
    MEMORY_WEIGHT_CONFIG,
    MEMORY_LIFECYCLE_CONFIG,
    MEMORY_STATUS_CONFIG,
)
from .memory_entity import MemoryEntity


logger = get_logger("MemoryStrategy")


class MemoryStrategy:
    """
    记忆分流策略类
    
    实现热、温、冷三层记忆的分流和管理
    """
    
    def __init__(self):
        """
        初始化记忆策略
        """
        self.redis_client = get_redis_client()
        self.milvus_client = get_milvus_client()
        self.mongo_client = get_mongo_client()
        
        self.hot_config = MEMORY_STORAGE_CONFIG["HOT_MEMORY"]
        self.warm_config = MEMORY_STORAGE_CONFIG["WARM_MEMORY"]
        self.cold_config = MEMORY_STORAGE_CONFIG["COLD_MEMORY"]
        
        self._init_collections()
    
    def _init_collections(self) -> None:
        """
        初始化集合
        """
        try:
            self.milvus_client.create_collection(
                collection_name=self.warm_config["COLLECTION_NAME"],
                dimension=self.warm_config["DIMENSION"],
                description="温记忆向量存储"
            )
            logger.info("Milvus 集合初始化成功")
        except Exception as e:
            logger.error(f"Milvus 集合初始化失败: {e}")
    
    def classify_memory(self, memory: MemoryEntity) -> str:
        """
        分类记忆到合适的层级
        
        Args:
            memory: 记忆实体
        
        Returns:
            str: 层级 (hot/warm/cold)
        """
        if memory.status == MEMORY_STATUS_CONFIG["STATUS_ARCHIVED"]:
            return "cold"
        
        if memory.status == MEMORY_STATUS_CONFIG["STATUS_EXPIRED"]:
            return "cold"
        
        if memory.memory_type == "short_term" and memory.access_count < 5:
            return "hot"
        
        if memory.memory_type in ["long_term", "important"]:
            return "warm"
        
        if memory.weight > MEMORY_WEIGHT_CONFIG["DEFAULT_WEIGHT"]:
            return "warm"
        
        if memory.access_count >= 5:
            return "warm"
        
        return "hot"
    
    def store_to_hot(self, memory: MemoryEntity) -> bool:
        """
        存储到热记忆（Redis）
        
        Args:
            memory: 记忆实体
        
        Returns:
            bool: 是否成功
        """
        try:
            key = f"{self.hot_config['PREFIX']}{memory.memory_id}"
            value = memory.to_json()
            ttl = self.hot_config["DEFAULT_TTL"]
            
            if memory.expire_type == "session":
                ttl = 3600
            elif memory.expire_type == "daily":
                ttl = 86400
            elif memory.expire_type == "weekly":
                ttl = 86400 * 7
            elif memory.expire_type == "monthly":
                ttl = 86400 * 30
            
            self.redis_client.set(key, value, ex=ttl)
            
            self.redis_client.zadd(
                f"{self.hot_config['PREFIX']}timeline",
                {memory.memory_id: memory.timestamp}
            )
            
            logger.info(f"存储热记忆: {memory.memory_id}")
            return True
        except Exception as e:
            logger.error(f"存储热记忆失败: {e}")
            return False
    
    def store_to_warm(self, memory: MemoryEntity) -> bool:
        """
        存储到温记忆（Milvus）
        
        Args:
            memory: 记忆实体
        
        Returns:
            bool: 是否成功
        """
        try:
            if not memory.embedding:
                logger.warning(f"记忆无向量，跳过温存储: {memory.memory_id}")
                return False
            
            data = [{
                "id": memory.memory_id,
                "embedding": memory.embedding,
                "content": memory.content[:2048],
                "user_id": memory.user_id,
                "timestamp": memory.timestamp,
            }]
            
            self.milvus_client.insert(
                collection_name=self.warm_config["COLLECTION_NAME"],
                data=data
            )
            
            logger.info(f"存储温记忆: {memory.memory_id}")
            return True
        except Exception as e:
            logger.error(f"存储温记忆失败: {e}")
            return False
    
    def store_to_cold(self, memory: MemoryEntity) -> bool:
        """
        存储到冷记忆（MongoDB）
        
        Args:
            memory: 记忆实体
        
        Returns:
            bool: 是否成功
        """
        try:
            document = memory.to_dict()
            document["archived_at"] = format_datetime()
            
            self.mongo_client.insert_one(
                collection_name=self.cold_config["COLLECTION_NAME"],
                document=document
            )
            
            logger.info(f"存储冷记忆: {memory.memory_id}")
            return True
        except Exception as e:
            logger.error(f"存储冷记忆失败: {e}")
            return False
    
    def get_from_hot(self, memory_id: str) -> Optional[MemoryEntity]:
        """
        从热记忆获取
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            Optional[MemoryEntity]: 记忆实体
        """
        try:
            key = f"{self.hot_config['PREFIX']}{memory_id}"
            value = self.redis_client.get(key)
            
            if value:
                memory = MemoryEntity.from_json(value)
                memory.access()
                self.store_to_hot(memory)
                logger.debug(f"获取热记忆: {memory_id}")
                return memory
            return None
        except Exception as e:
            logger.error(f"获取热记忆失败: {e}")
            return None
    
    def get_from_warm(self, memory_id: str) -> Optional[MemoryEntity]:
        """
        从温记忆获取
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            Optional[MemoryEntity]: 记忆实体
        """
        try:
            results = self.mongo_client.find_one(
                collection_name=self.cold_config["COLLECTION_NAME"],
                query={"memory_id": memory_id}
            )
            
            if results:
                memory = MemoryEntity.from_dict(results)
                logger.debug(f"获取温记忆: {memory_id}")
                return memory
            return None
        except Exception as e:
            logger.error(f"获取温记忆失败: {e}")
            return None
    
    def get_from_cold(self, memory_id: str) -> Optional[MemoryEntity]:
        """
        从冷记忆获取
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            Optional[MemoryEntity]: 记忆实体
        """
        try:
            results = self.mongo_client.find_one(
                collection_name=self.cold_config["COLLECTION_NAME"],
                query={"memory_id": memory_id}
            )
            
            if results:
                memory = MemoryEntity.from_dict(results)
                logger.debug(f"获取冷记忆: {memory_id}")
                return memory
            return None
        except Exception as e:
            logger.error(f"获取冷记忆失败: {e}")
            return None
    
    def delete_from_hot(self, memory_id: str) -> bool:
        """
        从热记忆删除
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            bool: 是否成功
        """
        try:
            key = f"{self.hot_config['PREFIX']}{memory_id}"
            self.redis_client.delete(key)
            logger.info(f"删除热记忆: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"删除热记忆失败: {e}")
            return False
    
    def delete_from_warm(self, memory_id: str) -> bool:
        """
        从温记忆删除
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            bool: 是否成功
        """
        try:
            self.milvus_client.delete(
                collection_name=self.warm_config["COLLECTION_NAME"],
                ids=[memory_id]
            )
            logger.info(f"删除温记忆: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"删除温记忆失败: {e}")
            return False
    
    def delete_from_cold(self, memory_id: str) -> bool:
        """
        从冷记忆删除
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            bool: 是否成功
        """
        try:
            self.mongo_client.delete_one(
                collection_name=self.cold_config["COLLECTION_NAME"],
                query={"memory_id": memory_id}
            )
            logger.info(f"删除冷记忆: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"删除冷记忆失败: {e}")
            return False
    
    def upgrade_memory(self, memory: MemoryEntity) -> bool:
        """
        升级记忆（从冷到温，从温到热）
        
        Args:
            memory: 记忆实体
        
        Returns:
            bool: 是否成功
        """
        try:
            current_level = self.classify_memory(memory)
            
            if current_level == "cold":
                self.store_to_warm(memory)
                logger.info(f"记忆升级: cold -> warm, {memory.memory_id}")
            elif current_level == "warm":
                self.store_to_hot(memory)
                logger.info(f"记忆升级: warm -> hot, {memory.memory_id}")
            
            return True
        except Exception as e:
            logger.error(f"记忆升级失败: {e}")
            return False
    
    def downgrade_memory(self, memory: MemoryEntity) -> bool:
        """
        降级记忆（从热到温，从温到冷）
        
        Args:
            memory: 记忆实体
        
        Returns:
            bool: 是否成功
        """
        try:
            current_level = self.classify_memory(memory)
            
            if current_level == "hot":
                self.delete_from_hot(memory.memory_id)
                if memory.embedding:
                    self.store_to_warm(memory)
                else:
                    self.store_to_cold(memory)
                logger.info(f"记忆降级: hot -> warm/cold, {memory.memory_id}")
            elif current_level == "warm":
                self.delete_from_warm(memory.memory_id)
                self.store_to_cold(memory)
                logger.info(f"记忆降级: warm -> cold, {memory.memory_id}")
            
            return True
        except Exception as e:
            logger.error(f"记忆降级失败: {e}")
            return False
    
    def auto_cleanup(self) -> int:
        """
        自动清理过期记忆
        
        Returns:
            int: 清理数量
        """
        try:
            cleaned = 0
            
            timeline_key = f"{self.hot_config['PREFIX']}timeline"
            memories = self.redis_client.zrange(timeline_key, 0, -1, withscores=True)
            
            for memory_id, timestamp in memories:
                memory = self.get_from_hot(memory_id)
                if memory and memory.is_expired():
                    self.downgrade_memory(memory)
                    cleaned += 1
            
            logger.info(f"自动清理完成: 清理 {cleaned} 条记忆")
            return cleaned
        except Exception as e:
            logger.error(f"自动清理失败: {e}")
            return 0
