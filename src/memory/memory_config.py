"""
记忆模块配置

定义记忆模块的所有配置参数
"""

# 记忆存储配置
MEMORY_STORAGE_CONFIG = {
    # 热记忆配置（Redis）
    "HOT_MEMORY": {
        "PREFIX": "memory:hot:",
        "DEFAULT_TTL": 3600,  # 1小时过期
        "MAX_SIZE": 1000,  # 最大存储数量
    },
    # 温记忆配置（Milvus）
    "WARM_MEMORY": {
        "COLLECTION_NAME": "memory_warm",
        "DIMENSION": 768,
        "INDEX_TYPE": "IVF_FLAT",
        "METRIC_TYPE": "COSINE",
    },
    # 冷记忆配置（MongoDB）
    "COLD_MEMORY": {
        "COLLECTION_NAME": "memory_cold",
    },
}

# 记忆类型配置
MEMORY_TYPE_CONFIG = {
    "TYPES": ["short_term", "long_term", "important"],
    "DEFAULT_TYPE": "short_term",
    "SHORT_TERM_EXPIRE": 3600,  # 短期记忆过期时间（秒）
    "LONG_TERM_EXPIRE": 86400 * 30,  # 长期记忆过期时间（30天）
    "IMPORTANT_EXPIRE": 86400 * 365,  # 重要记忆过期时间（1年）
}

# 记忆权重配置
MEMORY_WEIGHT_CONFIG = {
    "DEFAULT_WEIGHT": 1.0,
    "MIN_WEIGHT": 0.1,
    "MAX_WEIGHT": 10.0,
    "ACCESS_BOOST": 0.1,  # 每次访问权重增加
    "TIME_DECAY_RATE": 0.01,  # 时间衰减率
}

# 记忆检索配置
MEMORY_RETRIEVAL_CONFIG = {
    "DEFAULT_TOP_K": 10,
    "MAX_TOP_K": 100,
    "SIMILARITY_THRESHOLD": 0.7,  # 相似度阈值
    "TIME_DECAY_WEIGHT": 0.3,  # 时间衰减权重
    "CONTENT_WEIGHT": 0.4,  # 内容相似度权重
    "TAG_WEIGHT": 0.2,  # 标签匹配权重
    "EMOTION_WEIGHT": 0.1,  # 情感匹配权重
}

# 记忆生命周期配置
MEMORY_LIFECYCLE_CONFIG = {
    "AUTO_CLEANUP_INTERVAL": 3600,  # 自动清理间隔（秒）
    "EXPIRE_CHECK_INTERVAL": 300,  # 过期检查间隔（秒）
    "DOWNGRADE_THRESHOLD": 0.3,  # 降级阈值（权重低于此值降级）
    "CONFLICT_SIMILARITY_THRESHOLD": 0.95,  # 冲突检测相似度阈值
}

# 记忆精炼配置
MEMORY_REFINEMENT_CONFIG = {
    "ENABLE_AUTO_TAG": True,  # 启用自动打标签
    "ENABLE_AUTO_WEIGHT": True,  # 启用自动权重计算
    "ENABLE_TIME_DECAY": True,  # 启用时间衰减
    "ENABLE_AUTO_DOWNGRADE": True,  # 启用自动降级
    "ENABLE_CONFLICT_DETECT": True,  # 启用冲突检测
}

# 记忆状态配置
MEMORY_STATUS_CONFIG = {
    "STATUS_ACTIVE": "active",  # 活跃状态
    "STATUS_EXPIRED": "expired",  # 过期状态
    "STATUS_ARCHIVED": "archived",  # 归档状态
    "STATUS_DELETED": "deleted",  # 删除状态
}

# 记忆过期类型配置
MEMORY_EXPIRE_TYPE_CONFIG = {
    "SESSION": "session",  # 会话级
    "DAILY": "daily",  # 日级
    "WEEKLY": "weekly",  # 周级
    "MONTHLY": "monthly",  # 月级
    "PERMANENT": "permanent",  # 永久
}
