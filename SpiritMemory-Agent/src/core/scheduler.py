"""
中央调度器模块

负责协调整个 Agent 的执行流程，按照固定流程调度各模块
严格遵循：用户输入 → 任务规划 → 工具调用 → 工具校验 → 记忆/情感 → 最终全局校验 → 生成回答
"""

from typing import Optional, Dict, Any, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.logger import get_logger
from src.core.context import AgentContext, create_context, ValidationResult, FinalResponse
from src.Planner.planner import LLMPlanner, create_planner
from src.memory.memory_core import MemoryCore

logger = get_logger("Scheduler")


class EmotionAnalyzer:
    """情感分析器（占位实现）"""
    
    def __init__(self):
        self.enabled = True
    
    async def analyze(self, context: AgentContext) -> bool:
        """
        分析用户情感（占位）
        
        Args:
            context: AgentContext 上下文
            
        Returns:
            bool: 是否成功
        """
        logger.info("【情感分析】占位模块 - 待实现")
        # TODO: 实现情感分析逻辑
        # context.emotion_info = EmotionInfo(...)
        return True


class SelfCog:
    """自我认知对齐器（占位实现）"""
    
    def __init__(self):
        self.enabled = True
    
    async def align(self, context: AgentContext) -> bool:
        """
        自我认知对齐（占位）
        
        Args:
            context: AgentContext 上下文
            
        Returns:
            bool: 是否成功
        """
        logger.info("【自我认知】占位模块 - 待实现")
        # TODO: 实现自我认知对齐逻辑
        return True


class ToolValidator:
    """工具结果校验器（占位实现）"""
    
    def __init__(self):
        self.enabled = True
    
    async def validate(self, context: AgentContext) -> bool:
        """
        校验工具执行结果（占位，默认通过）
        
        Args:
            context: AgentContext 上下文
            
        Returns:
            bool: 是否通过校验
        """
        logger.info("【工具校验】占位模块 - 默认通过")
        
        # 创建校验结果
        validation = ValidationResult(
            validation_type="tool_result",
            is_valid=True,
            confidence=1.0,
            issues=[],
            suggestions=[]
        )
        context.tool_validation = validation
        
        return True


class FinalValidator:
    """最终全局校验器（占位实现）"""
    
    def __init__(self):
        self.enabled = True
    
    async def validate(self, context: AgentContext) -> tuple[bool, str]:
        """
        最终全局校验（占位，默认通过）
        
        Args:
            context: AgentContext 上下文
            
        Returns:
            tuple[bool, str]: (是否通过，原因)
        """
        logger.info("【最终校验】占位模块 - 默认通过")
        
        # 创建校验结果
        validation = ValidationResult(
            validation_type="final_answer",
            is_valid=True,
            confidence=0.95,
            issues=[],
            suggestions=[]
        )
        context.final_validation = validation
        
        return True, "校验通过"


class AnswerGenerator:
    """回答生成器（占位实现）"""
    
    def __init__(self):
        self.enabled = True
    
    async def generate(self, context: AgentContext) -> str:
        """
        生成最终回答（占位）
        
        Args:
            context: AgentContext 上下文
            
        Returns:
            str: 生成的回答
        """
        logger.info("【回答生成】占位模块 - 待实现")
        
        # TODO: 实现回答生成逻辑
        # 基于 context 中的工具结果、记忆、情感等生成回答
        
        # 临时实现：返回工具执行结果
        if context.tool_executions:
            results = []
            for exec_info in context.tool_executions:
                if exec_info.success:
                    results.append(f"{exec_info.tool_name}: {exec_info.result}")
            return "\n".join(results) if results else "已执行任务"
        
        return "您好，我是 SpiritMemory-Agent，很高兴为您服务！"


