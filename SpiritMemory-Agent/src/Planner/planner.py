import json
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.logger import get_logger
from utils.common_tools import generate_uuid, format_datetime
from src.core.context import AgentContext, TaskPlan, ToolExecution, ValidationResult

logger = get_logger("Planner")

@dataclass
class MCPTool:
    """MCP 工具信息"""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    mcp_endpoint: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "mcp_endpoint": self.mcp_endpoint,
        }


class MCPClient:
    """MCP 客户端 - 处理与阿里云 MCP 服务的通信"""
    
    MCP_ENDPOINTS = {
        "amap-maps": "https://dashscope.aliyuncs.com/api/v1/mcps/amap-maps/mcp",
        "code-interpreter": "https://dashscope.aliyuncs.com/api/v1/mcps/code-interpreter/mcp",
        "web-search": "https://dashscope.aliyuncs.com/api/v1/mcps/web-search/mcp",
    }
    
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY 环境变量未设置")
        self.available_tools: List[MCPTool] = []
    
    def _get_endpoint(self, tool_name: str) -> str:
        """获取工具对应的 MCP 端点"""
        if "map" in tool_name.lower() or "amap" in tool_name.lower() or "location" in tool_name.lower():
            return self.MCP_ENDPOINTS["amap-maps"]
        elif "code" in tool_name.lower() or "interpreter" in tool_name.lower() or "calculate" in tool_name.lower():
            return self.MCP_ENDPOINTS["code-interpreter"]
        elif "search" in tool_name.lower() or "web" in tool_name.lower() or "internet" in tool_name.lower():
            return self.MCP_ENDPOINTS["web-search"]
        else:
            logger.warning(f"未知工具类型：{tool_name}，使用默认端点")
            return self.MCP_ENDPOINTS["web-search"]
    
    def list_tools(self) -> List[MCPTool]:
        """获取可用工具列表"""
        try:
            import requests
            
            tools = []
            for tool_type, endpoint in self.MCP_ENDPOINTS.items():
                try:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    payload = {"method": "tools/list", "params": {}}
                    
                    response = requests.post(
                        endpoint,
                        headers=headers,
                        json=payload,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result and "result" in result:
                            for tool_data in result["result"]:
                                tool = MCPTool(
                                    name=tool_data.get("name", ""),
                                    description=tool_data.get("description", ""),
                                    input_schema=tool_data.get("inputSchema", {}),
                                    mcp_endpoint=endpoint
                                )
                                tools.append(tool)
                    else:
                        logger.warning(f"获取工具列表失败：{tool_type}, 状态码：{response.status_code}")
                        
                except Exception as e:
                    logger.error(f"获取 MCP 工具失败：{tool_type}, 错误：{str(e)}")
                    continue
            
            self.available_tools = tools
            return tools
            
        except Exception as e:
            logger.error(f"获取 MCP 工具列表异常：{str(e)}")
            return []
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            Tuple[bool, Any]: (是否成功，结果/错误信息)
        """
        try:
            import requests
            
            endpoint = self._get_endpoint(tool_name)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "parameters": parameters
                }
            }
            
            logger.info(f"调用 MCP 工具：{tool_name}, 端点：{endpoint}")
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result and "result" in result:
                    logger.info(f"MCP 工具调用成功：{tool_name}")
                    return True, result["result"]
                else:
                    error_msg = f"MCP 工具返回空结果：{tool_name}"
                    logger.warning(error_msg)
                    return False, error_msg
            else:
                error_msg = f"MCP 工具调用失败：{tool_name}, 状态码：{response.status_code}, 响应：{response.text}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"MCP 工具调用异常：{tool_name}, 错误：{str(e)}"
            logger.error(error_msg)
            return False, error_msg


class LLMPlanner:
    """LLM 任务规划器 - 使用 Qwen 进行任务规划和工具选择"""
    
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY 环境变量未设置")
        self.mcp_client = MCPClient()
        self.available_tools: List[MCPTool] = []
    
    def initialize_tools(self) -> None:
        """初始化可用工具列表"""
        logger.info("初始化 MCP 工具列表...")
        self.available_tools = self.mcp_client.list_tools()
        tool_names = [t.name for t in self.available_tools]
        logger.info(f"可用工具：{tool_names}")
    
    def _build_tool_description(self) -> str:
        """构建工具描述文本用于 LLM 提示"""
        if not self.available_tools:
            self.initialize_tools()
        
        tool_descriptions = []
        for tool in self.available_tools:
            desc = f"- {tool.name}: {tool.description}"
            if tool.input_schema:
                params = json.dumps(tool.input_schema, ensure_ascii=False)
                desc += f"\n  参数：{params}"
            tool_descriptions.append(desc)
        
        return "\n".join(tool_descriptions) if tool_descriptions else "暂无可用工具"
    
    def plan_task(self, user_input: str, context: Optional[AgentContext] = None) -> TaskPlan:
        """
        使用 LLM 进行任务规划
        
        Args:
            user_input: 用户输入
            context: 可选的上下文对象
            
        Returns:
            TaskPlan: 任务规划结果
        """
        try:
            import requests
            
            logger.info(f"开始任务规划：{user_input}")
            
            if not self.available_tools:
                self.initialize_tools()
            
            tool_description = self._build_tool_description()
            
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

            user_prompt = f"用户输入：{user_input}\n\n请分析并生成任务规划："
            
            full_prompt = system_prompt.format(tool_description=tool_description) + "\n\n" + user_prompt
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "qwen-plus",
                "messages": [
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            }
            
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result and "output" in result and "text" in result["output"]:
                    llm_response = result["output"]["text"]
                    logger.info(f"LLM 响应：{llm_response}")
                    
                    try:
                        plan_data = json.loads(llm_response)
                        return self._create_task_plan(user_input, plan_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"解析 LLM 响应失败：{str(e)}")
                        return self._create_fallback_plan(user_input)
                else:
                    logger.warning("LLM 返回空响应")
                    return self._create_fallback_plan(user_input)
            else:
                logger.error(f"LLM 调用失败：状态码 {response.status_code}")
                return self._create_fallback_plan(user_input)
                
        except Exception as e:
            logger.error(f"任务规划异常：{str(e)}")
            return self._create_fallback_plan(user_input)
    
    def _create_task_plan(self, user_input: str, plan_data: Dict[str, Any]) -> TaskPlan:
        """根据 LLM 响应创建 TaskPlan 对象"""
        sub_tasks = plan_data.get("sub_tasks", [])
        tools_to_use = plan_data.get("tools_to_use", [])
        
        if not sub_tasks and tools_to_use:
            for tool_info in tools_to_use:
                sub_tasks.append({
                    "name": f"使用工具：{tool_info['name']}",
                    "description": tool_info.get("reason", ""),
                    "tool": tool_info["name"],
                    "parameters": tool_info.get("parameters", {})
                })
        
        task_plan = TaskPlan(
            original_query=user_input,
            sub_tasks=sub_tasks,
            total_steps=len(sub_tasks),
            status="pending",
            metadata={
                "need_tools": plan_data.get("need_tools", False),
                "tools_to_use": tools_to_use,
                "final_goal": plan_data.get("final_goal", user_input)
            }
        )
        
        logger.info(f"任务规划完成：{len(sub_tasks)} 个子任务")
        return task_plan
    
    def _create_fallback_plan(self, user_input: str) -> TaskPlan:
        """创建降级任务规划（当 LLM 不可用时）"""
        logger.warning("使用降级任务规划")
        
        task_plan = TaskPlan(
            original_query=user_input,
            sub_tasks=[
                {
                    "name": "处理用户请求",
                    "description": user_input,
                    "tool": None,
                    "parameters": {}
                }
            ],
            total_steps=1,
            status="pending",
            metadata={
                "need_tools": False,
                "tools_to_use": [],
                "final_goal": user_input,
                "fallback": True
            }
        )
        
        return task_plan
    
    def execute_plan(self, context: AgentContext) -> None:
        """
        执行任务规划
        
        Args:
            context: AgentContext 上下文对象
        """
        if not context.task_plan:
            logger.error("没有任务规划可执行")
            return
        
        task_plan = context.task_plan
        logger.info(f"开始执行任务规划：{task_plan.task_id}")
        
        while not task_plan.is_completed():
            next_task = task_plan.next_step()
            if next_task:
                logger.info(f"执行子任务：{next_task.get('name')}")
                
                tool_name = next_task.get("tool")
                parameters = next_task.get("parameters", {})
                
                if tool_name:
                    tool_exec = ToolExecution(
                        tool_name=tool_name,
                        tool_type="mcp",
                        parameters=parameters
                    )
                    
                    start_time = time.time()
                    success, result = self.mcp_client.call_tool(tool_name, parameters)
                    execution_time = time.time() - start_time
                    
                    if success:
                        tool_exec.mark_success(result, execution_time)
                    else:
                        tool_exec.mark_failed(result)
                    
                    context.add_tool_execution(tool_exec)
                else:
                    logger.info(f"子任务不需要工具：{next_task.get('name')}")
        
        task_plan.status = "completed"
        logger.info(f"任务规划执行完成：{task_plan.task_id}")
    
    def should_use_tool(self, user_input: str) -> Tuple[bool, str]:
        """
        判断是否需要使用工具
        
        Args:
            user_input: 用户输入
            
        Returns:
            Tuple[bool, str]: (是否需要工具，工具名称)
        """
        try:
            import requests
            
            if not self.available_tools:
                self.initialize_tools()
            
            tool_names = ", ".join([t.name for t in self.available_tools])
            
            system_prompt = f"""你是一个智能助手。判断用户输入是否需要使用外部工具。

可用工具：{tool_names}

如果需要使用工具，返回：YES|工具名称
如果不需要使用工具，返回：NO

只返回这一行，不要返回其他内容。"""

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "qwen-plus",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.0,
                "max_tokens": 50
            }
            
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result and "output" in result and "text" in result["output"]:
                    llm_response = result["output"]["text"].strip()
                    logger.info(f"工具判断结果：{llm_response}")
                    
                    if llm_response.startswith("YES"):
                        parts = llm_response.split("|")
                        tool_name = parts[1] if len(parts) > 1 else ""
                        return True, tool_name
                    else:
                        return False, ""
                else:
                    logger.warning("LLM 返回空响应")
                    return False, ""
            else:
                logger.error(f"LLM 调用失败：状态码 {response.status_code}")
                return False, ""
                
        except Exception as e:
            logger.error(f"工具判断异常：{str(e)}")
            return False, ""


def create_planner() -> LLMPlanner:
    """创建规划器的便捷函数"""
    return LLMPlanner()


def plan_and_execute(user_input: str, user_id: str = "default") -> AgentContext:
    """
    规划并执行的便捷函数
    
    Args:
        user_input: 用户输入
        user_id: 用户 ID
        
    Returns:
        AgentContext: 执行后的上下文
    """
    from src.core.context import create_context
    
    context = create_context(user_id)
    context.user_input = user_input
    context.start_execution()
    
    try:
        planner = create_planner()
        context.task_plan = planner.plan_task(user_input, context)
        planner.execute_plan(context)
        context.complete_execution()
    except Exception as e:
        context.fail_execution(str(e))
    
    return context

