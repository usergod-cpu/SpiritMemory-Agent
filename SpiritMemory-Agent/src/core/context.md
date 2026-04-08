# AgentContext - 全局上下文模块

## 概述

`AgentContext` 是 SpiritMemory-Agent 的全局唯一数据载体，所有模块只读写该对象，不互相调用。它严格遵循以下执行流程：

```
用户输入 → 任务规划 → 工具调用 → 工具校验 → 记忆/情感 → 最终全局校验 → 生成回答
```

## 核心设计理念

1. **单一数据源**：所有模块通过读写 Context 进行数据交换，避免模块间直接耦合
2. **流程标准化**：强制执行标准化的处理流程，确保系统行为可预测
3. **两层校验机制**：
   - 工具结果校验：确保工具执行结果的正确性
   - 最终全局校验：在生成答案前进行最终质量把关
4. **完整可追溯**：记录执行全过程，支持调试、审计和优化

## 类结构

### 1. TaskPlan - 任务规划结果

存储任务分解和调度信息。

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | str | 任务唯一标识 |
| original_query | str | 原始用户查询 |
| sub_tasks | List[Dict] | 子任务列表 |
| current_step | int | 当前执行步骤 |
| total_steps | int | 总步骤数 |
| status | str | 状态：pending/running/completed/failed |
| created_at | str | 创建时间 |
| updated_at | str | 更新时间 |
| metadata | Dict | 扩展元数据 |

#### 核心方法

- `next_step()` - 获取下一步任务
- `is_completed()` - 检查是否完成
- `to_dict()` - 转换为字典

#### 使用示例

```python
task_plan = TaskPlan(
    original_query="帮我查询天气并发送邮件",
    sub_tasks=[
        {"name": "查询天气", "tool": "weather_api", "params": {"city": "北京"}},
        {"name": "发送邮件", "tool": "email_sender", "params": {"to": "user@example.com"}},
    ],
    total_steps=2,
)

# 逐步执行任务
while not task_plan.is_completed():
    next_task = task_plan.next_step()
    if next_task:
        # 执行任务...
        pass
```

---

### 2. ToolExecution - 工具执行信息

存储工具调用和结果。

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| tool_id | str | 工具执行唯一标识 |
| tool_name | str | 工具名称 |
| tool_type | str | 工具类型：local/mcp/api |
| parameters | Dict | 调用参数 |
| result | Any | 执行结果 |
| success | bool | 是否成功 |
| error_message | str | 错误信息 |
| execution_time | float | 执行耗时（秒） |
| timestamp | str | 时间戳 |
| metadata | Dict | 扩展元数据 |

#### 核心方法

- `mark_success(result, execution_time)` - 标记执行成功
- `mark_failed(error_message)` - 标记执行失败
- `to_dict()` - 转换为字典

#### 使用示例

```python
tool_exec = ToolExecution(
    tool_name="weather_api",
    tool_type="api",
    parameters={"city": "北京"},
)

# 执行工具
try:
    result = call_weather_api(city="北京")
    tool_exec.mark_success(result, execution_time=0.5)
except Exception as e:
    tool_exec.mark_failed(str(e))

ctx.add_tool_execution(tool_exec)
```

---

### 3. ValidationResult - 校验结果

用于工具结果校验和最终全局校验。

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| validation_id | str | 校验唯一标识 |
| validation_type | str | 校验类型：tool_result/final_answer |
| is_valid | bool | 是否通过校验 |
| confidence | float | 置信度（0-1） |
| issues | List[str] | 发现的问题 |
| suggestions | List[str] | 改进建议 |
| raw_data | Any | 原始数据 |
| validated_data | Any | 校验后的数据 |
| timestamp | str | 时间戳 |
| metadata | Dict | 扩展元数据 |

#### 核心方法

- `pass_validation(validated_data, confidence)` - 通过校验
- `fail_validation(issues, suggestions)` - 未通过校验
- `to_dict()` - 转换为字典

#### 使用示例

