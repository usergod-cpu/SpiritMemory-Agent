# SpiritMemory-Agent 记忆模块

企业级记忆管理系统，基于热、温、冷三层存储架构，提供完整的记忆生命周期管理。

## 模块结构

```
src/memory/
├── __init__.py           # 模块入口
├── memory_config.py      # 记忆配置
├── memory_entity.py      # 记忆实体结构
├── memory_strategy.py    # 三层记忆分流策略
├── hybrid_retrieval.py   # 混合检索
└── memory_core.py        # 记忆操作核心类
```

## 架构设计

### 三层存储架构

| 层级 | 存储介质 | 特点 | 用途 |
|------|----------|------|------|
| **热记忆** | Redis | 短期、高频、会话级 | 当前活跃记忆，快速访问 |
| **温记忆** | Milvus | 长期、向量、可检索 | 重要记忆，支持向量检索 |
| **冷记忆** | MongoDB | 原始归档、全量存储 | 历史记忆，持久化存储 |

### 记忆生命周期

```
创建 → 分类 → 存储 → 访问 → 精炼 → 降级/升级 → 归档/删除
```

## 核心组件

### 1. MemoryEntity - 记忆实体

记忆的数据结构定义。

**属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| memory_id | str | 记忆唯一ID |
| user_id | str | 用户ID |
| content | str | 记忆内容 |
| tags | List[str] | 标签列表 |
| emotion_tag | str | 情感标签 |
| weight | float | 权重 (0.1-10.0) |
| timestamp | int | 创建时间戳 |
| expire_type | str | 过期类型 |
| status | str | 状态 |
| memory_type | str | 记忆类型 |
| embedding | List[float] | 向量表示 |
| access_count | int | 访问次数 |

**使用示例：**

```python
from src.memory import MemoryEntity, create_memory

# 创建记忆实体
memory = create_memory(
    user_id="user_001",
    content="今天学习了Python编程",
    tags=["学习", "编程"],
    emotion_tag="happy",
    memory_type="short_term",
    expire_type="daily"
)

# 转换为字典
data = memory.to_dict()

# 从字典创建
memory = MemoryEntity.from_dict(data)
```

### 2. MemoryCore - 记忆操作核心类

提供记忆的 CRUD 操作和生命周期管理。

**主要方法：**

| 方法 | 说明 |
|------|------|
| create_memory() | 创建记忆 |
| update_memory() | 更新记忆 |
| delete_memory() | 删除记忆 |
| get_memory() | 获取单条记忆 |
| batch_insert() | 批量插入 |
| search_memories() | 搜索记忆 |
| refine_memory() | 精炼记忆 |
| detect_conflicts() | 检测冲突 |
| mark_expired() | 标记失效 |
| auto_downgrade() | 自动降级 |

**使用示例：**

```python
from src.memory import get_memory_core

# 获取记忆核心实例
memory_core = get_memory_core()

# 创建记忆
memory = memory_core.create_memory(
    user_id="user_001",
    content="今天学习了Python编程",
    tags=["学习", "编程"],
    emotion_tag="happy",
    memory_type="short_term"
)

# 获取记忆
memory = memory_core.get_memory(memory.memory_id)

# 更新记忆
memory_core.update_memory(
    memory.memory_id,
    content="今天学习了Python和JavaScript",
    tags=["学习", "编程", "前端"]
)

# 搜索记忆
results = memory_core.search_memories(
    query="编程学习",
    user_id="user_001",
    top_k=10
)

# 删除记忆
memory_core.delete_memory(memory.memory_id)
```

### 3. MemoryStrategy - 三层记忆分流策略

实现记忆在热、温、冷三层之间的自动分流。

**主要方法：**

| 方法 | 说明 |
|------|------|
| classify_memory() | 分类记忆到合适层级 |
| store_to_hot() | 存储到热记忆 |
| store_to_warm() | 存储到温记忆 |
| store_to_cold() | 存储到冷记忆 |
| upgrade_memory() | 升级记忆 |
| downgrade_memory() | 降级记忆 |
| auto_cleanup() | 自动清理过期记忆 |

**使用示例：**

