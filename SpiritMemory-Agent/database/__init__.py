"""
数据库模块

包含所有数据库客户端的封装
"""

# 导出所有数据库客户端
from .redis_client import RedisClient, get_redis_client
from .milvus_client import MilvusClient, get_milvus_client
from .mongo_client import MongoClient, get_mongo_client

__all__ = [
    # Redis
    'RedisClient',
    'get_redis_client',
    
    # Milvus
    'MilvusClient',
    'get_milvus_client',
    
    # MongoDB
    'MongoClient',
    'get_mongo_client',
]
