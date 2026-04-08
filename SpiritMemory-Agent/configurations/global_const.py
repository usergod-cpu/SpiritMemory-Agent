# 项目信息
PROJECT_NAME = "SpiritMemory-Agent"
PROJECT_VERSION = "1.0.0"

# 编码配置
DEFAULT_ENCODING = "utf-8"

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE_PATH = "logs/app.log"

# 时间配置
DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# API 配置
API_HOST = "0.0.0.0"
API_PORT = 8000
API_TIMEOUT = 30

# 嵌入模型配置
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_MAX_LENGTH = 512

# 安全配置
SECRET_KEY = "your-secret-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
