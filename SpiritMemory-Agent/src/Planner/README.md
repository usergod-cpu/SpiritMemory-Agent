# Planner 模块 - LLM 任务规划器

## 📋 概述

Planner 模块是 SpiritMemory-Agent 的核心组件，负责使用 LLM（通义千问/Qwen）进行智能任务规划和 MCP 工具调用。它能够分析用户输入，判断是否需要使用工具，选择合适的工具，并生成可执行的任务计划。

### 核心功能

- ✅ **智能任务规划** - 使用 Qwen LLM 分析用户意图并生成任务计划
- ✅ **工具选择** - 自动判断是否需要使用工具并选择合适的 MCP 工具
- ✅ **MCP 集成** - 集成阿里云 MCP 服务（高德地图、代码解释器、联网搜索）
- ✅ **任务执行** - 自动执行任务计划并调用 MCP 工具
- ✅ **异常处理** - 完善的错误处理和降级机制

---

## 🏗️ 架构设计

### 模块结构

```
src/Planner/
├── planner.py              # 主模块
│   ├── MCPTool            # MCP 工具数据类
│   ├── MCPClient          # MCP 客户端
│   ├── LLMPlanner         # LLM 任务规划器
│   ├── create_planner()   # 便捷函数
│   └── plan_and_execute() # 一站式执行函数
└── README.md              # 本文档
```

### 类关系图

```
┌─────────────────┐
│  LLMPlanner     │
│  (任务规划器)   │
├─────────────────┤
│ - mcp_client    │───────┐
│ - available_tools       │
└─────────────────┘       │
                          │ 使用
                          ▼
                  ┌─────────────────┐
                  │  MCPClient      │
                  │  (MCP 客户端)   │
                  ├─────────────────┤
                  │ - available_tools│
                  └─────────────────┘
                          │
                          │ 调用
                          ▼
                  ┌─────────────────┐
                  │  MCPTool        │
                  │  (工具信息)     │
                  └─────────────────┘
```

---

## 📦 核心组件

### 1. MCPTool

MCP 工具信息数据类，用于存储工具的元数据。

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| name | str | 工具名称 |
| description | str | 工具描述 |
| input_schema | Dict[str, Any] | 输入参数 schema |
| mcp_endpoint | str | MCP 端点 URL |

#### 示例

```python
from src.Planner.planner import MCPTool

tool = MCPTool(
    name="weather_query",
    description="查询天气信息",
    input_schema={"type": "object", "properties": {"city": {"type": "string"}}},
    mcp_endpoint="https://dashscope.aliyuncs.com/api/v1/mcps/web-search/mcp"
)

# 转换为字典
tool_dict = tool.to_dict()
```

---

### 2. MCPClient

MCP 客户端，负责与阿里云 MCP 服务通信。

#### MCP 端点

| 端点名称 | URL | 用途 |
|----------|-----|------|
| amap-maps | `https://dashscope.aliyuncs.com/api/v1/mcps/amap-maps/mcp` | 高德地图服务 |
| code-interpreter | `https://dashscope.aliyuncs.com/api/v1/mcps/code-interpreter/mcp` | 代码解释器 |
| web-search | `https://dashscope.aliyuncs.com/api/v1/mcps/web-search/mcp` | 联网搜索 |

#### 核心方法

##### `list_tools() -> List[MCPTool]`

获取所有可用的 MCP 工具列表。

**请求格式：**
```json
{
    "method": "tools/list",
    "params": {}
}
```

**示例：**
```python
client = MCPClient()
tools = client.list_tools()
for tool in tools:
    print(f"工具：{tool.name}, 描述：{tool.description}")
```

##### `call_tool(tool_name, parameters) -> Tuple[bool, Any]`

调用指定的 MCP 工具。

**请求格式：**
```json
{
    "method": "tools/call",
    "params": {
        "name": "工具名称",
        "parameters": {"参数名": "参数值"}
    }
}
```

**示例：**
```python
client = MCPClient()
success, result = client.call_tool("weather_query", {"city": "北京"})
if success:
    print(f"天气查询成功：{result}")
else:
    print(f"调用失败：{result}")
```

##### `_get_endpoint(tool_name) -> str`

根据工具名称获取对应的 MCP 端点。

**端点映射规则：**
- 包含 `map`、`amap`、`location` → amap-maps
- 包含 `code`、`interpreter`、`calculate` → code-interpreter
- 包含 `search`、`web`、`internet` → web-search
- 其他 → web-search（默认）

---

