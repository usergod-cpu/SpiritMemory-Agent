"""
Redis 客户端封装

提供 Redis 数据库的连接和操作封装
"""

import redis
from typing import Optional, Any, Dict, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db_config import REDIS_CONFIG
from utils.logger import get_logger


logger = get_logger("RedisClient")


class RedisClient:
    """
    Redis 客户端封装类
    
    提供 Redis 的连接管理和基础操作
    """
    
    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None
    
    def __new__(cls) -> 'RedisClient':
        """
        单例模式
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化 Redis 客户端
        """
        if self._client is None:
            self._connect()
    
    def _connect(self) -> None:
        """
        连接 Redis
        """
        try:
            self._client = redis.Redis(
                host=REDIS_CONFIG["HOST"],
                port=REDIS_CONFIG["PORT"],
                password=REDIS_CONFIG["PASSWORD"] if REDIS_CONFIG["PASSWORD"] else None,
                db=REDIS_CONFIG["DB"],
                socket_connect_timeout=REDIS_CONFIG["CONNECTION_TIMEOUT"],
                max_connections=REDIS_CONFIG["POOL_SIZE"]
            )
            self._client.ping()
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            raise
    
    def get_client(self) -> redis.Redis:
        """
        获取 Redis 客户端实例
        
        Returns:
            redis.Redis: Redis 客户端
        """
        return self._client
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """
        设置键值对
        
        Args:
            key: 键
            value: 值
            ex: 过期时间（秒）
        
        Returns:
            bool: 是否成功
        """
        try:
            result = self._client.set(key, value, ex=ex)
            logger.debug(f"Redis SET: {key}")
            return result
        except Exception as e:
            logger.error(f"Redis SET 失败: {e}")
            return False
    
    def get(self, key: str) -> Optional[str]:
        """
        获取值
        
        Args:
            key: 键
        
        Returns:
            Optional[str]: 值
        """
        try:
            value = self._client.get(key)
            if value:
                return value.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Redis GET 失败: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        删除键
        
        Args:
            key: 键
        
        Returns:
            bool: 是否成功
        """
        try:
            self._client.delete(key)
            logger.debug(f"Redis DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Redis DELETE 失败: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 键
        
        Returns:
            bool: 是否存在
        """
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS 失败: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        设置过期时间
        
        Args:
            key: 键
            seconds: 秒数
        
        Returns:
            bool: 是否成功
        """
        try:
            return self._client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis EXPIRE 失败: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        获取剩余过期时间
        
        Args:
            key: 键
        
        Returns:
            int: 剩余秒数
        """
        try:
            return self._client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL 失败: {e}")
            return -1
    
    def hset(self, name: str, key: str, value: str) -> bool:
        """
        设置哈希字段
        
        Args:
            name: 哈希名
            key: 字段名
            value: 值
        
        Returns:
            bool: 是否成功
        """
        try:
            self._client.hset(name, key, value)
            return True
        except Exception as e:
            logger.error(f"Redis HSET 失败: {e}")
            return False
    
    def hget(self, name: str, key: str) -> Optional[str]:
        """
        获取哈希字段
        
        Args:
            name: 哈希名
            key: 字段名
        
        Returns:
            Optional[str]: 值
        """
        try:
            value = self._client.hget(name, key)
            if value:
                return value.decode('utf-8')
            return None
        except Exception as e:
            logger.error(f"Redis HGET 失败: {e}")
            return None
    
    def hgetall(self, name: str) -> Dict[str, str]:
        """
        获取所有哈希字段
        
        Args:
            name: 哈希名
        
        Returns:
            Dict[str, str]: 所有字段
        """
        try:
            data = self._client.hgetall(name)
            return {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}
        except Exception as e:
            logger.error(f"Redis HGETALL 失败: {e}")
            return {}
    
    def hdel(self, name: str, key: str) -> bool:
        """
        删除哈希字段
        
        Args:
            name: 哈希名
            key: 字段名
        
        Returns:
            bool: 是否成功
        """
        try:
            self._client.hdel(name, key)
            return True
        except Exception as e:
            logger.error(f"Redis HDEL 失败: {e}")
            return False
    
    def zadd(self, name: str, mapping: Dict[str, float]) -> bool:
        """
        添加有序集合成员
        
        Args:
            name: 集合名
            mapping: 成员-分数映射
        
        Returns:
            bool: 是否成功
        """
        try:
            self._client.zadd(name, mapping)
            return True
        except Exception as e:
            logger.error(f"Redis ZADD 失败: {e}")
            return False
    
    def zrange(self, name: str, start: int, end: int, withscores: bool = False) -> List:
        """
        获取有序集合范围
        
        Args:
            name: 集合名
            start: 开始位置
            end: 结束位置
            withscores: 是否包含分数
        
        Returns:
            List: 成员列表
        """
        try:
            result = self._client.zrange(name, start, end, withscores=withscores)
            if withscores:
                return [(item[0].decode('utf-8'), item[1]) for item in result]
            return [item.decode('utf-8') for item in result]
        except Exception as e:
            logger.error(f"Redis ZRANGE 失败: {e}")
            return []
    
    def close(self) -> None:
        """
        关闭连接
        """
        try:
            if self._client:
                self._client.close()
                logger.info("Redis 连接已关闭")
        except Exception as e:
            logger.error(f"Redis 关闭连接失败: {e}")


def get_redis_client() -> RedisClient:
    """
    获取 Redis 客户端实例
    
    Returns:
        RedisClient: Redis 客户端
    """
    return RedisClient()
