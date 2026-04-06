"""
Milvus 客户端封装

提供 Milvus 向量数据库的连接和操作封装
"""

from typing import Optional, List, Dict, Any
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import MILVUS_CONFIG
from utils.logger import get_logger


logger = get_logger("MilvusClient")


class MilvusClient:
    """
    Milvus 客户端封装类
    
    提供 Milvus 的连接管理和向量操作
    """
    
    _instance: Optional['MilvusClient'] = None
    _connected: bool = False
    
    def __new__(cls) -> 'MilvusClient':
        """
        单例模式
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化 Milvus 客户端
        """
        if not self._connected:
            self._connect()
    
    def _connect(self) -> None:
        """
        连接 Milvus
        """
        try:
            connections.connect(
                alias="default",
                host=MILVUS_CONFIG["HOST"],
                port=MILVUS_CONFIG["PORT"]
            )
            self._connected = True
            logger.info("Milvus 连接成功")
        except Exception as e:
            logger.error(f"Milvus 连接失败: {e}")
            raise
    
    def create_collection(
        self,
        collection_name: str,
        dimension: int,
        description: str = ""
    ) -> bool:
        """
        创建集合
        
        Args:
            collection_name: 集合名称
            dimension: 向量维度
            description: 集合描述
        
        Returns:
            bool: 是否成功
        """
        try:
            if utility.has_collection(collection_name):
                logger.warning(f"集合已存在: {collection_name}")
                return True
            
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=2048),
                FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="timestamp", dtype=DataType.INT64)
            ]
            
            schema = CollectionSchema(fields=fields, description=description)
            collection = Collection(name=collection_name, schema=schema)
            
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            
            logger.info(f"集合创建成功: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            return False
    
    def drop_collection(self, collection_name: str) -> bool:
        """
        删除集合
        
        Args:
            collection_name: 集合名称
        
        Returns:
            bool: 是否成功
        """
        try:
            if utility.has_collection(collection_name):
                utility.drop_collection(collection_name)
                logger.info(f"集合删除成功: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return False
    
    def insert(
        self,
        collection_name: str,
        data: List[Dict[str, Any]]
    ) -> bool:
        """
        插入向量数据
        
        Args:
            collection_name: 集合名称
            data: 数据列表
        
        Returns:
            bool: 是否成功
        """
        try:
            collection = Collection(collection_name)
            
            ids = [item["id"] for item in data]
            embeddings = [item["embedding"] for item in data]
            contents = [item.get("content", "") for item in data]
            user_ids = [item.get("user_id", "") for item in data]
            timestamps = [item.get("timestamp", 0) for item in data]
            
            insert_data = [ids, embeddings, contents, user_ids, timestamps]
            collection.insert(insert_data)
            collection.flush()
            
            logger.info(f"插入数据成功: {len(data)} 条")
            return True
        except Exception as e:
            logger.error(f"插入数据失败: {e}")
            return False
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        向量检索
        
        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            top_k: 返回数量
            filter_expr: 过滤表达式
        
        Returns:
            List[Dict[str, Any]]: 检索结果
        """
        try:
            collection = Collection(collection_name)
            collection.load()
            
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            results = collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=["id", "content", "user_id", "timestamp"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        "id": hit.entity.get("id"),
                        "score": hit.score,
                        "content": hit.entity.get("content"),
                        "user_id": hit.entity.get("user_id"),
                        "timestamp": hit.entity.get("timestamp")
                    })
            
            logger.debug(f"检索完成: 返回 {len(search_results)} 条结果")
            return search_results
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []
    
    def delete(
        self,
        collection_name: str,
        ids: List[str]
    ) -> bool:
        """
        删除向量
        
        Args:
            collection_name: 集合名称
            ids: ID列表
        
        Returns:
            bool: 是否成功
        """
        try:
            collection = Collection(collection_name)
            expr = f'id in {ids}'
            collection.delete(expr)
            collection.flush()
            
            logger.info(f"删除数据成功: {len(ids)} 条")
            return True
        except Exception as e:
            logger.error(f"删除数据失败: {e}")
            return False
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        获取集合统计信息
        
        Args:
            collection_name: 集合名称
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            collection = Collection(collection_name)
            stats = collection.num_entities
            return {
                "collection_name": collection_name,
                "num_entities": stats
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def close(self) -> None:
        """
        关闭连接
        """
        try:
            connections.disconnect("default")
            self._connected = False
            logger.info("Milvus 连接已关闭")
        except Exception as e:
            logger.error(f"Milvus 关闭连接失败: {e}")


def get_milvus_client() -> MilvusClient:
    """
    获取 Milvus 客户端实例
    
    Returns:
        MilvusClient: Milvus 客户端
    """
    return MilvusClient()
