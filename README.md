# SpiritMemory-Agent

SpiritMemory-Agent 是一个智能记忆管理系统，用于处理和管理 AI 系统的记忆、情感和自我认知。

## 项目架构

```
SpiritMemory-Agent/
 ├── README.md                # 项目总介绍+架构说明
 ├── requirements.txt         # 依赖锁版
 ├── .gitignore
 ├── config/                  # 全局所有配置（杜绝硬编码）
 │   ├── db_config.py
 │   ├── memory_config.py
 │   ├── emotion_config.py
 │   └── global_const.py
 ├── database/                # 纯底层连接封装，无业务
 │   ├── redis_client.py
 │   ├── milvus_client.py
 │   └── mongo_client.py
 ├── utils/                   # 通用工具
 │   ├── logger.py
 │   ├── embedding_utils.py
 │   └── common_tools.py
 ├── src/                     # 未来业务核心
 │   ├── memory/
 │   ├── emotion/
 │   ├── self_cognition/
 │   ├── scheduler/
 │   ├── prompts/
 │   └── api/
 └── logs/                    # 日志自动落盘目录
```

## 目录说明

- **config/**: 存放所有配置文件，避免硬编码
  - `db_config.py`: 数据库连接配置（Redis、MongoDB、Milvus）
  - `memory_config.py`: 记忆相关配置
  - `emotion_config.py`: 情感相关配置
  - `global_const.py`: 全局常量配置
- **database/**: 底层数据库连接封装，包括 Redis、Milvus 和 MongoDB
- **utils/**: 通用工具函数，包括日志、嵌入处理和通用工具
- **src/**: 业务核心代码，包含记忆、情感、自我认知、调度器、提示词和 API 模块
- **logs/**: 日志文件存放目录

## 技术栈

- Python
- Redis
- Milvus (向量数据库)
- MongoDB

## 快速开始

1. **克隆项目**
   ```bash
   git clone https://github.com/usergod-cpu/SpiritMemory-Agent.git
   cd SpiritMemory-Agent
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置说明**
   - 所有配置文件位于 `config/` 目录
   - 数据库配置：`config/db_config.py`（本地环境已默认配置）
   - 记忆配置：`config/memory_config.py`
   - 情感配置：`config/emotion_config.py`
   - 全局常量：`config/global_const.py`

4. **启动服务**
   ```bash
   # 启动 API 服务
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```

## 功能特性

- 智能记忆管理
- 情感分析与处理
- 自我认知能力
- 任务调度
- 可扩展的 API 接口
