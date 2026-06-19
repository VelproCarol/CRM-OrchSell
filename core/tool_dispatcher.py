"""
工具调度器模块
编排串行/并行工具执行顺序
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from loguru import logger

from config.settings import settings, Constants
from schemas.output_schema import TaskPlan, TaskLog


class ToolDispatcher:
    """
    工具调度器
    负责编排任务的串行和并行执行
    """
    
    def __init__(self):
        """初始化工具调度器"""
        self._tools: Dict[str, Any] = {}
        self._timeout = settings.TOOL_TIMEOUT
        logger.info("工具调度器初始化完成")
    
    def register_tool(self, tool_name: str, tool_instance: Any):
        """
        注册工具实例
        
        Args:
            tool_name: 工具名称
            tool_instance: 工具实例
        """
        self._tools[tool_name] = tool_instance
        logger.info(f"注册工具: {tool_name}")
    
    async def dispatch(
        self,
        tasks: List[TaskPlan],
        context: Optional[Dict[str, Any]] = None
    ) -> List[TaskLog]:
        """
        调度执行任务列表
        
        Args:
            tasks: 任务计划列表
            context: 执行上下文（包含前序任务结果）
            
        Returns:
            任务执行日志列表
        """
        logger.info(f"开始调度 {len(tasks)} 个任务")
        
        context = context or {}
        task_logs: List[TaskLog] = []
        
        # 按优先级分组
        priority_groups = self._group_by_priority(tasks)
        
        # 按优先级顺序执行
        for priority in sorted(priority_groups.keys()):
            group_tasks = priority_groups[priority]
            
            # 检查依赖是否满足
            ready_tasks = []
            for task in group_tasks:
                if self._check_dependencies(task, task_logs):
                    ready_tasks.append(task)
                else:
                    # 依赖未满足，记录失败日志
                    task_log = TaskLog(
                        task_id=task.task_id,
                        task_type=task.task_type,
                        tool_name=task.tool_name,
                        status=Constants.TASK_STATUS_FAILED,
                        start_time=datetime.now(),
                        error_message=f"依赖任务未完成: {task.dependencies}"
                    )
                    task_logs.append(task_log)
            
            # 并行执行同优先级任务
            if ready_tasks:
                parallel_logs = await self._execute_parallel(ready_tasks, context)
                task_logs.extend(parallel_logs)
                
                # 更新上下文
                for log in parallel_logs:
                    if log.status == Constants.TASK_STATUS_COMPLETED and log.output_result:
                        context[log.task_type] = log.output_result
        
        logger.info(f"任务调度完成，成功: {sum(1 for log in task_logs if log.status == Constants.TASK_STATUS_COMPLETED)}")
        return task_logs
    
    def _group_by_priority(self, tasks: List[TaskPlan]) -> Dict[int, List[TaskPlan]]:
        """
        按优先级分组任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            优先级分组字典
        """
        groups: Dict[int, List[TaskPlan]] = {}
        for task in tasks:
            priority = task.priority
            if priority not in groups:
                groups[priority] = []
            groups[priority].append(task)
        return groups
    
    def _check_dependencies(
        self,
        task: TaskPlan,
        completed_logs: List[TaskLog]
    ) -> bool:
        """
        检查任务依赖是否满足
        
        Args:
            task: 待检查任务
            completed_logs: 已完成的任务日志
            
        Returns:
            是否满足依赖
        """
        if not task.dependencies:
            return True
        
        completed_types = {
            log.task_type for log in completed_logs
            if log.status == Constants.TASK_STATUS_COMPLETED
        }
        
        return all(dep in completed_types for dep in task.dependencies)
    
    async def _execute_parallel(
        self,
        tasks: List[TaskPlan],
        context: Dict[str, Any]
    ) -> List[TaskLog]:
        """
        并行执行任务
        
        Args:
            tasks: 任务列表
            context: 执行上下文
            
        Returns:
            任务日志列表
        """
        logger.info(f"并行执行 {len(tasks)} 个任务")
        
        # 创建并行任务
        coroutines = [
            self._execute_single(task, context)
            for task in tasks
        ]
        
        # 并行执行
        task_logs = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # 处理异常
        results = []
        for i, log in enumerate(task_logs):
            if isinstance(log, Exception):
                # 异常转换为失败日志
                task = tasks[i]
                error_log = TaskLog(
                    task_id=task.task_id,
                    task_type=task.task_type,
                    tool_name=task.tool_name,
                    status=Constants.TASK_STATUS_FAILED,
                    start_time=datetime.now(),
                    error_message=f"执行异常: {str(log)}"
                )
                results.append(error_log)
            else:
                results.append(log)
        
        return results
    
    async def _execute_single(
        self,
        task: TaskPlan,
        context: Dict[str, Any]
    ) -> TaskLog:
        """
        执行单个任务
        
        Args:
            task: 任务计划
            context: 执行上下文
            
        Returns:
            任务日志
        """
        start_time = datetime.now()
        logger.info(f"执行任务: {task.task_id} - {task.task_type}")
        
        task_log = TaskLog(
            task_id=task.task_id,
            task_type=task.task_type,
            tool_name=task.tool_name,
            status=Constants.TASK_STATUS_RUNNING,
            start_time=start_time,
            input_params=task.parameters
        )
        
        try:
            # 获取工具实例
            tool = self._tools.get(task.tool_name)
            if not tool:
                raise ValueError(f"工具未注册: {task.tool_name}")
            
            # 合并参数和上下文
            params = {**task.parameters, **context}
            
            # 执行工具（带超时）
            result = await asyncio.wait_for(
                tool.execute(**params),
                timeout=self._timeout
            )
            
            # 记录成功日志
            end_time = datetime.now()
            task_log.status = Constants.TASK_STATUS_COMPLETED
            task_log.end_time = end_time
            task_log.duration_ms = int((end_time - start_time).total_seconds() * 1000)
            task_log.output_result = result
            
            logger.info(f"任务完成: {task.task_id}, 耗时: {task_log.duration_ms}ms")
            
        except asyncio.TimeoutError:
            # 超时
            end_time = datetime.now()
            task_log.status = Constants.TASK_STATUS_FAILED
            task_log.end_time = end_time
            task_log.duration_ms = int((end_time - start_time).total_seconds() * 1000)
            task_log.error_message = f"任务执行超时（{self._timeout}秒）"
            logger.error(f"任务超时: {task.task_id}")
            
        except Exception as e:
            # 异常
            end_time = datetime.now()
            task_log.status = Constants.TASK_STATUS_FAILED
            task_log.end_time = end_time
            task_log.duration_ms = int((end_time - start_time).total_seconds() * 1000)
            task_log.error_message = f"任务执行失败: {str(e)}"
            logger.error(f"任务失败: {task.task_id}, 错误: {str(e)}")
        
        return task_log
    
    def get_registered_tools(self) -> List[str]:
        """
        获取已注册的工具列表
        
        Returns:
            工具名称列表
        """
        return list(self._tools.keys())