### 3. LLMPlanner

LLM 任务规划器，使用 Qwen 进行智能任务规划。

#### 核心方法

##### `initialize_tools() -> None`

初始化可用工具列表。

```python
planner = LLMPlanner()
planner.initialize_tools()
```

##### `plan_task(user_input, context) -> TaskPlan`

使用 LLM 进行任务规划。

**参数：**
- `user_input` (str): 用户输入
- `context` (Optional[AgentContext]): 可选的上下文对象

**返回：**
- `TaskPlan`: 任务规划结果

**示例：**
```python
planner = LLMPlanner()
task_plan = planner.plan_task("查询北京天气并发送邮件")

print(f"子任务数：{task_plan.total_steps}")
print(f"需要工具：{task_plan.metadata.get('need_tools')}")
for task in task_plan.sub_tasks:
    print(f"- {task['name']} (工具：{task.get('tool')})")
```

**LLM 提示词模板：**
```python
system_prompt = """你是一个智能任务规划助手。你的任务是分析用户输入，判断是否需要使用工具，如果需要，选择合适的工具并生成执行计划。

可用工具：
{tool_description}

请按照以下 JSON 格式返回规划结果：
{{
    "need_tools": true/false,
    "tools_to_use": [
        {{
            "name": "工具名称",
            "parameters": {{"参数名": "参数值"}},
            "reason": "使用该工具的原因"
        }}
    ],
    "sub_tasks": [
        {{
            "name": "子任务名称",
            "description": "子任务描述",
            "tool": "使用的工具名称（如果没有则为 null）",
            "parameters": {{}}
        }}
    ],
    "final_goal": "最终目标描述"
}}

注意：
1. 如果不需要使用工具，need_tools 设为 false，tools_to_use 设为空数组
2. 参数必须具体明确，不能包含占位符
3. 只返回 JSON，不要返回其他内容"""
```

##### `execute_plan(context) -> None`

执行任务规划。

**示例：**
```python
from src.core.context import create_context

context = create_context("user_123")
context.user_input = "查询北京天气"
context.start_execution()

planner = LLMPlanner()
context.task_plan = planner.plan_task(context.user_input)
planner.execute_plan(context)

context.complete_execution()
```

##### `should_use_tool(user_input) -> Tuple[bool, str]`

判断是否需要使用工具。

**返回：**
- `Tuple[bool, str]`: (是否需要工具，工具名称)

**示例：**
```python
planner = LLMPlanner()
need_tool, tool_name = planner.should_use_tool("计算 1+1")
print(f"需要工具：{need_tool}, 工具：{tool_name}")
```

---

## 🚀 使用指南

### 基础使用

#### 方法 1：使用便捷函数

```python
from src.Planner.planner import plan_and_execute

# 一站式执行
context = plan_and_execute("查询北京天气", "user_123")

# 查看结果
print(context.to_json())
```

#### 方法 2：手动控制

```python
from src.Planner.planner import create_planner
from src.core.context import create_context

# 创建规划器
planner = create_planner()

# 创建上下文
context = create_context("user_123")
context.user_input = "查询北京天气并发送邮件"
context.start_execution()

# 任务规划
context.task_plan = planner.plan_task(context.user_input)

# 执行计划
planner.execute_plan(context)

# 完成执行
context.complete_execution()

# 查看执行结果
print(f"状态：{context.status}")
print(f"工具调用：{len(context.tool_executions)}")
for exec in context.tool_executions:
    print(f"  - {exec.tool_name}: {'成功' if exec.success else '失败'}")
```

### 进阶使用

#### 批量任务规划

```python
from src.Planner.planner import create_planner

planner = create_planner()

test_cases = [
    "查询北京天气",
    "计算 1+1",
    "搜索 AI 新闻",
    "你好",
    "查询天气并发送邮件"
]

for user_input in test_cases:
    print(f"\n输入：{user_input}")
    task_plan = planner.plan_task(user_input)
    print(f"子任务数：{task_plan.total_steps}")
    print(f"需要工具：{task_plan.metadata.get('need_tools')}")
```

#### 工具判断

```python
from src.Planner.planner import create_planner

planner = create_planner()

# 快速判断是否需要工具
need_tool, tool_name = planner.should_use_tool("今天天气怎么样")
if need_tool:
    print(f"需要使用工具：{tool_name}")
else:
    print("不需要使用工具")
```

---

## ⚙️ 配置说明

### 环境变量

使用前必须设置以下环境变量：

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY="your_api_key_here"

