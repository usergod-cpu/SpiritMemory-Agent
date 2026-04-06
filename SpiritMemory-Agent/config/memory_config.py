# 记忆配置
MEMORY_CONFIG = {
    "MAX_MEMORY_SIZE": 10000,  # 最大记忆数量
    "MEMORY_RETENTION_DAYS": 30,  # 记忆保留天数
    "MEMORY_EMBEDDING_DIM": 768,  # 记忆嵌入维度
    "MEMORY_SIMILARITY_THRESHOLD": 0.7,  # 记忆相似度阈值
    "MEMORY_BATCH_SIZE": 100,  # 批处理大小
    "MEMORY_CLEANUP_INTERVAL": 86400,  # 记忆清理间隔（秒）
    "DEFAULT_MEMORY_TYPE": "short_term",  # 默认记忆类型
    "MEMORY_TYPES": ["short_term", "long_term", "important"]  # 记忆类型列表
}