```python
# 工具结果校验
validation = ValidationResult(validation_type="tool_result")

if is_valid_tool_result(tool_result):
    validation.pass_validation(
        validated_data=tool_result,
        confidence=0.95
    )
else:
    validation.fail_validation(
        issues=["数据格式错误", "缺少必要字段"],
        suggestions=["检查 API 返回", "使用备用数据源"]
    )

ctx.tool_validation = validation
```

---

### 4. MemoryInfo - 记忆信息

存储检索到的相关记忆。

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| query | str | 检索查询 |
| retrieved_memories | List[Dict] | 检索到的记忆列表 |
| memory_count | int | 记忆数量 |
| retrieval_method | str | 检索方法：hybrid/semantic/keyword |
| retrieval_time | float | 检索耗时（秒） |
| top_k | int | 返回数量 |
| similarity_threshold | float | 相似度阈值 |
| timestamp | str | 时间戳 |
| metadata | Dict | 扩展元数据 |

#### 核心方法

- `add_memories(memories, retrieval_time)` - 添加检索结果
- `get_relevant_memories(min_similarity)` - 获取相关记忆
- `to_dict()` - 转换为字典

#### 使用示例

```python
memory_info = MemoryInfo(
    query="北京的天气",
    retrieval_method="hybrid",
    top_k=10,
)

memories = hybrid_retrieval(query="北京的天气", top_k=10)
memory_info.add_memories(memories, retrieval_time=0.3)

ctx.memory_info = memory_info

# 获取高相似度记忆
relevant = memory_info.get_relevant_memories(min_similarity=0.8)
```

---

### 5. EmotionInfo - 情感信息

存储用户情感分析结果。

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| query | str | 分析的查询 |
| emotion | str | 情感类型：happy/sad/angry/anxious/neutral 等 |
| confidence | float | 置信度（0-1） |
| intensity | float | 情感强度（0-1） |
| sentiment_score | float | 情感得分（-1 到 1） |
| keywords | List[str] | 情感关键词 |
| response_strategy | str | 响应策略 |
| timestamp | str | 时间戳 |
| metadata | Dict | 扩展元数据 |

#### 核心方法

- `analyze(emotion, confidence, intensity, sentiment_score, keywords)` - 设置情感分析结果
- `_determine_response_strategy(emotion)` - 根据情感确定响应策略
- `to_dict()` - 转换为字典

#### 情感响应策略

| 情感 | 响应策略 | 说明 |
|------|----------|------|
| happy | share_and_celebrate | 分享并庆祝 |
| sad | comfort_and_support | 安慰和支持 |
| angry | calm_and_understand | 冷静和理解 |
| anxious | reassure_and_guide | 安抚和引导 |
| neutral | informative_and_helpful | 提供信息和帮助 |
| excited | enthusiastic_and_supportive | 热情和支持 |
| frustrated | patient_and_solution_oriented | 耐心和解决方案导向 |

#### 使用示例

```python
emotion_info = EmotionInfo(query=user_input)
emotion_info.analyze(
    emotion="happy",
    confidence=0.88,
    intensity=0.7,
    sentiment_score=0.6,
    keywords=["天气", "晴朗", "好心情"]
)

ctx.emotion_info = emotion_info
print(f"响应策略：{emotion_info.response_strategy}")
# 输出：响应策略：share_and_celebrate
```

---

### 6. FinalResponse - 最终回复

存储生成的回答。

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| response_id | str | 回复唯一标识 |
| content | str | 回复内容 |
| response_type | str | 回复类型：text/code/mixed |
| references | List[str] | 引用来源（记忆 ID 或工具结果） |
| confidence | float | 置信度（0-1） |
| generation_time | float | 生成耗时（秒） |
| token_count | int | token 数量 |
| timestamp | str | 时间戳 |
| metadata | Dict | 扩展元数据 |

#### 核心方法

- `generate(content, generation_time, confidence, references)` - 生成回复
- `to_dict()` - 转换为字典

#### 使用示例

```python
final_response = FinalResponse()
final_response.generate(
    content="北京今天天气晴朗，温度 25°C，湿度 60%。是个出门的好天气！",
    generation_time=1.2,
    confidence=0.95,
    references=["weather_api_result", "memory_123"]
)

ctx.final_response = final_response
```

