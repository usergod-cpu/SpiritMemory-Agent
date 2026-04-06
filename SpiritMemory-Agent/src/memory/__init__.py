"""
SpiritMemory-Agent 记忆模块

提供企业级记忆管理功能，包括：
- 记忆实体结构
- 三层存储策略（热/温/冷）
- 混合检索
- 记忆生命周期管理
"""

from .memory_entity import MemoryEntity, create_memory
from .memory_strategy import MemoryStrategy
from .hybrid_retrieval import HybridRetrieval
from .memory_core import MemoryCore, get_memory_core
from .memory_config import (
    MEMORY_STORAGE_CONFIG,
    MEMORY_TYPE_CONFIG,
    MEMORY_WEIGHT_CONFIG,
    MEMORY_RETRIEVAL_CONFIG,
    MEMORY_LIFECYCLE_CONFIG,
    MEMORY_REFINEMENT_CONFIG,
    MEMORY_STATUS_CONFIG,
    MEMORY_EXPIRE_TYPE_CONFIG,
)

__all__ = [
    "MemoryEntity",
    "create_memory",
    "MemoryStrategy",
    "HybridRetrieval",
    "MemoryCore",
    "get_memory_core",
    "MEMORY_STORAGE_CONFIG",
    "MEMORY_TYPE_CONFIG",
    "MEMORY_WEIGHT_CONFIG",
    "MEMORY_RETRIEVAL_CONFIG",
    "MEMORY_LIFECYCLE_CONFIG",
    "MEMORY_REFINEMENT_CONFIG",
    "MEMORY_STATUS_CONFIG",
    "MEMORY_EXPIRE_TYPE_CONFIG",
]

__version__ = "1.0.0"
