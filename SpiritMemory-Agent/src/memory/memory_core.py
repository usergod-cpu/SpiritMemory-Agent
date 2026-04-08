"""
记忆操作核心类

实现记忆的创建、更新、删除、获取等核心操作
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
from utils.embedding_utils import EmbeddingGenerator
from utils.text_process import extract_keywords, preprocess_text
from utils.common_tools import generate_uuid, format_datetime
from .memory_config import (
    MEMORY_STORAGE_CONFIG,
    MEMORY_WEIGHT_CONFIG,
    MEMORY_LIFECYCLE_CONFIG,
    MEMORY_STATUS_CONFIG,
    MEMORY_REFINEMENT_CONFIG,
)
from .memory_entity import MemoryEntity, create_memory
from .memory_strategy import MemoryStrategy
from .hybrid_retrieval import HybridRetrieval


logger = get_logger("MemoryCore")


class MemoryCore:
    """
    记忆核心操作类
    
    实现记忆的全生命周期管理
    """
    
    def __init__(self, embedding_generator: Optional[EmbeddingGenerator] = None):
        """
        初始化记忆核心
        
        Args:
            embedding_generator: 向量生成器
        """
        self.redis_client = get_redis_client()
        self.milvus_client = get_milvus_client()
        self.mongo_client = get_mongo_client()
        
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
        self.strategy = MemoryStrategy()
        self.retrieval = HybridRetrieval(self.embedding_generator)
        
        self.hot_config = MEMORY_STORAGE_CONFIG["HOT_MEMORY"]
        self.warm_config = MEMORY_STORAGE_CONFIG["WARM_MEMORY"]
        self.cold_config = MEMORY_STORAGE_CONFIG["COLD_MEMORY"]
        
        self.weight_config = MEMORY_WEIGHT_CONFIG
        self.lifecycle_config = MEMORY_LIFECYCLE_CONFIG
        self.refinement_config = MEMORY_REFINEMENT_CONFIG
    
    def create_memory(
        self,
        user_id: str,
        content: str,
        tags: Optional[List[str]] = None,
        emotion_tag: str = "",
        memory_type: str = "short_term",
        expire_type: str = "session",
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[MemoryEntity]:
        """
        创建记忆
        
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
            Optional[MemoryEntity]: 记忆实体
        """
        try:
            processed_content = preprocess_text(content)
            
            if self.refinement_config["ENABLE_AUTO_TAG"] and not tags:
                tags = extract_keywords(processed_content, max_keywords=5)
            
            if self.refinement_config["ENABLE_AUTO_WEIGHT"]:
                weight = self._calculate_initial_weight(content, tags or [])
            
            embedding = self.embedding_generator.encode(processed_content)
            
            memory = create_memory(
                user_id=user_id,
                content=processed_content,
                tags=tags or [],
                emotion_tag=emotion_tag,
                memory_type=memory_type,
                expire_type=expire_type,
                weight=weight,
                metadata=metadata or {},
            )
            
            memory.set_embedding(embedding)
            
            level = self.strategy.classify_memory(memory)
            
            if level == "hot":
                self.strategy.store_to_hot(memory)
            elif level == "warm":
                self.strategy.store_to_warm(memory)
                self.strategy.store_to_hot(memory)
            else:
                self.strategy.store_to_cold(memory)
            
            self._store_metadata(memory)
            
            logger.info(f"创建记忆成功: {memory.memory_id}")
            return memory
        except Exception as e:
            logger.error(f"创建记忆失败: {e}")
            return None
    
    def update_memory(
        self,
        memory_id: str,
        **kwargs
    ) -> bool:
        """
        更新记忆
        
        Args:
            memory_id: 记忆ID
            **kwargs: 要更新的属性
        
        Returns:
            bool: 是否成功
        """
        try:
            memory = self.get_memory(memory_id)
            if not memory:
                logger.warning(f"记忆不存在: {memory_id}")
                return False
            
            if "content" in kwargs:
                kwargs["content"] = preprocess_text(kwargs["content"])
                kwargs["embedding"] = self.embedding_generator.encode(kwargs["content"])
            
            memory.update(**kwargs)
            
            level = self.strategy.classify_memory(memory)
            
            if level == "hot":
                self.strategy.store_to_hot(memory)
            elif level == "warm":
                self.strategy.store_to_warm(memory)
            
            self._update_metadata(memory)
            
            logger.info(f"更新记忆成功: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
            return False
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            bool: 是否成功
        """
        try:
            self.strategy.delete_from_hot(memory_id)
            self.strategy.delete_from_warm(memory_id)
            self.strategy.delete_from_cold(memory_id)
            
            logger.info(f"删除记忆成功: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return False
    
    def get_memory(self, memory_id: str) -> Optional[MemoryEntity]:
        """
        获取单条记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            Optional[MemoryEntity]: 记忆实体
        """
        try:
            memory = self.strategy.get_from_hot(memory_id)
            if memory:
                memory.access()
                self.strategy.store_to_hot(memory)
                return memory
            
            memory = self.strategy.get_from_warm(memory_id)
            if memory:
                memory.access()
                return memory
            
            memory = self.strategy.get_from_cold(memory_id)
            if memory:
                return memory
            
            return None
        except Exception as e:
            logger.error(f"获取记忆失败: {e}")
            return None
    
    def batch_insert(
        self,
        memories_data: List[Dict[str, Any]]
    ) -> List[str]:
        """
        批量插入记忆
        
        Args:
            memories_data: 记忆数据列表
        
        Returns:
            List[str]: 记忆ID列表
        """
        try:
            memory_ids = []
            
            for data in memories_data:
                memory = self.create_memory(**data)
                if memory:
                    memory_ids.append(memory.memory_id)
            
            logger.info(f"批量插入完成: {len(memory_ids)} 条记忆")
            return memory_ids
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            return []
    
    def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        emotion_tag: Optional[str] = None,
        top_k: int = 10,
        memory_type: Optional[str] = None,
    ) -> List[MemoryEntity]:
        """
        搜索记忆
        
        Args:
            query: 查询文本
            user_id: 用户ID
            tags: 标签过滤
            emotion_tag: 情感标签
            top_k: 返回数量
            memory_type: 记忆类型
        
        Returns:
            List[MemoryEntity]: 记忆列表
        """
        try:
            return self.retrieval.search(
                query=query,
                user_id=user_id,
                tags=tags,
                emotion_tag=emotion_tag,
                top_k=top_k,
                memory_type=memory_type,
            )
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []
    
    def get_user_memories(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[MemoryEntity]:
        """
        获取用户所有记忆
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            offset: 偏移量
        
        Returns:
            List[MemoryEntity]: 记忆列表
        """
        try:
            results = self.mongo_client.find_many(
                collection_name=self.cold_config["COLLECTION_NAME"],
                query={"user_id": user_id},
                limit=limit,
                skip=offset,
                sort=[("timestamp", -1)]
            )
            
            memories = [MemoryEntity.from_dict(data) for data in results]
            logger.info(f"获取用户记忆: {len(memories)} 条")
            return memories
        except Exception as e:
            logger.error(f"获取用户记忆失败: {e}")
            return []
    
    def refine_memory(self, memory_id: str) -> bool:
        """
        精炼记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            bool: 是否成功
        """
        try:
            memory = self.get_memory(memory_id)
            if not memory:
                return False
            
            if self.refinement_config["ENABLE_AUTO_TAG"]:
                new_tags = extract_keywords(memory.content, max_keywords=5)
                for tag in new_tags:
                    memory.add_tag(tag)
            
            if self.refinement_config["ENABLE_AUTO_WEIGHT"]:
                memory.weight = self._calculate_initial_weight(
                    memory.content,
                    memory.tags
                )
            
            if self.refinement_config["ENABLE_TIME_DECAY"]:
                memory.weight = memory.calculate_decay_weight(
                    self.weight_config["TIME_DECAY_RATE"]
                )
            
            self.update_memory(memory_id, **memory.to_dict())
            
            logger.info(f"精炼记忆成功: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"精炼记忆失败: {e}")
            return False
    
    def detect_conflicts(self, memory: MemoryEntity) -> List[MemoryEntity]:
        """
        检测冲突记忆
        
        Args:
            memory: 记忆实体
        
        Returns:
            List[MemoryEntity]: 冲突记忆列表
        """
        try:
            if not self.refinement_config["ENABLE_CONFLICT_DETECT"]:
                return []
            
            similar_memories = self.retrieval.search(
                query=memory.content,
                user_id=memory.user_id,
                top_k=10
            )
            
            conflicts = []
            threshold = self.lifecycle_config["CONFLICT_SIMILARITY_THRESHOLD"]
            
            for similar in similar_memories:
                if similar.memory_id == memory.memory_id:
                    continue
                
                if similar.metadata.get("retrieval_score", 0) >= threshold:
                    conflicts.append(similar)
            
            logger.debug(f"检测到 {len(conflicts)} 条冲突记忆")
            return conflicts
        except Exception as e:
            logger.error(f"冲突检测失败: {e}")
            return []
    
    def mark_expired(self, memory_id: str) -> bool:
        """
        标记记忆失效
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            bool: 是否成功
        """
        try:
            return self.update_memory(
                memory_id,
                status=MEMORY_STATUS_CONFIG["STATUS_EXPIRED"]
            )
        except Exception as e:
            logger.error(f"标记失效失败: {e}")
            return False
    
    def auto_downgrade(self) -> int:
        """
        自动降级记忆
        
        Returns:
            int: 降级数量
        """
        try:
            downgraded = 0
            threshold = self.lifecycle_config["DOWNGRADE_THRESHOLD"]
            
            query = {"weight": {"$lt": threshold}}
            results = self.mongo_client.find_many(
                collection_name=self.cold_config["COLLECTION_NAME"],
                query=query,
                limit=100
            )
            
            for data in results:
                memory = MemoryEntity.from_dict(data)
                self.strategy.downgrade_memory(memory)
                downgraded += 1
            
            logger.info(f"自动降级完成: {downgraded} 条记忆")
            return downgraded
        except Exception as e:
            logger.error(f"自动降级失败: {e}")
            return 0
    
    def _calculate_initial_weight(
        self,
        content: str,
        tags: List[str]
    ) -> float:
        """
        计算初始权重
        
        Args:
            content: 内容
            tags: 标签
        
        Returns:
            float: 权重
        """
        try:
            weight = self.weight_config["DEFAULT_WEIGHT"]
            
            if len(content) > 200:
                weight += 0.5
            
            if len(tags) > 3:
                weight += 0.3
            
            return min(weight, self.weight_config["MAX_WEIGHT"])
        except Exception as e:
            logger.error(f"计算初始权重失败: {e}")
            return self.weight_config["DEFAULT_WEIGHT"]
    
    def _store_metadata(self, memory: MemoryEntity) -> bool:
        """
        存储记忆元数据
        
        Args:
            memory: 记忆实体
        
        Returns:
            bool: 是否成功
        """
        try:
            metadata = {
                "memory_id": memory.memory_id,
                "user_id": memory.user_id,
                "memory_type": memory.memory_type,
                "status": memory.status,
                "created_at": memory.created_at,
            }
            
            self.mongo_client.insert_one(
                collection_name=f"{self.cold_config['COLLECTION_NAME']}_metadata",
                document=metadata
            )
            return True
        except Exception as e:
            logger.error(f"存储元数据失败: {e}")
            return False
    
    def _update_metadata(self, memory: MemoryEntity) -> bool:
        """
        更新记忆元数据
        
        Args:
            memory: 记忆实体
        
        Returns:
            bool: 是否成功
        """
        try:
            self.mongo_client.update_one(
                collection_name=f"{self.cold_config['COLLECTION_NAME']}_metadata",
                query={"memory_id": memory.memory_id},
                update={
                    "status": memory.status,
                    "updated_at": memory.updated_at,
                }
            )
            return True
        except Exception as e:
            logger.error(f"更新元数据失败: {e}")
            return False


def get_memory_core() -> MemoryCore:
    """
    获取记忆核心实例
    
    Returns:
        MemoryCore: 记忆核心实例
    """
    return MemoryCore()