---

### 7. AgentContext - 全局上下文核心类

作为全局唯一数据载体，整合所有模块信息。

#### 字段结构

```python
@dataclass
class AgentContext:
    # ========== 基础信息 ==========
    context_id: str
    session_id: str
    user_id: str
    created_at: str
    updated_at: str
    
    # ========== 用户输入 ==========
    user_input: str
    input_timestamp: str
    input_metadata: Dict
    
    # ========== 任务规划 ==========
    task_plan: Optional[TaskPlan]
    
    # ========== 工具执行 ==========
    tool_executions: List[ToolExecution]
    tool_validation: Optional[ValidationResult]
    
    # ========== 记忆与情感 ==========
    memory_info: Optional[MemoryInfo]
    emotion_info: Optional[EmotionInfo]
    
    # ========== 最终校验与回复 ==========
    final_validation: Optional[ValidationResult]
    final_response: Optional[FinalResponse]
    
    # ========== 执行状态 ==========
    status: str  # initialized/planning/executing/validating/completed/failed
    error_message: str
    execution_start_time: str
    execution_end_time: str
    total_execution_time: float
    
    # ========== 扩展字段 ==========
    metadata: Dict
```

#### 核心方法

**生命周期管理**
- `start_execution()` - 开始执行
- `complete_execution()` - 完成执行
- `fail_execution(error_message)` - 失败执行
- `clear()` - 清空上下文

**工具管理**
- `add_tool_execution(tool_execution)` - 添加工具执行记录
- `get_tool_results()` - 获取所有工具执行结果

**序列化**
- `to_dict()` - 转换为字典
- `to_json(indent)` - 转换为 JSON 字符串
- `from_dict(data)` - 从字典创建
- `from_json(json_str)` - 从 JSON 字符串创建

#### 使用示例

```python
# 创建上下文
ctx = AgentContext(user_id="user_123", session_id="session_456")

# 开始执行
ctx.start_execution()

# 设置用户输入
ctx.user_input = "帮我查询北京天气并告诉朋友"

# 任务规划
ctx.task_plan = TaskPlan(
    original_query=ctx.user_input,
    sub_tasks=[
        {"name": "查询天气", "tool": "weather_api"},
        {"name": "发送消息", "tool": "message_sender"},
    ],
    total_steps=2,
)

# 执行工具
tool_exec = ToolExecution(tool_name="weather_api", tool_type="api")
result = call_weather_api(city="北京")
tool_exec.mark_success(result, execution_time=0.5)
ctx.add_tool_execution(tool_exec)

# 工具校验
validation = ValidationResult(validation_type="tool_result")
validation.pass_validation(validated_data=result, confidence=0.95)
ctx.tool_validation = validation

# 记忆检索
memory_info = MemoryInfo(query="北京天气", retrieval_method="hybrid")
memory_info.add_memories(retrieved_memories, retrieval_time=0.3)
ctx.memory_info = memory_info

# 情感分析
emotion_info = EmotionInfo(query=ctx.user_input)
emotion_info.analyze(emotion="happy", confidence=0.88)
ctx.emotion_info = emotion_info

# 最终校验
final_validation = ValidationResult(validation_type="final_answer")
final_validation.pass_validation(confidence=0.92)
ctx.final_validation = final_validation

# 生成回复
final_response = FinalResponse()
final_response.generate(
    content="北京今天天气晴朗，温度 25°C",
    generation_time=1.2,
    confidence=0.95
)
ctx.final_response = final_response

# 完成执行
ctx.complete_execution()

# 输出执行统计
print(f"执行完成，总耗时：{ctx.total_execution_time:.3f}s")
print(f"工具调用：{len(ctx.tool_executions)} 次")
print(f"检索记忆：{ctx.memory_info.memory_count} 条")
```

---

### 8. ContextManager - 上下文管理器

提供全局唯一的上下文实例管理（单例模式）。

#### 核心方法

- `create_context(user_id, session_id)` - 创建新上下文
- `get_context(context_id)` - 获取上下文
- `remove_context(context_id)` - 移除上下文
- `get_all_contexts()` - 获取所有上下文
- `clear_all()` - 清空所有上下文

