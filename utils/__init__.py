"""
SpiritMemory-Agent Utils 工具层

提供企业级工具函数，包括：
- logger: 全局统一日志
- common: 通用工具（时间、ID、版本号等）
- text_process: 文本处理工具
- embedding: 向量生成封装
"""

from .utils_config import (
    LOG_CONFIG,
    EMBEDDING_CONFIG,
    TEXT_PROCESS_CONFIG,
    COMMON_CONFIG,
    PROJECT_CONFIG,
)

from .logger import (
    get_logger,
    setup_logger,
    set_log_level,
    log_debug,
    log_info,
    log_warning,
    log_error,
    log_exception,
)

from .common import (
    generate_uuid,
    get_current_time,
    format_datetime,
    format_date,
    format_time,
    safe_dict_get,
    generate_version,
    timestamp_to_datetime,
    datetime_to_timestamp,
    is_valid_uuid,
    get_timestamp_str,
    calculate_time_diff,
)

from .text_process import (
    clean_text,
    truncate_text,
    extract_keywords,
    preprocess_text,
    split_text_by_length,
    count_words,
    remove_duplicates,
)

from .embedding import (
    EmbeddingGenerator,
    create_embedding_generator,
    encode_text,
)


__all__ = [
    "LOG_CONFIG",
    "EMBEDDING_CONFIG",
    "TEXT_PROCESS_CONFIG",
    "COMMON_CONFIG",
    "PROJECT_CONFIG",
    "get_logger",
    "setup_logger",
    "set_log_level",
    "log_debug",
    "log_info",
    "log_warning",
    "log_error",
    "log_exception",
    "generate_uuid",
    "get_current_time",
    "format_datetime",
    "format_date",
    "format_time",
    "safe_dict_get",
    "generate_version",
    "timestamp_to_datetime",
    "datetime_to_timestamp",
    "is_valid_uuid",
    "get_timestamp_str",
    "calculate_time_diff",
    "clean_text",
    "truncate_text",
    "extract_keywords",
    "preprocess_text",
    "split_text_by_length",
    "count_words",
    "remove_duplicates",
    "EmbeddingGenerator",
    "create_embedding_generator",
    "encode_text",
]

__version__ = PROJECT_CONFIG["PROJECT_VERSION"]
