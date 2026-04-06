# SpiritMemory-Agent 项目开发日志 - Day 1

## 项目概述

**项目名称**: SpiritMemory-Agent  
**项目版本**: 1.0.0  
**开发日期**: 2026-04-06  
**项目描述**: 企业级智能记忆管理系统，基于热、温、冷三层存储架构

---

## 今日完成工作

### 1. 项目初始化

#### 1.1 项目结构搭建

```
SpiritMemory-Agent/
├── README.md                # 项目总介绍+架构说明
├── requirements.txt         # 依赖锁版
├── .gitignore              # Git忽略配置
├── config/                 # 全局配置层
│   ├── db_config.py        # 数据库配置
│   ├── memory_config.py    # 记忆配置
│   ├── emotion_config.py   # 情感配置
│   ├── global_const.py     # 全局常量
│   └── connect_test.py     # 连接测试
├── database/               # 数据库连接封装
│   ├── redis_client.py     # Redis客户端
│   ├── milvus_client.py    # Milvus客户端
│   └── mongo_client.py     # MongoDB客户端
├── utils/                  # 工具层
│   ├── __init__.py
│   ├── utils_config.py     # 统一配置
│   ├── logger.py           # 日志模块
│   ├── common.py           # 通用工具
│   ├── text_process.py     # 文本处理
│   ├── embedding.py        # 向量生成
│   └── README.md           # 工具层文档
├── src/                    # 业务核心
│   └── memory/             # 记忆模块
│       ├── __init__.py
│       ├── memory_config.py
│       ├── memory_entity.py
│       ├── memory_strategy.py
│       ├── hybrid_retrieval.py
│       ├── memory_core.py
│       └── README.md
└── logs/                   # 日志目录
```

#### 1.2 Git 仓库管理

- 初始化 Git 仓库
- 关联 GitHub 远程仓库: `https://github.com/usergod-cpu/SpiritMemory-Agent.git`
- 创建 dev 分支作为开发分支
- master 分支与 dev 分支同步

---

### 2. Config 配置层

#### 2.1 数据库配置 (db_config.py)

```python
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
    "DB_NAME": "spirit_memory",
    "DEFAULT_COLLECTION": "memories",
}

# Milvus 配置
MILVUS_CONFIG = {
    "HOST": "localhost",
    "PORT": 19530,
    "DB_NAME": "spirit_memory",
    "DEFAULT_COLLECTION": "memory_embeddings",
}
```

#### 2.2 连接测试

- 创建 `connect_test.py` 测试脚本
- 成功连接 Redis、MongoDB、Milvus 三个数据库

---

### 3. Database 数据库层

#### 3.1 Redis 客户端 (redis_client.py)

**功能特性:**
- 单例模式封装
- 完整的 Redis 操作方法
- 支持字符串、哈希、有序集合操作
- 异常捕获和日志记录

**主要方法:**
| 方法 | 说明 |
|------|------|
| set/get | 键值操作 |
| hset/hget/hgetall | 哈希操作 |
| zadd/zrange | 有序集合操作 |
| expire/ttl | 过期时间管理 |

#### 3.2 Milvus 客户端 (milvus_client.py)

**功能特性:**
- 单例模式封装
- 集合创建、删除
- 向量插入、检索、删除
- 索引管理

**主要方法:**
| 方法 | 说明 |
|------|------|
| create_collection | 创建集合 |
| insert | 插入向量 |
| search | 向量检索 |
| delete | 删除向量 |

#### 3.3 MongoDB 客户端 (mongo_client.py)

**功能特性:**
- 单例模式封装
- 文档 CRUD 操作
- 索引创建
- 批量操作支持

**主要方法:**
| 方法 | 说明 |
|------|------|
| insert_one/insert_many | 插入文档 |
| find_one/find_many | 查询文档 |
| update_one/update_many | 更新文档 |
| delete_one/delete_many | 删除文档 |

---

### 4. Utils 工具层

#### 4.1 统一配置 (utils_config.py)

集中管理所有工具模块的配置参数:

```python
# 日志配置
LOG_CONFIG = {
    "LOG_DIR": "logs",
    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "DEFAULT_LOG_LEVEL": "INFO",
}

# 向量生成配置
EMBEDDING_CONFIG = {
    "DEFAULT_EMBEDDING_DIM": 768,
    "DEFAULT_MODEL_NAME": "sentence-transformers/all-MiniLM-L6-v2",
}

# 文本处理配置
TEXT_PROCESS_CONFIG = {
    "DEFAULT_MAX_LENGTH": 512,
    "DEFAULT_MAX_KEYWORDS": 10,
}
```

#### 4.2 日志模块 (logger.py)

**功能特性:**
- 同时输出控制台 + 文件落盘
- 日志分级：DEBUG/INFO/WARN/ERROR
- 日志文件按天切割（保留30天）
- 支持多日志记录器管理

#### 4.3 通用工具 (common.py)

**功能列表:**
| 函数 | 说明 |
|------|------|
| generate_uuid() | 生成唯一ID |
| get_current_time() | 获取当前时间 |
| format_datetime() | 时间格式化 |
| safe_dict_get() | 字典安全获取 |
| generate_version() | 版本号生成 |

#### 4.4 文本处理 (text_process.py)