```python
from src.memory import MemoryStrategy, MemoryEntity

strategy = MemoryStrategy()

# 分类记忆
level = strategy.classify_memory(memory)
# 返回: "hot", "warm", 或 "cold"

# 存储到热记忆
strategy.store_to_hot(memory)

# 升级记忆
strategy.upgrade_memory(memory)

# 降级记忆
strategy.downgrade_memory(memory)
```

### 4. HybridRetrieval - 混合检索

实现多维度融合的记忆检索。

**检索维度：**

- 向量相似度检索
- 标签过滤
- 时间衰减加权
- 权重加权
- 情感匹配

**使用示例：**

```python
from src.memory import HybridRetrieval

retrieval = HybridRetrieval()

# 混合检索
results = retrieval.search(
    query="编程学习",
    user_id="user_001",
    tags=["学习"],
    emotion_tag="happy",
    top_k=10
)

# 按标签搜索
results = retrieval.search_by_tags(
    tags=["编程", "学习"],
    user_id="user_001",
    top_k=10
)

# 按时间范围搜索
results = retrieval.search_by_time_range(
    start_time=1704067200,  # 2024-01-01
    end_time=1704153600,    # 2024-01-02
    user_id="user_001",
    top_k=10
)
```

## 配置说明

### 记忆类型配置

```python
MEMORY_TYPE_CONFIG = {
    "TYPES": ["short_term", "long_term", "important"],
    "DEFAULT_TYPE": "short_term",
    "SHORT_TERM_EXPIRE": 3600,        # 1小时
    "LONG_TERM_EXPIRE": 2592000,      # 30天
    "IMPORTANT_EXPIRE": 31536000,     # 1年
}
```

### 过期类型配置

```python
MEMORY_EXPIRE_TYPE_CONFIG = {
    "SESSION": "session",     # 会话级
    "DAILY": "daily",         # 日级
    "WEEKLY": "weekly",       # 周级
    "MONTHLY": "monthly",     # 月级
    "PERMANENT": "permanent", # 永久
}
```

### 权重配置

```python
MEMORY_WEIGHT_CONFIG = {
    "DEFAULT_WEIGHT": 1.0,
    "MIN_WEIGHT": 0.1,
    "MAX_WEIGHT": 10.0,
    "ACCESS_BOOST": 0.1,      # 每次访问权重增加
    "TIME_DECAY_RATE": 0.01,  # 时间衰减率
}
```

### 检索配置

```python
MEMORY_RETRIEVAL_CONFIG = {
    "DEFAULT_TOP_K": 10,
    "MAX_TOP_K": 100,
    "SIMILARITY_THRESHOLD": 0.7,
    "TIME_DECAY_WEIGHT": 0.3,
    "CONTENT_WEIGHT": 0.4,
    "TAG_WEIGHT": 0.2,
    "EMOTION_WEIGHT": 0.1,
}
```

## 完整使用示例

```python
from src.memory import get_memory_core

# 初始化
memory_core = get_memory_core()

# 创建记忆
memory = memory_core.create_memory(
    user_id="user_001",
    content="今天学习了Python编程，感觉很充实",
    tags=["学习", "编程"],
    emotion_tag="happy",
    memory_type="short_term",
    expire_type="daily"
)

print(f"创建记忆: {memory.memory_id}")

# 搜索记忆
results = memory_core.search_memories(
    query="编程学习",
    user_id="user_001",
    top_k=5
)

for mem in results:
    print(f"记忆: {mem.content}")
    print(f"得分: {mem.metadata.get('retrieval_score', 0):.4f}")

# 精炼记忆
memory_core.refine_memory(memory.memory_id)

# 检测冲突
conflicts = memory_core.detect_conflicts(memory)
print(f"检测到 {len(conflicts)} 条冲突记忆")

# 清理
memory_core.delete_memory(memory.memory_id)
```

## 设计原则

1. **完全解耦** - 不依赖情感、自我认知、调度模块
2. **三层存储** - 热/温/冷架构，自动分流
3. **混合检索** - 多维度融合，精准匹配
4. **生命周期管理** - 自动精炼、降级、清理
5. **配置驱动** - 所有参数可配置
6. **企业级标准** - 类型注解、异常捕获、日志完整

## 依赖说明

```
redis>=5.0.1
pymilvus>=2.4.0
pymongo>=4.6.0
numpy>=1.24.0
sentence-transformers>=2.2.0
```

## 版本信息

- 版本号：1.0.0
- 最后更新：2026-04-06
