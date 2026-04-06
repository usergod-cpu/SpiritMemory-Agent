"""
SpiritMemory-Agent Utils 工具层

提供企业级工具函数，包括：
- logger: 全局统一日志
- common: 通用工具（时间、ID、版本号等）
- text_process: 文本处理工具
- embedding: 向量生成封装
"""

from .logger import get_logger, setup_logger
from .common import (
    generate_uuid,
    get_current_time,
    format_datetime,
    safe_dict_get,
    generate_version
)
from .text_process import (
    clean_text,
    truncate_text,
    extract_keywords,
    preprocess_text
)
from .embedding import EmbeddingGenerator

__all__ = [
    "get_logger",
    "setup_logger",
    "generate_uuid",
    "get_current_time",
    "format_datetime",
    "safe_dict_get",
    "generate_version",
    "clean_text",
    "truncate_text",
    "extract_keywords",
    "preprocess_text",
    "EmbeddingGenerator",
]

__version__ = "1.0.0"