**功能列表:**
| 函数 | 说明 |
|------|------|
| clean_text() | 文本清洗 |
| truncate_text() | 文本截断 |
| extract_keywords() | 提取关键词 |
| preprocess_text() | 文本预处理 |

#### 4.5 向量生成 (embedding.py)

**功能特性:**
- 封装文本生成向量的统一接口
- 模型接口可替换
- 支持单个文本和批量文本
- 延迟初始化模型

---

### 5. Memory 记忆模块

#### 5.1 架构设计

**三层存储架构:**

| 层级 | 存储介质 | 特点 | 用途 |
|------|----------|------|------|
| 热记忆 | Redis | 短期、高频、会话级 | 当前活跃记忆 |
| 温记忆 | Milvus | 长期、向量、可检索 | 重要记忆 |
| 冷记忆 | MongoDB | 原始归档、全量存储 | 历史记忆 |

**记忆生命周期:**
```
创建 → 分类 → 存储 → 访问 → 精炼 → 降级/升级 → 归档/删除
```

#### 5.2 记忆实体 (memory_entity.py)

**属性结构:**
```python
@dataclass
class MemoryEntity:
    memory_id: str          # 记忆唯一ID
    user_id: str            # 用户ID
    content: str            # 记忆内容
    tags: List[str]         # 标签列表
    emotion_tag: str        # 情感标签
    weight: float           # 权重 (0.1-10.0)
    timestamp: int          # 创建时间戳
    expire_type: str        # 过期类型
    status: str             # 状态
    memory_type: str        # 记忆类型
    embedding: List[float]  # 向量表示
    access_count: int       # 访问次数
```

#### 5.3 三层分流策略 (memory_strategy.py)

**主要功能:**
- classify_memory(): 分类记忆到合适层级
- store_to_hot/warm/cold(): 存储到对应层级
- upgrade_memory(): 升级记忆
- downgrade_memory(): 降级记忆
- auto_cleanup(): 自动清理过期记忆

#### 5.4 混合检索 (hybrid_retrieval.py)

**检索维度:**
- 向量相似度检索
- 标签过滤
- 时间衰减加权
- 权重加权
- 情感匹配

**检索配置:**
```python
MEMORY_RETRIEVAL_CONFIG = {
    "DEFAULT_TOP_K": 10,
    "SIMILARITY_THRESHOLD": 0.7,
    "CONTENT_WEIGHT": 0.4,
    "TAG_WEIGHT": 0.2,
    "EMOTION_WEIGHT": 0.1,
    "TIME_DECAY_WEIGHT": 0.3,
}
```

#### 5.5 记忆核心操作 (memory_core.py)

**主要方法:**
| 方法 | 说明 |
|------|------|
| create_memory() | 创建记忆 |
| update_memory() | 更新记忆 |
| delete_memory() | 删除记忆 |
| get_memory() | 获取单条记忆 |
| batch_insert() | 批量插入 |
| search_memories() | 搜索记忆 |
| refine_memory() | 精炼记忆 |
| detect_conflicts() | 冲突检测 |

---

## 技术栈

### 后端框架
- Python 3.x
- FastAPI (API框架)

### 数据库
- Redis 5.0+ (热记忆存储)
- Milvus 2.4+ (向量数据库)
- MongoDB 4.6+ (文档数据库)

### AI/ML
- sentence-transformers (向量生成)
- numpy (数值计算)

### 工具库
- loguru (日志)
- pydantic (数据验证)

---

## 代码统计

| 模块 | 文件数 | 代码行数 |
|------|--------|----------|
| config | 5 | ~150 |
| database | 3 | ~900 |
| utils | 6 | ~800 |
| memory | 6 | ~1500 |
| **总计** | **20** | **~3350** |

---

## Git 提交记录

```
49dbd27 - 创建 utils 统一配置文件并更新所有模块使用统一配置
01ea38a - 添加 memory 模块 README 文档
fad5187 - 完成 memory 记忆模块开发
35d7784 - 添加 utils 工具层 README 文档
49dbd27 - 完成 utils 工具层开发
```

---

## 设计原则

1. **完全解耦** - 各模块独立，不相互依赖
2. **三层存储** - 热/温/冷架构，自动分流
3. **混合检索** - 多维度融合，精准匹配
4. **生命周期管理** - 自动精炼、降级、清理
5. **配置驱动** - 所有参数可配置
6. **企业级标准** - 类型注解、异常捕获、日志完整

---

## 下一步计划

### Day 2 计划
1. 开发 emotion 情感模块
2. 实现情感分析与标签
3. 开发 self_cognition 自我认知模块
4. 实现 scheduler 调度器模块
5. 开发 API 接口层

### 后续规划
1. 单元测试编写
2. 性能优化
3. 文档完善
4. 部署方案

---

## 项目亮点

1. **三层存储架构**: 创新的热/温/冷记忆分层设计
2. **混合检索**: 多维度融合的智能检索系统
3. **生命周期管理**: 完整的记忆生命周期自动化
4. **企业级代码**: 类型注解、异常处理、日志完整
5. **配置驱动**: 所有参数可配置，易于维护

---

## 联系方式

- GitHub: https://github.com/usergod-cpu/SpiritMemory-Agent
- 开发团队: SpiritMemory Team

---

*最后更新: 2026-04-06*