class Scheduler:
    """
    中央调度器
    
    负责协调整个 Agent 的执行流程，按照固定流程调度各模块
    只做流程调度，不做任何业务判断
    """
    
    def __init__(self):
        """初始化调度器，创建所有模块实例"""
        logger.info("初始化中央调度器...")
        
        # 初始化规划器
        self.planner = create_planner()
        
        # 初始化记忆核心
        self.memory_core = MemoryCore()
        
        # 初始化占位模块
        self.emotion_analyzer = EmotionAnalyzer()
        self.self_cog = SelfCog()
        self.tool_validator = ToolValidator()
        self.final_validator = FinalValidator()
        self.answer_generator = AnswerGenerator()
        
        logger.info("中央调度器初始化完成")
    
    async def chat(self, user_input: str, user_id: str) -> str:
        """
        聊天入口方法
        
        Args:
            user_input: 用户输入
            user_id: 用户 ID
            
        Returns:
            str: 生成的回答
        """
        logger.info(f"收到用户输入：{user_input} (用户：{user_id})")
        
        try:
            # ========== 步骤 1: 创建 AgentContext ==========
            logger.info("【步骤 1】创建 AgentContext...")
            context = create_context(user_id)
            context.user_input = user_input
            context.start_execution()
            logger.info(f"Context 创建成功：{context.context_id}")
            
            # ========== 步骤 2: 调用 LLMPlanner 生成 task_plan ==========
            logger.info("【步骤 2】调用 LLMPlanner 进行任务规划...")
            task_plan = self.planner.plan_task(user_input)
            context.task_plan = task_plan
            logger.info(f"任务规划完成：{task_plan.total_steps} 个子任务，需要工具：{task_plan.metadata.get('need_tools', False)}")
            
            # ========== 步骤 3: 根据 plan 判断是否执行工具 ==========
            if task_plan.metadata.get('need_tools', False) and task_plan.sub_tasks:
                logger.info("【步骤 3】执行工具调用...")
                self.planner.execute_plan(context)
                logger.info(f"工具执行完成：{len(context.tool_executions)} 个工具被调用")
            else:
                logger.info("【步骤 3】无需工具调用，跳过")
            
            # ========== 步骤 4: 调用工具校验模块 ==========
            logger.info("【步骤 4】工具结果校验...")
            tool_validation_passed = await self.tool_validator.validate(context)
            if not tool_validation_passed:
                logger.warning("工具校验未通过，返回原因")
                context.fail_execution("工具校验未通过")
                return f"抱歉，工具执行结果校验失败：{context.tool_validation.issues}"
            logger.info("工具校验通过")
            
            # ========== 步骤 5: 调用记忆模块检索记忆 ==========
            logger.info("【步骤 5】检索相关记忆...")
            try:
                memories = self.memory_core.retrieve_relevant_memories(context)
                if memories:
                    logger.info(f"检索到 {len(memories)} 条记忆")
                    # 将记忆写入 context（需要根据实际 MemoryEntity 结构调整）
                    # TODO: 完善记忆写入逻辑
                else:
                    logger.info("未检索到相关记忆")
            except Exception as e:
                logger.error(f"记忆检索失败：{str(e)}")
                # 记忆检索失败不影响后续流程
            
            # ========== 步骤 6: 调用情感分析 ==========
            logger.info("【步骤 6】情感分析...")
            emotion_analyzed = await self.emotion_analyzer.analyze(context)
            if not emotion_analyzed:
                logger.warning("情感分析失败，但不影响后续流程")
            
            # ========== 步骤 7: 调用自我认知对齐 ==========
            logger.info("【步骤 7】自我认知对齐...")
            self_cog_aligned = await self.self_cog.align(context)
            if not self_cog_aligned:
                logger.warning("自我认知对齐失败，但不影响后续流程")
            
            # ========== 步骤 8: 执行最终全局校验 ==========
            logger.info("【步骤 8】最终全局校验...")
            final_valid, reason = await self.final_validator.validate(context)
            if not final_valid:
                logger.warning(f"最终校验未通过：{reason}")
                context.fail_execution(reason)
                return f"抱歉，回答生成前的最终校验未通过：{reason}"
            logger.info("最终校验通过")
            
            # ========== 步骤 9: 校验通过，调用生成器生成回答 ==========
            logger.info("【步骤 9】生成最终回答...")
            answer = await self.answer_generator.generate(context)
            logger.info(f"回答生成成功，长度：{len(answer)}")
            
            # 完成执行
            context.complete_execution()
            logger.info(f"执行完成，总耗时：{context.total_execution_time:.3f}s")
            
            return answer
            
        except Exception as e:
            logger.error(f"调度器执行异常：{str(e)}", exc_info=True)
            # 异常时返回友好提示
            return f"抱歉，处理您的请求时遇到错误：{str(e)}"
    
    async def chat_with_context(self, context: AgentContext) -> str:
        """
        使用已有上下文的聊天方法（高级用法）
        
        Args:
            context: 已有的 AgentContext 实例
            
        Returns:
            str: 生成的回答
        """
        logger.info(f"使用已有 Context 进行处理：{context.context_id}")
        
        try:
            # 复用 chat 方法的逻辑，但使用传入的 context
            user_input = context.user_input
            
            # 如果还没有 task_plan，则生成
            if not context.task_plan:
                logger.info("生成任务规划...")
                context.task_plan = self.planner.plan_task(user_input)
            
            # 执行后续步骤（从步骤 3 开始）
            # ...（逻辑与 chat 方法相同）
            
            return await self.chat(user_input, context.user_id)
            
        except Exception as e:
            logger.error(f"Context 处理异常：{str(e)}", exc_info=True)
            return f"处理失败：{str(e)}"
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """
        获取调度器状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        return {
            "planner_initialized": self.planner is not None,
            "memory_core_initialized": self.memory_core is not None,
            "emotion_analyzer_enabled": self.emotion_analyzer.enabled,
            "self_cog_enabled": self.self_cog.enabled,
            "tool_validator_enabled": self.tool_validator.enabled,
            "final_validator_enabled": self.final_validator.enabled,
            "answer_generator_enabled": self.answer_generator.enabled,
        }


# ========== 便捷函数 ==========
def get_scheduler() -> Scheduler:
    """获取调度器实例的便捷函数"""
    return Scheduler()


# ========== 同步版本（用于不支持异步的场景）==========
class SyncScheduler:
    """同步版本的调度器（包装异步方法）"""
    
    def __init__(self):
        self.async_scheduler = Scheduler()
    
    def chat(self, user_input: str, user_id: str) -> str:
        """同步聊天方法"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.async_scheduler.chat(user_input, user_id)
        )


def get_sync_scheduler() -> SyncScheduler:
    """获取同步调度器实例的便捷函数"""
    return SyncScheduler()
