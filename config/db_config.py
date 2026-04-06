# Redis 配置
REDIS_CONFIG = {
    "HOST": "localhost",
    "PORT": 6379,
    "PASSWORD": "",
    "DB": 0,
    "CONNECTION_TIMEOUT": 5,
    "POOL_SIZE": 10
}

# MongoDB 配置
MONGODB_CONFIG = {
    "HOST": "localhost",
    "PORT": 27017,
    "PASSWORD": "",
    "DB_NAME": "spirit_memory",
    "DEFAULT_COLLECTION": "memories",
    "CONNECTION_TIMEOUT": 5
}

# Milvus 配置
MILVUS_CONFIG = {
    "HOST": "localhost",
    "PORT": 19530,
    "PASSWORD": "",
    "DB_NAME": "spirit_memory",
    "DEFAULT_COLLECTION": "memory_embeddings",
    "CONNECTION_TIMEOUT": 5
}