# Linux/Mac
export DASHSCOPE_API_KEY="your_api_key_here"
```

**获取 API Key：**
1. 访问 [阿里云百炼](https://dashscope.console.aliyun.com/)
2. 注册/登录账号
3. 创建 API Key
4. 复制并设置到环境变量

### 依赖安装

```bash
pip install requests
```

---

## 📊 执行流程

### 完整流程图

```
用户输入
    │
    ▼
┌─────────────────┐
│  任务规划阶段   │
│  (LLMPlanner)   │
└─────────────────┘
    │
    ├─ 分析用户意图
    ├─ 判断是否需要工具
    ├─ 选择合适工具
    └─ 生成任务计划
    │
    ▼
┌─────────────────┐
│  任务执行阶段   │
│  (execute_plan) │
└─────────────────┘
    │
    ├─ 遍历子任务
    ├─ 调用 MCP 工具
    ├─ 记录执行结果
    └─ 更新任务状态
    │
    ▼
┌─────────────────┐
│  结果输出阶段   │
│  (AgentContext) │
└─────────────────┘
    │
    ├─ 收集工具结果
    ├─ 生成最终回复
    └─ 返回给用户
```

### 状态流转

```
initialized → planning → executing → validating → completed
                                      ↓
                                    failed
```

---

## 🧪 测试示例

### 测试用例

```python
from src.Planner.planner import create_planner

planner = create_planner()

# 测试 1：简单查询
task_plan = planner.plan_task("查询北京天气")
assert task_plan.total_steps > 0
print(f"✓ 测试 1 通过")

# 测试 2：数学计算
task_plan = planner.plan_task("计算 1+1")
assert task_plan.metadata.get("need_tools") == True
print(f"✓ 测试 2 通过")

# 测试 3：简单对话
task_plan = planner.plan_task("你好")
assert task_plan.metadata.get("need_tools") == False
print(f"✓ 测试 3 通过")

# 测试 4：多步骤任务
task_plan = planner.plan_task("查询天气并发送邮件")
assert task_plan.total_steps >= 2
print(f"✓ 测试 4 通过")
```

### 自动化测试

运行自动化测试：

```bash
python -m pytest src/Planner/ -v
```

---

## 🔧 最佳实践

### 1. 错误处理

```python
from src.Planner.planner import create_planner
from src.core.context import create_context

planner = create_planner()
context = create_context("user_123")

try:
    context.start_execution()
    context.task_plan = planner.plan_task(context.user_input)
    planner.execute_plan(context)
    context.complete_execution()
except Exception as e:
    context.fail_execution(str(e))
    logger.error(f"执行失败：{e}")
```

### 2. 日志记录

```python
from utils.logger import get_logger

logger = get_logger("Planner")

# 在关键步骤添加日志
logger.info("开始任务规划")
logger.debug(f"用户输入：{user_input}")
logger.warning("工具调用失败")
logger.error(f"异常：{str(e)}")
```

### 3. 性能优化

```python
# 复用规划器实例
planner = create_planner()
planner.initialize_tools()  # 只初始化一次

# 批量处理
for user_input in inputs:
    task_plan = planner.plan_task(user_input)
    # 处理任务计划...
```

---

## 📝 常见问题

### Q1: 如何添加自定义工具？

**A:** 在 `MCPClient.MCP_ENDPOINTS` 中添加新的端点映射：

```python
MCP_ENDPOINTS = {
    "amap-maps": "...",
    "code-interpreter": "...",
    "web-search": "...",
    "custom-tool": "https://your-custom-endpoint.com/mcp"  # 添加自定义端点
}
```

然后在 `_get_endpoint()` 方法中添加映射逻辑。

### Q2: 如何修改 LLM 模型？

**A:** 修改 `plan_task()` 方法中的 `model` 参数：

```python
payload = {
    "model": "qwen-max",  # 修改为其他模型
    "messages": [...],
    ...
}
```

### Q3: 如何处理超时？

**A:** 调整 `timeout` 参数：

```python
response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=60  # 增加超时时间
)
```

### Q4: 如何调试？

**A:** 启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📚 相关文档

- [AgentContext 文档](../core/context.md) - 全局上下文模块
- [MCP 规范](https://modelcontextprotocol.io/) - Model Context Protocol
- [阿里云百炼](https://help.aliyun.com/zh/dashscope/) - 官方文档

---

## 📄 许可证

本模块遵循项目主许可证。

---

## 📞 联系方式

如有问题或建议，请提交 Issue 或联系开发团队。
