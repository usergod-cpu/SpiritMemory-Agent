"""
全局上下文模块

提供全局唯一的数据载体 AgentContext，所有模块只读写该对象，不互相调用
严格遵循执行流程：用户输入 → 任务规划 → 工具调用 → 工具校验 → 记忆/情感 → 最终全局校验 → 生成回答
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.logger import get_logger
from utils.common_tools import generate_uuid, get_current_time, format_datetime


logger = get_logger("AgentContext")


@dataclass
class TaskPlan:
    """
    任务规划结果
    
    存储任务分解和调度信息
    """
    
    task_id: str = field(default_factory=generate_uuid)
    original_query: str = ""
    sub_tasks: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    total_steps: int = 0
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = field(default_factory=lambda: format_datetime())
    updated_at: str = field(default_factory=lambda: format_datetime())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "original_query": self.original_query,
            "sub_tasks": self.sub_tasks,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
    
    def next_step(self) -> Optional[Dict[str, Any]]:
        """获取下一步任务"""
        if self.current_step < self.total_steps:
            task = self.sub_tasks[self.current_step]
            self.current_step += 1
            self.updated_at = format_datetime()
            return task
        return None
    
    def is_completed(self) -> bool:
        """检查是否完成"""
        return self.current_step >= self.total_steps or self.status == "completed"


@dataclass
class ToolExecution:
    """
    工具执行信息
    
    存储工具调用和结果
    """
    
    tool_id: str = field(default_factory=generate_uuid)
    tool_name: str = ""
    tool_type: str = ""  # local, mcp, api
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = False
    error_message: str = ""
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: format_datetime())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "tool_type": self.tool_type,
            "parameters": self.parameters,
            "result": self.result,
            "success": self.success,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    def mark_success(self, result: Any, execution_time: float = 0.0) -> None:
        """标记执行成功"""
        self.result = result
        self.success = True
        self.execution_time = execution_time
        self.timestamp = format_datetime()
        logger.info(f"工具执行成功：{self.tool_name}, 耗时：{execution_time:.3f}s")
    
    def mark_failed(self, error_message: str) -> None:
        """标记执行失败"""
        self.error_message = error_message
        self.success = False
        self.timestamp = format_datetime()
        logger.error(f"工具执行失败：{self.tool_name}, 错误：{error_message}")


@dataclass
class ValidationResult:
    """
    校验结果
    
    用于工具结果校验和最终全局校验
    """
    
    validation_id: str = field(default_factory=generate_uuid)
    validation_type: str = ""  # tool_result, final_answer
    is_valid: bool = False
    confidence: float = 0.0
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    raw_data: Any = None
    validated_data: Any = None
    timestamp: str = field(default_factory=lambda: format_datetime())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "validation_id": self.validation_id,
            "validation_type": self.validation_type,
            "is_valid": self.is_valid,
            "confidence": self.confidence,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "raw_data": self.raw_data,
            "validated_data": self.validated_data,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    def pass_validation(self, validated_data: Any = None, confidence: float = 1.0) -> None:
        """通过校验"""
        self.is_valid = True
        self.validated_data = validated_data
        self.confidence = confidence
        self.timestamp = format_datetime()
        logger.info(f"校验通过：{self.validation_type}, 置信度：{confidence:.2f}")
    
    def fail_validation(self, issues: List[str], suggestions: Optional[List[str]] = None) -> None:
        """未通过校验"""
        self.is_valid = False
        self.issues = issues
        self.suggestions = suggestions or []
        self.timestamp = format_datetime()
        logger.warning(f"校验失败：{self.validation_type}, 问题：{issues}")


@dataclass
class MemoryInfo:
    """
    记忆信息
    
    存储检索到的相关记忆
    """
    
    query: str = ""
    retrieved_memories: List[Dict[str, Any]] = field(default_factory=list)
    memory_count: int = 0
    retrieval_method: str = ""  # hybrid, semantic, keyword
    retrieval_time: float = 0.0
    top_k: int = 10
    similarity_threshold: float = 0.7
    timestamp: str = field(default_factory=lambda: format_datetime())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "retrieved_memories": self.retrieved_memories,
            "memory_count": self.memory_count,
            "retrieval_method": self.retrieval_method,
            "retrieval_time": self.retrieval_time,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    def add_memories(self, memories: List[Dict[str, Any]], retrieval_time: float = 0.0) -> None:
        """添加检索到的记忆"""
        self.retrieved_memories = memories
        self.memory_count = len(memories)
        self.retrieval_time = retrieval_time
        self.timestamp = format_datetime()
        logger.info(f"检索到 {self.memory_count} 条记忆，耗时：{retrieval_time:.3f}s")
    
    def get_relevant_memories(self, min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """获取相关记忆"""
        if min_similarity <= 0.0:
            return self.retrieved_memories
        return [
            m for m in self.retrieved_memories 
            if m.get("similarity", 0.0) >= min_similarity
        ]


@dataclass
class EmotionInfo:
    """
    情感信息
    
    存储用户情感分析结果
    """
    
    query: str = ""
    emotion: str = ""  # happy, sad, angry, anxious, neutral, etc.
    confidence: float = 0.0
    intensity: float = 0.0  # 情感强度 0-1
    sentiment_score: float = 0.0  # 情感得分 -1 到 1
    keywords: List[str] = field(default_factory=list)
    response_strategy: str = ""  # 响应策略
    timestamp: str = field(default_factory=lambda: format_datetime())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "emotion": self.emotion,
            "confidence": self.confidence,
            "intensity": self.intensity,
            "sentiment_score": self.sentiment_score,
            "keywords": self.keywords,
            "response_strategy": self.response_strategy,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    def analyze(self, emotion: str, confidence: float, intensity: float = 0.5, 
                sentiment_score: float = 0.0, keywords: Optional[List[str]] = None) -> None:
        """设置情感分析结果"""
        self.emotion = emotion
        self.confidence = max(0.0, min(1.0, confidence))
        self.intensity = max(0.0, min(1.0, intensity))
        self.sentiment_score = max(-1.0, min(1.0, sentiment_score))
        self.keywords = keywords or []
        self.timestamp = format_datetime()
        
        # 根据情感设置响应策略
        self.response_strategy = self._determine_response_strategy(emotion)
        logger.info(f"情感分析：{emotion}, 置信度：{confidence:.2f}, 策略：{self.response_strategy}")
    
    def _determine_response_strategy(self, emotion: str) -> str:
        """根据情感确定响应策略"""
        strategies = {
            "happy": "share_and_celebrate",
            "sad": "comfort_and_support",
            "angry": "calm_and_understand",
            "anxious": "reassure_and_guide",
            "neutral": "informative_and_helpful",
            "excited": "enthusiastic_and_supportive",
            "frustrated": "patient_and_solution_oriented",
        }
        return strategies.get(emotion, "informative_and_helpful")


@dataclass
class FinalResponse:
    """
    最终回复
    
    存储生成的回答
    """
    
    response_id: str = field(default_factory=generate_uuid)
    content: str = ""
    response_type: str = "text"  # text, code, mixed
    references: List[str] = field(default_factory=list)  # 引用的记忆或工具结果
    confidence: float = 0.0
    generation_time: float = 0.0
    token_count: int = 0
    timestamp: str = field(default_factory=lambda: format_datetime())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "response_id": self.response_id,
            "content": self.content,
            "response_type": self.response_type,
            "references": self.references,
            "confidence": self.confidence,
            "generation_time": self.generation_time,
            "token_count": self.token_count,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    def generate(self, content: str, generation_time: float = 0.0, 
                 confidence: float = 1.0, references: Optional[List[str]] = None) -> None:
        """生成回复"""
        self.content = content
        self.generation_time = generation_time
        self.confidence = confidence
        self.references = references or []
        self.token_count = len(content)
        self.timestamp = format_datetime()
        logger.info(f"生成回复：{len(content)} 字符，耗时：{generation_time:.3f}s")


@dataclass
class AgentContext:
    """
    全局上下文类
    
    作为全局唯一数据载体，所有模块只读写该对象，不互相调用
    严格遵循执行流程：用户输入 → 任务规划 → 工具调用 → 工具校验 → 记忆/情感 → 最终全局校验 → 生成回答
    """
    
    # ========== 基础信息 ==========
    context_id: str = field(default_factory=generate_uuid)
    session_id: str = ""
    user_id: str = ""
    created_at: str = field(default_factory=lambda: format_datetime())
    updated_at: str = field(default_factory=lambda: format_datetime())
    
    # ========== 用户输入 ==========
    user_input: str = ""
    input_timestamp: str = ""
    input_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # ========== 任务规划 ==========
    task_plan: Optional[TaskPlan] = None
    
    # ========== 工具执行 ==========
    tool_executions: List[ToolExecution] = field(default_factory=list)
    tool_validation: Optional[ValidationResult] = None
    
    # ========== 记忆与情感 ==========
    memory_info: Optional[MemoryInfo] = None
    emotion_info: Optional[EmotionInfo] = None
    
    # ========== 最终校验与回复 ==========
    final_validation: Optional[ValidationResult] = None
    final_response: Optional[FinalResponse] = None
    
    # ========== 执行状态 ==========
    status: str = "initialized"  # initialized, planning, executing, validating, completed, failed
    error_message: str = ""
    execution_start_time: str = ""
    execution_end_time: str = ""
    total_execution_time: float = 0.0
    
    # ========== 扩展字段（用于未来功能） ==========
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 字典数据
        """
        return {
            "context_id": self.context_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_input": self.user_input,
            "input_timestamp": self.input_timestamp,
            "input_metadata": self.input_metadata,
            "task_plan": self.task_plan.to_dict() if self.task_plan else None,
            "tool_executions": [t.to_dict() for t in self.tool_executions],
            "tool_validation": self.tool_validation.to_dict() if self.tool_validation else None,
            "memory_info": self.memory_info.to_dict() if self.memory_info else None,
            "emotion_info": self.emotion_info.to_dict() if self.emotion_info else None,
            "final_validation": self.final_validation.to_dict() if self.final_validation else None,
            "final_response": self.final_response.to_dict() if self.final_response else None,
            "status": self.status,
            "error_message": self.error_message,
            "execution_start_time": self.execution_start_time,
            "execution_end_time": self.execution_end_time,
            "total_execution_time": self.total_execution_time,
            "metadata": self.metadata,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        转换为 JSON 字符串
        
        Args:
            indent: JSON 缩进
        
        Returns:
            str: JSON 字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentContext':
        """
        从字典创建上下文
        
        Args:
            data: 字典数据
        
        Returns:
            AgentContext: 上下文对象
        """
        context = cls()
        context.context_id = data.get("context_id", generate_uuid())
        context.session_id = data.get("session_id", "")
        context.user_id = data.get("user_id", "")
        context.created_at = data.get("created_at", format_datetime())
        context.updated_at = data.get("updated_at", format_datetime())
        context.user_input = data.get("user_input", "")
        context.input_timestamp = data.get("input_timestamp", "")
        context.input_metadata = data.get("input_metadata", {})
        
        task_plan_data = data.get("task_plan")
        if task_plan_data:
            context.task_plan = TaskPlan(**task_plan_data)
        
        tool_executions_data = data.get("tool_executions", [])
        context.tool_executions = [ToolExecution(**t) for t in tool_executions_data]
        
        tool_validation_data = data.get("tool_validation")
        if tool_validation_data:
            context.tool_validation = ValidationResult(**tool_validation_data)
        
        memory_info_data = data.get("memory_info")
        if memory_info_data:
            context.memory_info = MemoryInfo(**memory_info_data)
        
        emotion_info_data = data.get("emotion_info")
        if emotion_info_data:
            context.emotion_info = EmotionInfo(**emotion_info_data)
        
        final_validation_data = data.get("final_validation")
        if final_validation_data:
            context.final_validation = ValidationResult(**final_validation_data)
        
        final_response_data = data.get("final_response")
        if final_response_data:
            context.final_response = FinalResponse(**final_response_data)
        
        context.status = data.get("status", "initialized")
        context.error_message = data.get("error_message", "")
        context.execution_start_time = data.get("execution_start_time", "")
        context.execution_end_time = data.get("execution_end_time", "")
        context.total_execution_time = data.get("total_execution_time", 0.0)
        context.metadata = data.get("metadata", {})
        
        return context
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentContext':
        """
        从 JSON 字符串创建上下文
        
        Args:
            json_str: JSON 字符串
        
        Returns:
            AgentContext: 上下文对象
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update(self) -> None:
        """更新上下文时间戳"""
        self.updated_at = format_datetime()
    
    def start_execution(self) -> None:
        """开始执行"""
        self.status = "planning"
        self.execution_start_time = format_datetime()
        self.updated_at = format_datetime()
        logger.info(f"开始执行：{self.context_id}")
    
    def complete_execution(self) -> None:
        """完成执行"""
        self.status = "completed"
        self.execution_end_time = format_datetime()
        
        if self.execution_start_time:
            start = datetime.strptime(self.execution_start_time, "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(self.execution_end_time, "%Y-%m-%d %H:%M:%S")
            self.total_execution_time = (end - start).total_seconds()
        
        self.updated_at = format_datetime()
        logger.info(f"执行完成：{self.context_id}, 总耗时：{self.total_execution_time:.3f}s")
    
    def fail_execution(self, error_message: str) -> None:
        """失败执行"""
        self.status = "failed"
        self.error_message = error_message
        self.execution_end_time = format_datetime()
        
        if self.execution_start_time:
            start = datetime.strptime(self.execution_start_time, "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(self.execution_end_time, "%Y-%m-%d %H:%M:%S")
            self.total_execution_time = (end - start).total_seconds()
        
        self.updated_at = format_datetime()
        logger.error(f"执行失败：{self.context_id}, 错误：{error_message}")
    
    def add_tool_execution(self, tool_execution: ToolExecution) -> None:
        """添加工具执行记录"""
        self.tool_executions.append(tool_execution)
        self.updated_at = format_datetime()
        logger.debug(f"添加工具执行：{tool_execution.tool_name}")
    
    def get_tool_results(self) -> List[Any]:
        """获取所有工具执行结果"""
        return [t.result for t in self.tool_executions if t.success]
    
    def clear(self) -> None:
        """清空上下文（保留基础信息）"""
        self.user_input = ""
        self.input_timestamp = ""
        self.input_metadata = {}
        self.task_plan = None
        self.tool_executions = []
        self.tool_validation = None
        self.memory_info = None
        self.emotion_info = None
        self.final_validation = None
        self.final_response = None
        self.status = "initialized"
        self.error_message = ""
        self.execution_start_time = ""
        self.execution_end_time = ""
        self.total_execution_time = 0.0
        self.metadata = {}
        self.updated_at = format_datetime()
        logger.debug(f"上下文已清空：{self.context_id}")
    
    def __repr__(self) -> str:
        return (
            f"AgentContext(id={self.context_id}, user={self.user_id}, "
            f"status={self.status}, tools={len(self.tool_executions)})"
        )


# ========== 全局上下文管理器（可选单例模式） ==========
class ContextManager:
    """
    上下文管理器
    
    提供全局唯一的上下文实例管理
    """
    
    _instance: Optional['ContextManager'] = None
    _contexts: Dict[str, AgentContext] = {}
    
    def __new__(cls) -> 'ContextManager':
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_context(self, user_id: str, session_id: str = "") -> AgentContext:
        """创建新上下文"""
        context = AgentContext(user_id=user_id, session_id=session_id or generate_uuid())
        self._contexts[context.context_id] = context
        logger.info(f"创建上下文：{context.context_id}, 用户：{user_id}")
        return context
    
    def get_context(self, context_id: str) -> Optional[AgentContext]:
        """获取上下文"""
        return self._contexts.get(context_id)
    
    def remove_context(self, context_id: str) -> bool:
        """移除上下文"""
        if context_id in self._contexts:
            del self._contexts[context_id]
            logger.info(f"移除上下文：{context_id}")
            return True
        return False
    
    def get_all_contexts(self) -> Dict[str, AgentContext]:
        """获取所有上下文"""
        return self._contexts.copy()
    
    def clear_all(self) -> None:
        """清空所有上下文"""
        self._contexts.clear()
        logger.info("清空所有上下文")


# ========== 便捷函数 ==========
def create_context(user_id: str, session_id: str = "") -> AgentContext:
    """创建上下文的便捷函数"""
    manager = ContextManager()
    return manager.create_context(user_id, session_id)


def get_context(context_id: str) -> Optional[AgentContext]:
    """获取上下文的便捷函数"""
    manager = ContextManager()
    return manager.get_context(context_id)
