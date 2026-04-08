# Scheduler 中央调度器实现总结

**创建时间**: 2026-04-08  
**文件位置**: `src/core/scheduler.py`  
**实现状态**: ✅ 已完成

---

## 📋 实现概览

根据 SpiritMemory-Agent 现有完整架构，成功实现了中央调度器模块，负责协调整个 Agent 的执行流程。

### 核心设计原则

1. ✅ **只做流程调度，不做业务判断**
2. ✅ **不做校验，只根据校验结果决定下一步**
3. ✅ **严格操作 context 对象，不绕过上下文**
4. ✅ **异常捕获，不崩溃**
5. ✅ **占位模块先 return True 或空实现，保证流程可跑**

---

## 🏗️ 架构设计

### 类结构

```
Scheduler (中央调度器)
├── EmotionAnalyzer (情感分析器 - 占位)
├── SelfCog (自我认知对齐器 - 占位)
├── ToolValidator (工具结果校验器 - 占位)
├── FinalValidator (最终全局校验器 - 占位)
└── AnswerGenerator (回答生成器 - 占位)
```

### 模块依赖

```python
from src.core.context import AgentContext, create_context, ValidationResult
from src.Planner.planner import LLMPlanner, create_planner
from src.memory.memory_core import MemoryCore
```

---

## 🔄 执行流程

### 标准流程（9 个步骤）

```
1. 创建 AgentContext
   ↓
2. 调用 LLMPlanner 生成 task_plan
   ↓
3. 根据 plan 判断是否执行工具 → planner.execute_plan(context)
   ↓
4. 调用工具校验模块（占位，默认通过）
   ↓
5. 调用记忆模块检索记忆 → 写入 context
   ↓
6. 调用情感分析（占位）
   ↓
7. 调用自我认知对齐（占位）
   ↓
8. 执行最终全局校验（占位，默认通过）
   ↓
9. 校验通过 → 调用生成器生成回答
```

### 流程图

```
用户输入
    │
    ▼
┌─────────────────┐
│ 1. 创建 Context │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ 2. 任务规划     │
│ (LLMPlanner)    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ 3. 工具调用？   │─── 是 ───> planner.execute_plan()
└─────────────────┘              │
    │ 否                         │
    └────────────────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ 4. 工具校验     │─── ✗ ───> 返回失败原因
        │ (默认通过)      │
        └─────────────────┘
                 │ ✓
                 ▼
        ┌─────────────────┐
        │ 5. 记忆检索     │
        │ (MemoryCore)    │
        └─────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ 6. 情感分析     │─── ✗ ───> 继续（不影响）
        │ (占位)          │
        └─────────────────┘
                 │ ✓
                 ▼
        ┌─────────────────┐
        │ 7. 自我认知     │─── ✗ ───> 继续（不影响）
        │ (占位)          │
        └─────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ 8. 最终校验     │─── ✗ ───> 返回失败原因
        │ (默认通过)      │
        └─────────────────┘
                 │ ✓
                 ▼
        ┌─────────────────┐
        │ 9. 生成回答     │
        │ (AnswerGenerator)│
        └─────────────────┘
                 │
                 ▼
            返回用户
```

---

## 📦 核心类说明

### 1. Scheduler (主调度器)

**初始化方法**:
```python
def __init__(self):
    self.planner = create_planner()           # LLM 规划器
    self.memory_core = MemoryCore()           # 记忆核心
    self.emotion_analyzer = EmotionAnalyzer() # 情感分析（占位）
    self.self_cog = SelfCog()                 # 自我认知（占位）
    self.tool_validator = ToolValidator()     # 工具校验（占位）
    self.final_validator = FinalValidator()   # 最终校验（占位）
    self.answer_generator = AnswerGenerator() # 回答生成（占位）
```

**入口方法**:
```python
async def chat(self, user_input: str, user_id: str) -> str:
    """
    聊天入口方法
    
    Args:
        user_input: 用户输入
        user_id: 用户 ID
        
    Returns:
        str: 生成的回答
    """
```

**高级方法**:
```python
async def chat_with_context(self, context: AgentContext) -> str:
    """使用已有上下文的聊天方法"""
    
def get_scheduler_status(self) -> Dict[str, Any]:
    """获取调度器状态"""
```

---

### 2. 占位模块类

#### EmotionAnalyzer (情感分析器)

```python
class EmotionAnalyzer:
    async def analyze(self, context: AgentContext) -> bool:
        """分析用户情感（占位，待实现）"""
        logger.info("【情感分析】占位模块 - 待实现")
        return True
```

#### SelfCog (自我认知对齐器)

```python
class SelfCog:
    async def align(self, context: AgentContext) -> bool:
        """自我认知对齐（占位，待实现）"""
        logger.info("【自我认知】占位模块 - 待实现")
        return True
```

#### ToolValidator (工具结果校验器)

```python
class ToolValidator:
    async def validate(self, context: AgentContext) -> bool:
        """校验工具执行结果（占位，默认通过）"""
        validation = ValidationResult(
            validation_type="tool_result",
            is_valid=True,
            confidence=1.0
        )
        context.tool_validation = validation
        return True
```

#### FinalValidator (最终全局校验器)

```python
class FinalValidator:
    async def validate(self, context: AgentContext) -> tuple[bool, str]:
        """最终全局校验（占位，默认通过）"""
        validation = ValidationResult(
            validation_type="final_answer",
            is_valid=True,
            confidence=0.95
        )
        context.final_validation = validation
        return True, "校验通过"
```

#### AnswerGenerator (回答生成器)