#### 使用示例

```python
from src.core.context import ContextManager

# 获取单例管理器
manager = ContextManager()

# 创建多个用户上下文
ctx1 = manager.create_context("user_A", "session_1")
ctx2 = manager.create_context("user_B", "session_2")

# 获取上下文
ctx = manager.get_context(ctx1.context_id)

# 获取所有上下文
all_contexts = manager.get_all_contexts()
print(f"当前活跃上下文：{len(all_contexts)}")

# 清理
manager.remove_context(ctx1.context_id)
manager.clear_all()
```

---

### 9. 便捷函数

```python
from src.core.context import create_context, get_context

# 创建上下文
ctx = create_context("user_123", "session_456")

# 获取上下文
ctx = get_context("ctx_123456")
```

---

## 完整执行流程示例

```python
from src.core.context import (
    AgentContext, TaskPlan, ToolExecution, ValidationResult,
    MemoryInfo, EmotionInfo, FinalResponse, create_context
)


def process_user_request(user_id: str, user_input: str):
    """处理用户请求的完整流程"""
    
    # 1. 创建上下文
    ctx = create_context(user_id)
    ctx.user_input = user_input
    
    # 2. 开始执行
    ctx.start_execution()
    
    try:
        # 3. 任务规划
        ctx.task_plan = TaskPlan(
            original_query=user_input,
            sub_tasks=[
                {"name": "查询天气", "tool": "weather_api", "params": {"city": "北京"}},
                {"name": "检索记忆", "tool": "memory_search", "params": {"query": "北京"}},
            ],
            total_steps=2,
        )
        
        # 4. 执行工具
        while not ctx.task_plan.is_completed():
            task = ctx.task_plan.next_step()
            if task:
                tool_exec = ToolExecution(
                    tool_name=task["tool"],
                    tool_type="api",
                    parameters=task.get("params", {}),
                )
                
                # 调用工具...
                result = execute_tool(task["tool"], task.get("params", {}))
                tool_exec.mark_success(result, execution_time=0.5)
                
                ctx.add_tool_execution(tool_exec)
        
        # 5. 工具结果校验
        ctx.tool_validation = ValidationResult(validation_type="tool_result")
        if validate_tool_results(ctx.get_tool_results()):
            ctx.tool_validation.pass_validation(
                validated_data=ctx.get_tool_results(),
                confidence=0.95
            )
        else:
            ctx.tool_validation.fail_validation(
                issues=["工具结果异常"],
                suggestions=["重试", "使用备用方案"]
            )
            raise Exception("工具校验失败")
        
        # 6. 记忆检索
        ctx.memory_info = MemoryInfo(query=user_input, retrieval_method="hybrid")
        memories = hybrid_retrieval(user_input, top_k=10)
        ctx.memory_info.add_memories(memories, retrieval_time=0.3)
        
        # 7. 情感分析
        ctx.emotion_info = EmotionInfo(query=user_input)
        emotion_result = analyze_emotion(user_input)
        ctx.emotion_info.analyze(
            emotion=emotion_result["emotion"],
            confidence=emotion_result["confidence"],
            keywords=emotion_result["keywords"]
        )
        
        # 8. 生成回复
        response_content = generate_response(ctx)
        ctx.final_response = FinalResponse()
        ctx.final_response.generate(
            content=response_content,
            generation_time=1.2,
            confidence=0.95,
            references=["tool_1", "memory_3"]
        )
        
        # 9. 最终全局校验
        ctx.final_validation = ValidationResult(validation_type="final_answer")
        if validate_final_answer(ctx.final_response.content):
            ctx.final_validation.pass_validation(confidence=0.92)
        else:
            ctx.final_validation.fail_validation(
                issues=["回答质量不足"],
                suggestions=["重新生成", "补充信息"]
            )
            raise Exception("最终校验失败")
        
        # 10. 完成执行
        ctx.complete_execution()
        
        # 11. 返回回复
        return ctx.final_response.content
        
    except Exception as e:
        # 失败处理
        ctx.fail_execution(str(e))
        raise


# 使用示例
response = process_user_request(
    user_id="user_123",
    user_input="帮我查询北京天气并告诉朋友"
)
print(f"回复：{response}")
```

