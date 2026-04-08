"""
MongoDB 客户端封装

提供 MongoDB 数据库的连接和操作封装
"""

from typing import Optional, List, Dict, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configurations.db_config import MONGODB_CONFIG
from utils.logger import get_logger


logger = get_logger("MongoClient")


class MongoClientWrapper:
    """
    MongoDB 客户端封装类
    
    提供 MongoDB 的连接管理和文档操作
    """
    
    _instance: Optional['MongoClientWrapper'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls) -> 'MongoClientWrapper':
        """
        单例模式
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化 MongoDB 客户端
        """
        if self._client is None:
            self._connect()
    
    def _connect(self) -> None:
        """
        连接 MongoDB
        """
        try:
            self._client = MongoClient(
                host=MONGODB_CONFIG["HOST"],
                port=MONGODB_CONFIG["PORT"],
                serverSelectionTimeoutMS=MONGODB_CONFIG["CONNECTION_TIMEOUT"] * 1000
            )
            self._db = self._client[MONGODB_CONFIG["DB_NAME"]]
            self._client.admin.command('ping')
            logger.info("MongoDB 连接成功")
        except Exception as e:
            logger.error(f"MongoDB 连接失败: {e}")
            raise
    
    def get_client(self) -> MongoClient:
        """
        获取 MongoDB 客户端实例
        
        Returns:
            MongoClient: MongoDB 客户端
        """
        return self._client
    
    def get_database(self) -> Database:
        """
        获取数据库实例
        
        Returns:
            Database: 数据库实例
        """
        return self._db
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        获取集合
        
        Args:
            collection_name: 集合名称
        
        Returns:
            Collection: 集合实例
        """
        return self._db[collection_name]
    
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        """
        插入单个文档
        
        Args:
            collection_name: 集合名称
            document: 文档数据
        
        Returns:
            Optional[str]: 插入的文档ID
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_one(document)
            logger.debug(f"MongoDB 插入文档: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"MongoDB 插入文档失败: {e}")
            return None
    
    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """
        批量插入文档
        
        Args:
            collection_name: 集合名称
            documents: 文档列表
        
        Returns:
            List[str]: 插入的文档ID列表
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.insert_many(documents)
            logger.debug(f"MongoDB 批量插入: {len(result.inserted_ids)} 条")
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            logger.error(f"MongoDB 批量插入失败: {e}")
            return []
    
    def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        查询单个文档
        
        Args:
            collection_name: 集合名称
            query: 查询条件
        
        Returns:
            Optional[Dict[str, Any]]: 文档数据
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.find_one(query)
            if result:
                result["_id"] = str(result["_id"])
            return result
        except Exception as e:
            logger.error(f"MongoDB 查询单个文档失败: {e}")
            return None
    
    def find_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        limit: int = 0,
        skip: int = 0,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """
        查询多个文档
        
        Args:
            collection_name: 集合名称
            query: 查询条件
            limit: 返回数量限制
            skip: 跳过数量
            sort: 排序规则
        
        Returns:
            List[Dict[str, Any]]: 文档列表
        """
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.find(query)
            
            if sort:
                cursor = cursor.sort(sort)
            if skip > 0:
                cursor = cursor.skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)
            
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)
            
            logger.debug(f"MongoDB 查询: {len(results)} 条")
            return results
        except Exception as e:
            logger.error(f"MongoDB 查询多个文档失败: {e}")
            return []
    
    def update_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """
        更新单个文档
        
        Args:
            collection_name: 集合名称
            query: 查询条件
            update: 更新数据
            upsert: 是否插入不存在文档
        
        Returns:
            bool: 是否成功
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_one(query, {"$set": update}, upsert=upsert)
            logger.debug(f"MongoDB 更新: {result.modified_count} 条")
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"MongoDB 更新文档失败: {e}")
            return False
    
    def update_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """
        批量更新文档
        
        Args:
            collection_name: 集合名称
            query: 查询条件
            update: 更新数据
        
        Returns:
            int: 更新数量
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.update_many(query, {"$set": update})
            logger.debug(f"MongoDB 批量更新: {result.modified_count} 条")
            return result.modified_count
        except Exception as e:
            logger.error(f"MongoDB 批量更新失败: {e}")
            return 0
    
    def delete_one(self, collection_name: str, query: Dict[str, Any]) -> bool:
        """
        删除单个文档
        
        Args:
            collection_name: 集合名称
            query: 查询条件
        
        Returns:
            bool: 是否成功
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_one(query)
            logger.debug(f"MongoDB 删除: {result.deleted_count} 条")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"MongoDB 删除文档失败: {e}")
            return False
    
    def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        批量删除文档
        
        Args:
            collection_name: 集合名称
            query: 查询条件
        
        Returns:
            int: 删除数量
        """
        try:
            collection = self.get_collection(collection_name)
            result = collection.delete_many(query)
            logger.debug(f"MongoDB 批量删除: {result.deleted_count} 条")
            return result.deleted_count
        except Exception as e:
            logger.error(f"MongoDB 批量删除失败: {e}")
            return 0
    
    def count(self, collection_name: str, query: Dict[str, Any] = None) -> int:
        """
        统计文档数量
        
        Args:
            collection_name: 集合名称
            query: 查询条件
        
        Returns:
            int: 文档数量
        """
        try:
            collection = self.get_collection(collection_name)
            if query is None:
                query = {}
            return collection.count_documents(query)
        except Exception as e:
            logger.error(f"MongoDB 统计失败: {e}")
            return 0
    
    def create_index(self, collection_name: str, keys: List[tuple], unique: bool = False) -> bool:
        """
        创建索引
        
        Args:
            collection_name: 集合名称
            keys: 索引键列表 [(field, direction), ...]
            unique: 是否唯一索引
        
        Returns:
            bool: 是否成功
        """
        try:
            collection = self.get_collection(collection_name)
            collection.create_index(keys, unique=unique)
            logger.info(f"MongoDB 创建索引: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"MongoDB 创建索引失败: {e}")
            return False
    
    def close(self) -> None:
        """
        关闭连接
        """
        try:
            if self._client:
                self._client.close()
                logger.info("MongoDB 连接已关闭")
        except Exception as e:
            logger.error(f"MongoDB 关闭连接失败: {e}")


def get_mongo_client() -> MongoClientWrapper:
    """
    获取 MongoDB 客户端实例
    
    Returns:
        MongoClientWrapper: MongoDB 客户端
    """
    return MongoClientWrapper()