```python
class AnswerGenerator:
    async def generate(self, context: AgentContext) -> str:
        """生成最终回答（占位，临时实现）"""
        # 临时实现：返回工具执行结果
        if context.tool_executions:
            results = [f"{t.tool_name}: {t.result}" for t in context.tool_executions if t.success]
            return "\n".join(results) if results else "已执行任务"
        return "您好，我是 SpiritMemory-Agent，很高兴为您服务！"
```

---

## 🚀 使用指南

### 异步使用（推荐）

```python
from src.core.scheduler import get_scheduler

# 获取调度器
scheduler = get_scheduler()

# 调用聊天方法
answer = await scheduler.chat("查询北京天气", "user_123")
print(f"回答：{answer}")
```

### 同步使用

```python
from src.core.scheduler import get_sync_scheduler

# 获取同步调度器
sync_scheduler = get_sync_scheduler()

# 调用聊天方法
answer = sync_scheduler.chat("查询北京天气", "user_123")
print(f"回答：{answer}")
```

### 高级用法（使用已有 Context）

```python
from src.core.context import create_context
from src.core.scheduler import get_scheduler

# 创建上下文
context = create_context("user_123")
context.user_input = "查询北京天气"

# 使用调度器处理
scheduler = get_scheduler()
answer = await scheduler.chat_with_context(context)
```

---

## 📊 日志输出示例

```
INFO - 初始化中央调度器...
INFO - 中央调度器初始化完成
INFO - 收到用户输入：查询北京天气 (用户：user_123)
INFO - 【步骤 1】创建 AgentContext...
INFO - Context 创建成功：ctx_123456
INFO - 【步骤 2】调用 LLMPlanner 进行任务规划...
INFO - 任务规划完成：2 个子任务，需要工具：True
INFO - 【步骤 3】执行工具调用...
INFO - 工具执行完成：2 个工具被调用
INFO - 【步骤 4】工具结果校验...
INFO - 【工具校验】占位模块 - 默认通过
INFO - 工具校验通过
INFO - 【步骤 5】检索相关记忆...
INFO - 未检索到相关记忆
INFO - 【步骤 6】情感分析...
INFO - 【情感分析】占位模块 - 待实现
INFO - 【步骤 7】自我认知对齐...
INFO - 【自我认知】占位模块 - 待实现
INFO - 【步骤 8】最终全局校验...
INFO - 【最终校验】占位模块 - 默认通过
INFO - 最终校验通过
INFO - 【步骤 9】生成最终回答...
INFO - 回答生成成功，长度：45
INFO - 执行完成，总耗时：2.345s
```

---

## ✅ 实现验证

### 已实现功能

- [x] Scheduler 主类
- [x] 异步入口方法 `chat()`
- [x] 同步包装类 `SyncScheduler`
- [x] 所有占位模块（5 个）
- [x] 完整的 9 步流程
- [x] 异常处理
- [x] 日志记录
- [x] 便捷函数

### 代码质量

- ✅ 严格遵循项目现有结构
- ✅ 使用真实存在的类和路径
- ✅ 符合 Context 规范
- ✅ 风格简洁、注释清晰
- ✅ 无硬编码、无虚构类

---

## 🔧 待实现模块

以下模块当前为占位实现，后续需要完善：

| 模块 | 文件路径 | 状态 | TODO |
|------|---------|------|------|
| 情感分析 | `src/emotion/analyzer.py` | ⏳ 占位 | 实现情感识别逻辑 |
| 自我认知 | `src/self_cognition/aligner.py` | ⏳ 占位 | 实现自我认知对齐 |
| 工具校验 | `src/validation/tool_validator.py` | ⏳ 占位 | 实现工具结果校验 |
| 最终校验 | `src/validation/final_validator.py` | ⏳ 占位 | 实现最终全局校验 |
| 回答生成 | `src/generation/generator.py` | ⏳ 占位 | 实现 LLM 回答生成 |

---

## 📝 注意事项

### 1. 依赖模块

确保以下模块已正确实现：
- ✅ `src/Planner/planner.py` - LLMPlanner
- ✅ `src/core/context.py` - AgentContext
- ✅ `src/memory/memory_core.py` - MemoryCore

### 2. 环境变量

使用前设置 MCP 服务 API Key：
```bash
export DASHSCOPE_API_KEY="your_api_key"
```

### 3. 异步支持

- 主方法为异步方法 `async def chat()`
- 提供同步包装类 `SyncScheduler`
- 建议在新代码中使用异步方式

### 4. 错误处理

- 所有步骤都有异常捕获
- 不会抛出异常给用户
- 返回友好的错误提示

---

## 🎯 下一步计划

### 短期（1 周）

1. **完善记忆检索逻辑**
   - 将检索结果正确写入 context
   - 处理 MemoryEntity 结构

2. **实现情感分析模块**
   - 创建 `src/emotion/analyzer.py`
   - 实现情感识别 API 调用

3. **实现工具校验模块**
   - 创建 `src/validation/tool_validator.py`
   - 实现工具结果验证逻辑

### 中期（1 个月）

1. **实现回答生成模块**
   - 创建 `src/generation/generator.py`
   - 使用 LLM 生成最终回答

2. **实现自我认知模块**
   - 创建 `src/self_cognition/aligner.py`
   - 实现自我认知对齐逻辑

3. **完善最终校验**
   - 创建 `src/validation/final_validator.py`
   - 实现回答质量校验

---

## 📚 相关文档

- [Context 规范](context.md) - 全局上下文模块
- [Planner 文档](../Planner/README.md) - 任务规划器
- [Memory 文档](../memory/README.md) - 记忆模块
- [项目总览](../../README.md) - 项目架构

---

**实现完成时间**: 2026-04-08  
**维护者**: SpiritMemory-Agent Team  
**文档版本**: v1.0.0