---

## 最佳实践

### 1. 模块间通信

❌ **错误做法**：模块直接互相调用
```python
# 不要这样做
memory_result = memory_module.search(query)
emotion_result = emotion_module.analyze(user_input)
```

✅ **正确做法**：通过 Context 交换数据
```python
# 所有模块读写 Context
ctx.memory_info = MemoryInfo(...)
ctx.emotion_info = EmotionInfo(...)
```

### 2. 校验机制

❌ **错误做法**：跳过校验
```python
# 不要跳过校验
tool_result = call_tool()
# 直接使用...
```

✅ **正确做法**：严格执行两层校验
```python
# 工具结果校验
tool_validation = ValidationResult(validation_type="tool_result")
tool_validation.pass_validation(validated_data=tool_result)
ctx.tool_validation = tool_validation

# 最终全局校验
final_validation = ValidationResult(validation_type="final_answer")
final_validation.pass_validation()
ctx.final_validation = final_validation
```

### 3. 错误处理

❌ **错误做法**：不记录错误到 Context
```python
try:
    execute()
except Exception as e:
    print(f"错误：{e}")
    # Context 中没有错误记录
```

✅ **正确做法**：完整记录错误
```python
try:
    execute()
except Exception as e:
    ctx.fail_execution(str(e))
    # Context 中记录完整错误信息
```

### 4. 序列化持久化

```python
# 保存上下文
json_str = ctx.to_json()
save_to_database(json_str)

# 恢复上下文
json_str = load_from_database()
ctx = AgentContext.from_json(json_str)
```

---

## 扩展性设计

### 1. 任务规划模块扩展

```python
# 未来可接入更复杂的任务规划器
task_plan = TaskPlan(
    original_query=user_input,
    sub_tasks=llm_planner.plan(user_input),  # LLM 规划
    total_steps=len(sub_tasks),
)
```

### 2. 工具模块扩展

```python
# 支持本地工具、MCP 工具、API 工具
tool_exec = ToolExecution(
    tool_name="weather",
    tool_type="mcp",  # 或 "local" 或 "api"
    parameters={},
)
```

### 3. 阿里云 MCP 接入

```python
# 未来接入阿里云 MCP
tool_exec = ToolExecution(
    tool_name="aliyun_weather",
    tool_type="mcp",
    parameters={"city": "北京", "mcp_endpoint": "..."},
)
```

---

## 调试与监控

### 1. 查看执行状态

```python
print(f"状态：{ctx.status}")
print(f"工具调用：{len(ctx.tool_executions)}")
print(f"检索记忆：{ctx.memory_info.memory_count if ctx.memory_info else 0}")
print(f"总耗时：{ctx.total_execution_time:.3f}s")
```

### 2. 导出执行日志

```python
# 导出完整执行记录
execution_log = ctx.to_json(indent=2)
with open(f"execution_{ctx.context_id}.json", "w", encoding="utf-8") as f:
    f.write(execution_log)
```

### 3. 性能分析

```python
# 分析各阶段耗时
tool_time = sum(t.execution_time for t in ctx.tool_executions)
memory_time = ctx.memory_info.retrieval_time if ctx.memory_info else 0
response_time = ctx.final_response.generation_time if ctx.final_response else 0

print(f"工具执行：{tool_time:.3f}s")
print(f"记忆检索：{memory_time:.3f}s")
print(f"回复生成：{response_time:.3f}s")
```

---

## 总结

`AgentContext` 是 SpiritMemory-Agent 的核心数据载体，通过标准化的流程和严格的数据管理，确保系统的：

- ✅ **可维护性**：清晰的数据流和模块边界
- ✅ **可扩展性**：易于接入新模块和功能
- ✅ **可追溯性**：完整的执行记录
- ✅ **可靠性**：两层校验机制保障质量

所有模块开发者应严格遵循本文档规范，确保系统的一致性和稳定性。
