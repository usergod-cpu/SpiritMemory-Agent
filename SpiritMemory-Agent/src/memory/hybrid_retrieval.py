"""
混合检索模块

实现向量相似度、标签过滤、时间衰减、权重加权的混合检索
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import math
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.redis_client import get_redis_client
from database.milvus_client import get_milvus_client
from database.mongo_client import get_mongo_client
from utils.logger import get_logger
from utils.embedding_utils import EmbeddingGenerator
from .memory_config import (
    MEMORY_STORAGE_CONFIG,
    MEMORY_RETRIEVAL_CONFIG,
    MEMORY_WEIGHT_CONFIG,
)
from .memory_entity import MemoryEntity


logger = get_logger("HybridRetrieval")


class HybridRetrieval:
    """
    混合检索类
    
    实现多维度融合的记忆检索
    """
    
    def __init__(self, embedding_generator: Optional[EmbeddingGenerator] = None):
        """
        初始化混合检索
        
        Args:
            embedding_generator: 向量生成器
        """
        self.redis_client = get_redis_client()
        self.milvus_client = get_milvus_client()
        self.mongo_client = get_mongo_client()
        
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
        
        self.hot_config = MEMORY_STORAGE_CONFIG["HOT_MEMORY"]
        self.warm_config = MEMORY_STORAGE_CONFIG["WARM_MEMORY"]
        self.cold_config = MEMORY_STORAGE_CONFIG["COLD_MEMORY"]
        
        self.retrieval_config = MEMORY_RETRIEVAL_CONFIG
        self.weight_config = MEMORY_WEIGHT_CONFIG
    
    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        emotion_tag: Optional[str] = None,
        top_k: int = 10,
        memory_type: Optional[str] = None,
    ) -> List[MemoryEntity]:
        """
        混合检索
        
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
            query_embedding = self.embedding_generator.encode(query)
            
            hot_memories = self._search_hot(user_id, tags)
            warm_memories = self._search_warm(query_embedding, user_id, top_k * 2)
            cold_memories = self._search_cold(user_id, tags, top_k)
            
            all_memories = hot_memories + warm_memories + cold_memories
            
            scored_memories = []
            for memory in all_memories:
                score = self._calculate_score(
                    memory=memory,
                    query_embedding=query_embedding,
                    query_tags=tags,
                    query_emotion=emotion_tag,
                    memory_type=memory_type
                )
                scored_memories.append((memory, score))
            
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            
            unique_memories = []
            seen_ids = set()
            for memory, score in scored_memories:
                if memory.memory_id not in seen_ids:
                    memory.metadata["retrieval_score"] = score
                    unique_memories.append(memory)
                    seen_ids.add(memory.memory_id)
                if len(unique_memories) >= top_k:
                    break
            
            logger.info(f"混合检索完成: 返回 {len(unique_memories)} 条记忆")
            return unique_memories
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return []
    
    def _search_hot(
        self,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[MemoryEntity]:
        """
        搜索热记忆
        
        Args:
            user_id: 用户ID
            tags: 标签过滤
        
        Returns:
            List[MemoryEntity]: 记忆列表
        """
        try:
            memories = []
            timeline_key = f"{self.hot_config['PREFIX']}timeline"
            memory_ids = self.redis_client.zrange(timeline_key, 0, -1)
            
            for memory_id in memory_ids:
                memory = self._get_hot_memory(memory_id)
                if memory:
                    if user_id and memory.user_id != user_id:
                        continue
                    if tags and not any(tag in memory.tags for tag in tags):
                        continue
                    memories.append(memory)
            
            logger.debug(f"热记忆搜索: {len(memories)} 条")
            return memories
        except Exception as e:
            logger.error(f"热记忆搜索失败: {e}")
            return []
    
    def _search_warm(
        self,
        query_embedding: List[float],
        user_id: Optional[str] = None,
        top_k: int = 20
    ) -> List[MemoryEntity]:
        """
        搜索温记忆
        
        Args:
            query_embedding: 查询向量
            user_id: 用户ID
            top_k: 返回数量
        
        Returns:
            List[MemoryEntity]: 记忆列表
        """
        try:
            filter_expr = None
            if user_id:
                filter_expr = f'user_id == "{user_id}"'
            
            results = self.milvus_client.search(
                collection_name=self.warm_config["COLLECTION_NAME"],
                query_vector=query_embedding,
                top_k=top_k,
                filter_expr=filter_expr
            )
            
            memories = []
            for result in results:
                memory = self._get_memory_by_id(result["id"])
                if memory:
                    memory.metadata["vector_score"] = result["score"]
                    memories.append(memory)
            
            logger.debug(f"温记忆搜索: {len(memories)} 条")
            return memories
        except Exception as e:
            logger.error(f"温记忆搜索失败: {e}")
            return []
    
    def _search_cold(
        self,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[MemoryEntity]:
        """
        搜索冷记忆
        
        Args:
            user_id: 用户ID
            tags: 标签过滤
            limit: 返回数量
        
        Returns:
            List[MemoryEntity]: 记忆列表
        """
        try:
            query = {}
            if user_id:
                query["user_id"] = user_id
            if tags:
                query["tags"] = {"$in": tags}
            
            results = self.mongo_client.find_many(
                collection_name=self.cold_config["COLLECTION_NAME"],
                query=query,
                limit=limit,
                sort=[("timestamp", -1)]
            )
            
            memories = [MemoryEntity.from_dict(data) for data in results]
            logger.debug(f"冷记忆搜索: {len(memories)} 条")
            return memories
        except Exception as e:
            logger.error(f"冷记忆搜索失败: {e}")
            return []
    
    def _calculate_score(
        self,
        memory: MemoryEntity,
        query_embedding: List[float],
        query_tags: Optional[List[str]] = None,
        query_emotion: Optional[str] = None,
        memory_type: Optional[str] = None,
    ) -> float:
        """
        计算综合得分
        
        Args:
            memory: 记忆实体
            query_embedding: 查询向量
            query_tags: 查询标签
            query_emotion: 查询情感
            memory_type: 记忆类型
        
        Returns:
            float: 综合得分
        """
        try:
            content_score = self._calculate_content_similarity(memory, query_embedding)
            tag_score = self._calculate_tag_similarity(memory, query_tags)
            emotion_score = self._calculate_emotion_similarity(memory, query_emotion)
            time_score = self._calculate_time_decay(memory)
            weight_score = self._calculate_weight_score(memory)
            
            total_score = (
                content_score * self.retrieval_config["CONTENT_WEIGHT"] +
                tag_score * self.retrieval_config["TAG_WEIGHT"] +
                emotion_score * self.retrieval_config["EMOTION_WEIGHT"] +
                time_score * self.retrieval_config["TIME_DECAY_WEIGHT"] +
                weight_score * 0.1
            )
            
            if memory_type and memory.memory_type != memory_type:
                total_score *= 0.5
            
            return total_score
        except Exception as e:
            logger.error(f"计算得分失败: {e}")
            return 0.0
    
    def _calculate_content_similarity(
        self,
        memory: MemoryEntity,
        query_embedding: List[float]
    ) -> float:
        """
        计算内容相似度
        
        Args:
            memory: 记忆实体
            query_embedding: 查询向量
        
        Returns:
            float: 相似度得分
        """
        try:
            if not memory.embedding:
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(memory.embedding, query_embedding))
            norm_a = math.sqrt(sum(a * a for a in memory.embedding))
            norm_b = math.sqrt(sum(b * b for b in query_embedding))
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            logger.error(f"计算内容相似度失败: {e}")
            return 0.0
    
    def _calculate_tag_similarity(
        self,
        memory: MemoryEntity,
        query_tags: Optional[List[str]] = None
    ) -> float:
        """
        计算标签相似度
        
        Args:
            memory: 记忆实体
            query_tags: 查询标签
        
        Returns:
            float: 标签相似度
        """
        try:
            if not query_tags or not memory.tags:
                return 0.0
            
            common_tags = set(query_tags) & set(memory.tags)
            return len(common_tags) / len(set(query_tags))
        except Exception as e:
            logger.error(f"计算标签相似度失败: {e}")
            return 0.0
    
    def _calculate_emotion_similarity(
        self,
        memory: MemoryEntity,
        query_emotion: Optional[str] = None
    ) -> float:
        """
        计算情感相似度
        
        Args:
            memory: 记忆实体
            query_emotion: 查询情感
        
        Returns:
            float: 情感相似度
        """
        try:
            if not query_emotion or not memory.emotion_tag:
                return 0.0
            
            return 1.0 if query_emotion == memory.emotion_tag else 0.0
        except Exception as e:
            logger.error(f"计算情感相似度失败: {e}")
            return 0.0
    
    def _calculate_time_decay(self, memory: MemoryEntity) -> float:
        """
        计算时间衰减得分
        
        Args:
            memory: 记忆实体
        
        Returns:
            float: 时间衰减得分
        """
        try:
            current_time = int(datetime.now().timestamp())
            time_diff = current_time - memory.timestamp
            hours = time_diff / 3600
            
            decay = math.exp(-hours * self.weight_config["TIME_DECAY_RATE"])
            return max(0.1, decay)
        except Exception as e:
            logger.error(f"计算时间衰减失败: {e}")
            return 0.5
    
    def _calculate_weight_score(self, memory: MemoryEntity) -> float:
        """
        计算权重得分
        
        Args:
            memory: 记忆实体
        
        Returns:
            float: 权重得分
        """
        try:
            normalized_weight = (
                (memory.weight - self.weight_config["MIN_WEIGHT"]) /
                (self.weight_config["MAX_WEIGHT"] - self.weight_config["MIN_WEIGHT"])
            )
            return max(0.0, min(1.0, normalized_weight))
        except Exception as e:
            logger.error(f"计算权重得分失败: {e}")
            return 0.5
    
    def _get_hot_memory(self, memory_id: str) -> Optional[MemoryEntity]:
        """
        获取热记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            Optional[MemoryEntity]: 记忆实体
        """
        try:
            key = f"{self.hot_config['PREFIX']}{memory_id}"
            value = self.redis_client.get(key)
            if value:
                return MemoryEntity.from_json(value)
            return None
        except Exception as e:
            logger.error(f"获取热记忆失败: {e}")
            return None
    
    def _get_memory_by_id(self, memory_id: str) -> Optional[MemoryEntity]:
        """
        根据ID获取记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            Optional[MemoryEntity]: 记忆实体
        """
        memory = self._get_hot_memory(memory_id)
        if memory:
            return memory
        
        memory = self.mongo_client.find_one(
            collection_name=self.cold_config["COLLECTION_NAME"],
            query={"memory_id": memory_id}
        )
        if memory:
            return MemoryEntity.from_dict(memory)
        
        return None
    
    def search_by_tags(
        self,
        tags: List[str],
        user_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[MemoryEntity]:
        """
        按标签搜索
        
        Args:
            tags: 标签列表
            user_id: 用户ID
            top_k: 返回数量
        
        Returns:
            List[MemoryEntity]: 记忆列表
        """
        try:
            query = {"tags": {"$in": tags}}
            if user_id:
                query["user_id"] = user_id
            
            results = self.mongo_client.find_many(
                collection_name=self.cold_config["COLLECTION_NAME"],
                query=query,
                limit=top_k,
                sort=[("weight", -1)]
            )
            
            memories = [MemoryEntity.from_dict(data) for data in results]
            logger.info(f"标签搜索完成: 返回 {len(memories)} 条记忆")
            return memories
        except Exception as e:
            logger.error(f"标签搜索失败: {e}")
            return []
    
    def search_by_time_range(
        self,
        start_time: int,
        end_time: int,
        user_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[MemoryEntity]:
        """
        按时间范围搜索
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            user_id: 用户ID
            top_k: 返回数量
        
        Returns:
            List[MemoryEntity]: 记忆列表
        """
        try:
            query = {
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }
            if user_id:
                query["user_id"] = user_id
            
            results = self.mongo_client.find_many(
                collection_name=self.cold_config["COLLECTION_NAME"],
                query=query,
                limit=top_k,
                sort=[("timestamp", -1)]
            )
            
            memories = [MemoryEntity.from_dict(data) for data in results]
            logger.info(f"时间范围搜索完成: 返回 {len(memories)} 条记忆")
            return memories
        except Exception as e:
            logger.error(f"时间范围搜索失败: {e}")
            return []
