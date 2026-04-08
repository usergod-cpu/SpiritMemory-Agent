"""
配置模块

包含项目的所有配置模块
"""

# 导出所有配置
from .db_config import REDIS_CONFIG, MONGODB_CONFIG, MILVUS_CONFIG
from .memory_config import MEMORY_CONFIG
from .emotion_config import EMOTION_CONFIG
from .global_const import PROJECT_NAME, PROJECT_VERSION

__all__ = [
    # 数据库配置
    'REDIS_CONFIG',
    'MONGODB_CONFIG',
    'MILVUS_CONFIG',
    
    # 记忆配置
    'MEMORY_CONFIG',
    
    # 情感配置
    'EMOTION_CONFIG',
    
    # 全局常量
    'PROJECT_NAME',
    'PROJECT_VERSION',
]
