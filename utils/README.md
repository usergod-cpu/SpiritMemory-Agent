# SpiritMemory-Agent Utils 工具层

企业级工具函数库，提供低耦合、高可用、全类型注解的工具模块。

## 模块结构

```
utils/
├── __init__.py        # 模块入口
├── logger.py          # 全局统一日志
├── common.py          # 通用工具
├── text_process.py    # 文本处理工具
└── embedding.py       # 向量生成封装
```

## 模块介绍

### 1. logger.py - 全局统一日志

基于 Python logging 封装，提供企业级日志功能。

**功能特性：**
- 同时输出控制台 + 文件落盘
- 日志分级：DEBUG/INFO/WARN/ERROR
- 日志文件按天切割（保留30天）
- 支持多日志记录器管理

**使用示例：**
```python
from utils import get_logger, setup_logger

# 获取默认日志记录器
logger = get_logger()

# 记录日志
logger.info("这是一条信息日志")
logger.warning("这是一条警告日志")
logger.error("这是一条错误日志")

# 自定义日志记录器
custom_logger = setup_logger(
    name="MyModule",
    log_dir="logs",
    console_output=True,
    file_output=True
)
```

### 2. common.py - 通用工具

提供常用工具函数，纯函数设计，高复用性。

**功能列表：**

| 函数 | 说明 |
|------|------|
| `generate_uuid()` | 生成唯一ID |
| `get_current_time()` | 获取当前时间 |
| `format_datetime()` | 时间格式化 |
| `safe_dict_get()` | 字典安全获取 |
| `generate_version()` | 版本号生成 |
| `timestamp_to_datetime()` | 时间戳转时间对象 |
| `datetime_to_timestamp()` | 时间对象转时间戳 |
| `is_valid_uuid()` | UUID验证 |
| `get_timestamp_str()` | 获取时间戳字符串 |
| `calculate_time_diff()` | 计算时间差 |

**使用示例：**
```python
from utils import generate_uuid, format_datetime, safe_dict_get

# 生成UUID
uid = generate_uuid()  # "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# 格式化时间
time_str = format_datetime(fmt="%Y-%m-%d")  # "2024-01-01"

# 字典安全获取
data = {"name": "test", "age": 25}
name = safe_dict_get(data, "name", default="unknown")  # "test"
```

### 3. text_process.py - 文本处理工具

提供文本清洗、截断、关键词提取等功能。

**功能列表：**

| 函数 | 说明 |
|------|------|
| `clean_text()` | 文本清洗 |
| `truncate_text()` | 过长文本自动截断 |
| `extract_keywords()` | 提取关键词 |
| `preprocess_text()` | 结构化预处理 |
| `split_text_by_length()` | 按长度分割文本 |
| `count_words()` | 统计词数 |
| `remove_duplicates()` | 移除重复文本 |

**使用示例：**
```python
from utils import clean_text, truncate_text, extract_keywords

# 文本清洗
text = "  Hello   World!  "
cleaned = clean_text(text)  # "Hello World!"

# 文本截断
long_text = "这是一段很长的文本..."
truncated = truncate_text(long_text, max_length=20)  # "这是一段很长的文本..."

# 提取关键词
text = "Python是一种流行的编程语言"
keywords = extract_keywords(text, max_keywords=5)  # ["python", "流行", "编程语言"]
```

### 4. embedding.py - 向量生成封装

封装文本生成向量的统一接口，支持多种模型。

**功能特性：**
- 模型接口可替换
- 支持单个文本和批量文本
- 异常捕获
- 与 Milvus 对齐维度（默认768维）
- 延迟初始化模型

**使用示例：**
```python
from utils import EmbeddingGenerator, encode_text

# 创建向量生成器
generator = EmbeddingGenerator(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    embedding_dim=768,
    device="cpu"
)

# 生成单个文本向量
text = "这是一段测试文本"
vector = generator.encode(text)  # [0.123, 0.456, ...]

# 批量生成向量
texts = ["文本1", "文本2", "文本3"]
vectors = generator.encode(texts)  # [[...], [...], [...]]

# 使用便捷函数
vector = encode_text("测试文本")
```

## 设计原则

1. **低耦合** - 不依赖业务模块（memory、emotion、self_cognition）
2. **高可用** - 完善的异常处理和日志记录
3. **全类型注解** - 所有函数都有完整的类型注解
4. **纯函数设计** - 工具函数无副作用，易于测试
5. **注释完整** - 所有函数都有详细的文档字符串

## 依赖说明

```
numpy>=1.24.0
sentence-transformers>=2.2.0  # 可选，用于向量生成
```

## 版本信息

- 版本号：1.0.0
- 最后更新：2026-04-06
