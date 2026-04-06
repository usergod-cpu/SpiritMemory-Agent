"""
Utils 工具层统一配置

集中管理所有工具模块的配置参数
"""

# 日志配置
LOG_CONFIG = {
    "LOG_DIR": "logs",
    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "DATE_FORMAT": "%Y-%m-%d %H:%M:%S",
    "DEFAULT_LOG_LEVEL": "INFO",
    "DEFAULT_LOGGER_NAME": "SpiritMemory",
    "LOG_FILE_BACKUP_COUNT": 30,
    "LOG_FILE_ENCODING": "utf-8",
}

# 向量生成配置
EMBEDDING_CONFIG = {
    "EMBEDDING_TYPE": "online",  # online: 线上模型, local: 本地模型
    "DEFAULT_EMBEDDING_DIM": 1024,  # 智谱 embedding-3 默认维度
    "DEFAULT_NORMALIZE": True,
    
    # 本地模型配置
    "LOCAL_MODEL_NAME": "sentence-transformers/all-MiniLM-L6-v2",
    "LOCAL_DEVICE": "cpu",
    "LOCAL_EMBEDDING_DIM": 768,
    
    # 线上模型配置 (智谱 AI)
    "ONLINE_PROVIDER": "zhipuai",  # zhipuai, openai, aliyun
    "ONLINE_MODEL_NAME": "embedding-3",  # embedding-2, embedding-3
    "ONLINE_API_KEY": "",  # 从环境变量 ZHIPUAI_API_KEY 读取
    "ONLINE_API_BASE": "https://open.bigmodel.cn/api/paas/v4",
    "ONLINE_EMBEDDING_DIM": 1024,  # embedding-3: 1024, embedding-2: 1024
    
    # OpenAI 配置 (备用)
    "OPENAI_API_KEY": "",  # 从环境变量 OPENAI_API_KEY 读取
    "OPENAI_API_BASE": "https://api.openai.com/v1",
    "OPENAI_MODEL_NAME": "text-embedding-3-small",
    "OPENAI_EMBEDDING_DIM": 1536,
}

# 文本处理配置
TEXT_PROCESS_CONFIG = {
    "DEFAULT_MAX_LENGTH": 512,
    "DEFAULT_MIN_KEYWORD_LENGTH": 2,
    "DEFAULT_MAX_KEYWORDS": 10,
    "DEFAULT_TRUNCATE_SUFFIX": "...",
    "DEFAULT_CHUNK_SIZE": 256,
    "DEFAULT_OVERLAP": 50,
    "DEFAULT_STOP_WORDS": {
        "的", "是", "在", "了", "和", "与", "或", "有", "这", "那",
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall"
    },
}

# 通用工具配置
COMMON_CONFIG = {
    "DEFAULT_DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
    "DEFAULT_DATE_FORMAT": "%Y-%m-%d",
    "DEFAULT_TIME_FORMAT": "%H:%M:%S",
    "DEFAULT_VERSION_MAJOR": 1,
    "DEFAULT_VERSION_MINOR": 0,
    "DEFAULT_VERSION_PATCH": 0,
}

# 项目信息配置
PROJECT_CONFIG = {
    "PROJECT_NAME": "SpiritMemory-Agent",
    "PROJECT_VERSION": "1.0.0",
    "PROJECT_AUTHOR": "SpiritMemory Team",
    "PROJECT_DESCRIPTION": "企业级智能记忆管理系统",
}
