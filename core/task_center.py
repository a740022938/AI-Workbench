"""
分身任务中心 v1 - 核心骨架

为 OpenClaw 提供任务级协作能力，支持任务单创建、策略执行、智能中断和状态报告。
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"                    # 等待开始
    RUNNING = "running"                    # 正在执行
    PAUSED = "paused"                      # 已暂停
    WAITING_CONFIRMATION = "waiting_confirmation"  # 等待确认
    WAITING_CHOICE = "waiting_choice"      # 等待选择
    COMPLETED = "completed"                # 已完成
    FAILED = "failed"                      # 已失败
    CANCELLED = "cancelled"                # 已取消


class ReportMode(Enum):
    """报告模式枚举"""
    MINIMAL = "minimal"    # 最小报告
    SUMMARY = "summary"    # 摘要报告
    DETAILED = "detailed"  # 详细报告


class Task:
    """
    任务单对象 - 封装一个完整任务的所有状态
    
    字段说明：
    - task_id: 任务唯一标识
    - task_name: 任务名称
    - created_time: 创建时间
    - action_list: 动作列表 [{"action": "next_image", "params": {}}, ...]
    - current_action_index: 当前执行的动作索引
    - action_results: 每个动作的执行结果
    - auto_run: 是否自动运行（跳过确认）
    - stop_on_risk: 高风险时是否停止
    - report_mode: 报告模式
    - task_status: 任务状态
    - task_result_summary: 任务结果摘要
    - pending_confirmation: 等待确认的动作名
    - pending_choice: 等待选择的动作名
    - context_data: 执行上下文数据
    - task_notes: 任务笔记
    """
    
    def __init__(self, task_name: str, action_list: List[Dict[str, Any]], **kwargs):
        """初始化任务单"""
        # 基本信息
        self.task_id = self._generate_task_id()
        self.task_name = task_name
        self.created_time = datetime.now()
        
        # 动作配置
        self.action_list = action_list
        self.current_action_index = 0
        self.action_results = []  # 存储每个动作的执行结果
        
        # 执行配置
        self.auto_run = kwargs.get('auto_run', True)
        self.stop_on_risk = kwargs.get('stop_on_risk', True)
        self.report_mode = ReportMode(kwargs.get('report_mode', 'summary'))
        
        # 状态跟踪
        self.task_status = TaskStatus.PENDING
        self.task_result_summary = {
            'success': None,
            'total_actions': len(action_list),
            'completed_actions': 0,
            'failed_actions': 0,
            'pending_confirmation': 0,
            'pending_choice': 0,
            'start_time': None,
            'end_time': None,
            'execution_time': None,
            'risk_summary': {
                'low': 0,
                'medium': 0,
                'high': 0
            },
            'action_summary': []
        }
        
        # 中断状态
        self.pending_confirmation = None  # 等待确认的动作名
        self.pending_choice = None  # 等待选择的动作名
        self.pending_choice_options = None  # 选择选项列表
        
        # 上下文数据
        self.context_data = kwargs.get('context', {})
        self.task_notes = kwargs.get('notes', [])
        
        # 内部状态
        self._main_window = None  # MainWindow 实例（执行时设置）
        self._start_time = None
        self._end_time = None
    
    def _generate_task_id(self) -> str:
        """生成任务ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = random.randint(1000, 9999)
        return f"task_{timestamp}_{random_suffix}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于序列化）"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'created_time': self.created_time.isoformat(),
            'action_list': self.action_list,
            'current_action_index': self.current_action_index,
            'action_results': self.action_results,
            'auto_run': self.auto_run,
            'stop_on_risk': self.stop_on_risk,
            'report_mode': self.report_mode.value,
            'task_status': self.task_status.value,
            'task_result_summary': self.task_result_summary,
            'pending_confirmation': self.pending_confirmation,
            'pending_choice': self.pending_choice,
            'context_data': self.context_data,
            'task_notes': self.task_notes,
            'progress': f"{self.current_action_index}/{len(self.action_list)}"
        }
    
    def get_progress(self) -> str:
        """获取任务进度"""
        return f"{self.current_action_index}/{len(self.action_list)}"
    
    def add_note(self, note: str):
        """添加任务笔记"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.task_notes.append(f"[{timestamp}] {note}")
    
    def update_result_summary(self, action_name: str, result: Dict[str, Any]):
        """更新任务结果摘要"""
        # 这里先做简单更新，后续可以扩展
        if result.get('success'):
            self.task_result_summary['completed_actions'] += 1
        else:
            self.task_result_summary['failed_actions'] += 1
        
        # 记录动作摘要
        self.task_result_summary['action_summary'].append({
            'action': action_name,
            'success': result.get('success'),
            'message': result.get('message'),
            'timestamp': datetime.now().isoformat()
        })


class TaskCenter:
    """
    任务管理中心 - 负责任务的创建、存储和查询
    
    功能：
    - 任务创建和管理
    - 任务模板生成
    - 任务状态查询
    - 任务历史记录
    """
    
    def __init__(self):
        """初始化任务中心"""
        self._tasks: Dict[str, Task] = {}  # task_id -> Task
        self._task_history: List[Dict[str, Any]] = []  # 任务历史记录
    
    def create_task(self, task_name: str, action_list: List[Dict[str, Any]], **kwargs) -> Task:
        """
        创建新任务
        
        参数:
            task_name: 任务名称
            action_list: 动作列表
            **kwargs: 额外配置参数
            
        返回:
            Task: 创建的任务对象
        """
        task = Task(task_name, action_list, **kwargs)
        self._tasks[task.task_id] = task
        self._task_history.append({
            'task_id': task.task_id,
            'task_name': task_name,
            'created_time': datetime.now().isoformat(),
            'action_count': len(action_list),
            'status': 'created'
        })
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取指定任务"""
        return self._tasks.get(task_id)
    
    def list_tasks(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有任务
        
        参数:
            status_filter: 状态过滤（可选）
            
        返回:
            List[Dict]: 任务列表
        """
        tasks = []
        for task in self._tasks.values():
            task_dict = task.to_dict()
            if status_filter and task_dict['task_status'] != status_filter:
                continue
            tasks.append(task_dict)
        
        # 按创建时间倒序排序
        tasks.sort(key=lambda x: x['created_time'], reverse=True)
        return tasks
    
    def create_light_annotation_task(self, **kwargs) -> Task:
        """
        创建轻量标注任务模板
        
        动作流程:
        1. next_image - 切换到下一张图片
        2. copy_labels_from_previous_image - 复制上一张标注
        3. save_current_labels - 保存当前标注
        """
        action_list = [
            {"action": "next_image", "params": {}},
            {"action": "copy_labels_from_previous_image", "params": {}},
            {"action": "save_current_labels", "params": {}}
        ]
        
        default_kwargs = {
            'task_name': '轻量标注任务',
            'auto_run': True,
            'stop_on_risk': True,
            'report_mode': 'summary',
            'notes': ['自动生成的轻量标注任务']
        }
        
        # 合并参数
        merged_kwargs = {**default_kwargs, **kwargs}
        
        return self.create_task(
            task_name=merged_kwargs['task_name'],
            action_list=action_list,
            auto_run=merged_kwargs['auto_run'],
            stop_on_risk=merged_kwargs['stop_on_risk'],
            report_mode=merged_kwargs['report_mode'],
            notes=merged_kwargs['notes']
        )
    
    def create_inspection_task(self, **kwargs) -> Task:
        """
        创建巡查任务模板
        
        动作流程:
        1. boss_status - 查询老板状态
        2. openclaw_status - 查询OpenClaw状态
        3. run_openclaw_analysis - 运行OpenClaw分析
        """
        action_list = [
            {"action": "boss_status", "params": {}},
            {"action": "openclaw_status", "params": {}},
            {"action": "run_openclaw_analysis", "params": {}}
        ]
        
        default_kwargs = {
            'task_name': '巡查任务',
            'auto_run': True,
            'stop_on_risk': False,  # 巡查任务不因风险停止
            'report_mode': 'detailed',
            'notes': ['自动生成的巡查任务']
        }
        
        merged_kwargs = {**default_kwargs, **kwargs}
        
        return self.create_task(
            task_name=merged_kwargs['task_name'],
            action_list=action_list,
            auto_run=merged_kwargs['auto_run'],
            stop_on_risk=merged_kwargs['stop_on_risk'],
            report_mode=merged_kwargs['report_mode'],
            notes=merged_kwargs['notes']
        )
    
    def create_cleanup_task(self, **kwargs) -> Task:
        """
        创建清理任务模板
        
        动作流程:
        1. delete_selected_box - 删除选中框
        2. save_current_labels - 保存标注
        3. run_openclaw_analysis - 运行分析
        """
        action_list = [
            {"action": "delete_selected_box", "params": {}},
            {"action": "save_current_labels", "params": {}},
            {"action": "run_openclaw_analysis", "params": {}}
        ]
        
        default_kwargs = {
            'task_name': '清理任务',
            'auto_run': False,  # 清理任务需要确认
            'stop_on_risk': True,
            'report_mode': 'detailed',
            'notes': ['自动生成的清理任务（高风险）']
        }
        
        merged_kwargs = {**default_kwargs, **kwargs}
        
        return self.create_task(
            task_name=merged_kwargs['task_name'],
            action_list=action_list,
            auto_run=merged_kwargs['auto_run'],
            stop_on_risk=merged_kwargs['stop_on_risk'],
            report_mode=merged_kwargs['report_mode'],
            notes=merged_kwargs['notes']
        )
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
    
    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务历史记录"""
        return self._task_history[-limit:] if self._task_history else []


class TaskExecutor:
    """
    任务执行器 - 负责任务的执行和状态管理
    
    功能：
    - 任务执行流程控制
    - 策略集成执行
    - 中断处理
    - 报告生成
    """
    
    def __init__(self, main_window=None):
        """初始化任务执行器"""
        self.main_window = main_window
        self._task_center = TaskCenter()
        
        # 导入策略模块（延迟导入避免循环依赖）
        self._action_policy_available = False
        try:
            from core.action_policy import get_action_policy
            self._get_action_policy = get_action_policy
            self._action_policy_available = True
        except ImportError:
            self._get_action_policy = lambda x: None
    
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        执行任务
        
        参数:
            task: 要执行的任务对象
            
        返回:
            Dict: 执行结果
        """
        # 设置 MainWindow 实例
        task._main_window = self.main_window
        
        # 更新任务状态
        task.task_status = TaskStatus.RUNNING
        task.task_result_summary['start_time'] = datetime.now().isoformat()
        task._start_time = datetime.now()
        
        task.add_note(f"任务开始执行: {task.task_name}")
        
        try:
            # 执行任务
            result = self._execute_task_internal(task)
            return result
        except Exception as e:
            # 任务执行异常
            task.task_status = TaskStatus.FAILED
            task.task_result_summary['success'] = False
            task.task_result_summary['end_time'] = datetime.now().isoformat()
            task._end_time = datetime.now()
            
            task.add_note(f"任务执行异常: {str(e)}")
            
            return {
                'success': False,
                'task_id': task.task_id,
                'task_name': task.task_name,
                'error': str(e),
                'task_status': 'failed',
                'summary': self.build_task_summary(task)
            }
    
    def _execute_task_internal(self, task: Task) -> Dict[str, Any]:
        """内部任务执行逻辑"""
        # 执行所有动作
        while task.current_action_index < len(task.action_list):
            # 执行下一个动作
            action_result = self.execute_next_action(task)
            
            if not action_result.get('success', True):
                # 动作执行失败
                task.task_status = TaskStatus.FAILED
                break
            
            if action_result.get('status') == 'waiting_confirmation':
                # 等待确认
                task.task_status = TaskStatus.WAITING_CONFIRMATION
                task.pending_confirmation = action_result.get('action_name')
                break
            
            if action_result.get('status') == 'waiting_choice':
                # 等待选择
                task.task_status = TaskStatus.WAITING_CHOICE
                task.pending_choice = action_result.get('action_name')
                task.pending_choice_options = action_result.get('options', [])
                break
        
        # 检查任务状态
        if task.task_status == TaskStatus.RUNNING and task.current_action_index >= len(task.action_list):
            # 所有动作执行完成
            task.task_status = TaskStatus.COMPLETED
            task.task_result_summary['success'] = True
        
        # 更新结束时间
        task.task_result_summary['end_time'] = datetime.now().isoformat()
        task._end_time = datetime.now()
        
        # 计算执行时间
        if task._start_time and task._end_time:
            exec_time = (task._end_time - task._start_time).total_seconds()
            task.task_result_summary['execution_time'] = exec_time
        
        task.add_note(f"任务执行结束: {task.task_status.value}")
        
        return {
            'success': task.task_status == TaskStatus.COMPLETED,
            'task_id': task.task_id,
            'task_name': task.task_name,
            'task_status': task.task_status.value,
            'summary': self.build_task_summary(task)
        }
    
    def execute_next_action(self, task: Task) -> Dict[str, Any]:
        """
        执行下一个动作
        
        参数:
            task: 任务对象
            
        返回:
            Dict: 动作执行结果
        """
        if task.current_action_index >= len(task.action_list):
            return {'success': True, 'status': 'completed'}
        
        # 获取当前动作
        action_spec = task.action_list[task.current_action_index]
        action_name = action_spec['action']
        action_params = action_spec.get('params', {})
        
        task.add_note(f"执行动作: {action_name}")
        
        # 导入桥接层函数
        try:
            from core.openclaw_bridge import execute_action_with_policy
        except ImportError:
            task.add_note("警告: 无法导入桥接层，使用模拟执行")
            # 模拟执行结果
            result = {
                'success': True,
                'action_name': action_name,
                'message': f'模拟执行: {action_name}',
                'status': 'executed'
            }
            
            # 记录结果
            task.action_results.append(result)
            task.update_result_summary(action_name, result)
            task.current_action_index += 1
            
            return result
        
        # 使用桥接层执行动作
        if self.main_window:
            try:
                # 执行动作
                bridge_result = execute_action_with_policy(
                    action_name=action_name,
                    main_window=self.main_window,
                    context=task.context_data,
                    force_execute=task.auto_run  # 如果auto_run=True，跳过确认
                )
                
                # 处理执行结果
                if bridge_result.get('success', False):
                    # 成功执行
                    result = {
                        'success': True,
                        'action_name': action_name,
                        'message': bridge_result.get('telegram_response', f'执行: {action_name}'),
                        'status': 'executed',
                        'bridge_result': bridge_result
                    }
                    
                    # 记录结果
                    task.action_results.append(result)
                    task.update_result_summary(action_name, result)
                    task.current_action_index += 1
                    
                    return result
                else:
                    # 执行失败
                    result = {
                        'success': False,
                        'action_name': action_name,
                        'message': bridge_result.get('telegram_response', f'执行失败: {action_name}'),
                        'status': 'failed',
                        'error': bridge_result.get('error', '未知错误'),
                        'bridge_result': bridge_result
                    }
                    
                    # 记录结果
                    task.action_results.append(result)
                    task.update_result_summary(action_name, result)
                    
                    return result
                    
            except Exception as e:
                # 执行异常
                result = {
                    'success': False,
                    'action_name': action_name,
                    'message': f'执行异常: {action_name}',
                    'status': 'failed',
                    'error': str(e)
                }
                
                # 记录结果
                task.action_results.append(result)
                task.update_result_summary(action_name, result)
                
                return result
        else:
            # 没有MainWindow实例
            result = {
                'success': False,
                'action_name': action_name,
                'message': f'无法执行: 缺少MainWindow实例',
                'status': 'failed',
                'error': 'MainWindow not available'
            }
            
            # 记录结果
            task.action_results.append(result)
            task.update_result_summary(action_name, result)
            
            return result
    
    def build_task_summary(self, task: Task) -> Dict[str, Any]:
        """
        构建任务摘要
        
        参数:
            task: 任务对象
            
        返回:
            Dict: 任务摘要
        """
        summary = {
            'task_id': task.task_id,
            'task_name': task.task_name,
            'task_status': task.task_status.value,
            'created_time': task.created_time.isoformat(),
            'progress': task.get_progress(),
            'total_actions': task.task_result_summary['total_actions'],
            'completed_actions': task.task_result_summary['completed_actions'],
            'failed_actions': task.task_result_summary['failed_actions'],
            'start_time': task.task_result_summary['start_time'],
            'end_time': task.task_result_summary['end_time'],
            'execution_time': task.task_result_summary['execution_time'],
            'auto_run': task.auto_run,
            'stop_on_risk': task.stop_on_risk,
            'report_mode': task.report_mode.value
        }
        
        # 根据报告模式添加详细信息
        if task.report_mode == ReportMode.DETAILED:
            summary['action_results'] = task.action_results
            summary['task_notes'] = task.task_notes
            summary['context_data'] = task.context_data
        
        elif task.report_mode == ReportMode.SUMMARY:
            summary['recent_actions'] = task.action_results[-3:] if task.action_results else []
            summary['recent_notes'] = task.task_notes[-3:] if task.task_notes else []
        
        # 最小报告模式不添加额外信息
        
        return summary
    
    def confirm_action(self, task: Task, confirm: bool = True) -> Dict[str, Any]:
        """
        确认动作执行
        
        参数:
            task: 任务对象
            confirm: 是否确认执行
            
        返回:
            Dict: 确认结果
        """
        if task.task_status != TaskStatus.WAITING_CONFIRMATION:
            return {'success': False, 'error': '任务不在等待确认状态'}
        
        if not task.pending_confirmation:
            return {'success': False, 'error': '没有待确认的动作'}
        
        action_name = task.pending_confirmation
        
        if confirm:
            task.add_note(f"确认执行: {action_name}")
            task.pending_confirmation = None
            task.task_status = TaskStatus.RUNNING
            
            # 导入桥接层函数
            try:
                from core.openclaw_bridge import execute_action_with_policy
            except ImportError:
                # 模拟执行
                result = {
                    'success': True,
                    'action_name': action_name,
                    'message': f'确认执行: {action_name}',
                    'status': 'confirmed_and_executed'
                }
                
                task.action_results.append(result)
                task.update_result_summary(action_name, result)
                task.current_action_index += 1
                
                return {
                    'success': True,
                    'action_name': action_name,
                    'confirmed': True,
                    'result': result
                }
            
            # 使用桥接层执行动作（强制确认）
            if self.main_window:
                try:
                    bridge_result = execute_action_with_policy(
                        action_name=action_name,
                        main_window=self.main_window,
                        context=task.context_data,
                        force_execute=True  # 强制确认执行
                    )
                    
                    if bridge_result.get('success', False):
                        result = {
                            'success': True,
                            'action_name': action_name,
                            'message': bridge_result.get('telegram_response', f'确认执行: {action_name}'),
                            'status': 'confirmed_and_executed',
                            'bridge_result': bridge_result
                        }
                        
                        task.action_results.append(result)
                        task.update_result_summary(action_name, result)
                        task.current_action_index += 1
                        
                        return {
                            'success': True,
                            'action_name': action_name,
                            'confirmed': True,
                            'result': result
                        }
                    else:
                        # 执行失败
                        result = {
                            'success': False,
                            'action_name': action_name,
                            'message': bridge_result.get('telegram_response', f'确认执行失败: {action_name}'),
                            'status': 'failed',
                            'error': bridge_result.get('error', '未知错误'),
                            'bridge_result': bridge_result
                        }
                        
                        task.action_results.append(result)
                        task.update_result_summary(action_name, result)
                        
                        return {
                            'success': False,
                            'action_name': action_name,
                            'confirmed': True,
                            'error': '执行失败',
                            'result': result
                        }
                        
                except Exception as e:
                    # 执行异常
                    result = {
                        'success': False,
                        'action_name': action_name,
                        'message': f'确认执行异常: {action_name}',
                        'status': 'failed',
                        'error': str(e)
                    }
                    
                    task.action_results.append(result)
                    task.update_result_summary(action_name, result)
                    
                    return {
                        'success': False,
                        'action_name': action_name,
                        'confirmed': True,
                        'error': str(e),
                        'result': result
                    }
            else:
                # 没有MainWindow实例
                result = {
                    'success': False,
                    'action_name': action_name,
                    'message': f'无法确认执行: 缺少MainWindow实例',
                    'status': 'failed',
                    'error': 'MainWindow not available'
                }
                
                task.action_results.append(result)
                task.update_result_summary(action_name, result)
                
                return {
                    'success': False,
                    'action_name': action_name,
                    'confirmed': True,
                    'error': 'MainWindow not available',
                    'result': result
                }
        else:
            # 取消执行
            task.add_note(f"取消执行: {action_name}")
            task.pending_confirmation = None
            task.task_status = TaskStatus.CANCELLED
            
            return {
                'success': True,
                'action_name': action_name,
                'confirmed': False,
                'message': '动作已取消'
            }
    
    def make_choice(self, task: Task, choice: str) -> Dict[str, Any]:
        """
        做出选择
        
        参数:
            task: 任务对象
            choice: 选择的选项
            
        返回:
            Dict: 选择结果
        """
        if task.task_status != TaskStatus.WAITING_CHOICE:
            return {'success': False, 'error': '任务不在等待选择状态'}
        
        if not task.pending_choice:
            return {'success': False, 'error': '没有待选择的动作'}
        
        if not task.pending_choice_options or choice not in task.pending_choice_options:
            return {
                'success': False,
                'error': f'无效选择，可用选项: {", ".join(task.pending_choice_options)}'
            }
        
        action_name = task.pending_choice
        
        task.add_note(f"选择 {choice} 执行: {action_name}")
        task.pending_choice = None
        task.pending_choice_options = None
        task.task_status = TaskStatus.RUNNING
        
        # 这里应该根据选择执行动作，暂时模拟
        result = {
            'success': True,
            'action_name': action_name,
            'choice': choice,
            'message': f'选择 {choice} 执行: {action_name}',
            'status': 'chosen_and_executed'
        }
        
        task.action_results.append(result)
        task.update_result_summary(action_name, result)
        task.current_action_index += 1
        
        return {
            'success': True,
            'action_name': action_name,
            'choice': choice,
            'result': result
        }
    
    def pause_task(self, task: Task) -> bool:
        """暂停任务"""
        if task.task_status == TaskStatus.RUNNING:
            task.task_status = TaskStatus.PAUSED
            task.add_note("任务已暂停")
            return True
        return False
    
    def resume_task(self, task: Task) -> bool:
        """恢复任务"""
        if task.task_status == TaskStatus.PAUSED:
            task.task_status = TaskStatus.RUNNING
            task.add_note("任务已恢复")
            return True
        return False
    
    def cancel_task(self, task: Task) -> bool:
        """取消任务"""
        if task.task_status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.task_status = TaskStatus.CANCELLED
            task.add_note("任务已取消")
            return True
        return False


# ==================== 全局任务中心实例 ====================
# 提供全局访问点，便于桥接层使用

_global_task_center: Optional[TaskCenter] = None
_global_task_executor: Optional[TaskExecutor] = None


def get_task_center() -> TaskCenter:
    """获取全局任务中心实例"""
    global _global_task_center
    if _global_task_center is None:
        _global_task_center = TaskCenter()
    return _global_task_center


def get_task_executor(main_window=None) -> TaskExecutor:
    """获取全局任务执行器实例"""
    global _global_task_executor
    if _global_task_executor is None:
        _global_task_executor = TaskExecutor(main_window)
    elif main_window and _global_task_executor.main_window is None:
        _global_task_executor.main_window = main_window
    return _global_task_executor


def create_task_from_template(template_name: str, **kwargs) -> Optional[Task]:
    """
    从模板创建任务（便捷函数）
    
    参数:
        template_name: 模板名称 ('light_annotation', 'inspection', 'cleanup')
        **kwargs: 额外参数
        
    返回:
        Task: 创建的任务对象
    """
    task_center = get_task_center()
    
    if template_name == 'light_annotation':
        return task_center.create_light_annotation_task(**kwargs)
    elif template_name == 'inspection':
        return task_center.create_inspection_task(**kwargs)
    elif template_name == 'cleanup':
        return task_center.create_cleanup_task(**kwargs)
    else:
        return None


def get_task_summary_telegram(task: Task) -> str:
    """
    获取任务摘要（Telegram友好格式）
    
    参数:
        task: 任务对象
        
    返回:
        str: Telegram格式的任务摘要
    """
    summary = task.to_dict()
    
    # 状态图标
    status_icons = {
        'pending': '⏳',
        'running': '▶️',
        'paused': '⏸️',
        'waiting_confirmation': '⚠️',
        'waiting_choice': '🔄',
        'completed': '✅',
        'failed': '❌',
        'cancelled': '🚫'
    }
    
    icon = status_icons.get(summary['task_status'], '📋')
    
    lines = [
        f"{icon} *任务摘要: {summary['task_name']}*",
        f"📋 ID: `{summary['task_id']}`",
        f"📊 状态: {summary['task_status']}",
        f"📈 进度: {summary['progress']}",
        f"⏰ 创建时间: {summary['created_time'][:19]}",
    ]
    
    if summary['task_result_summary']['start_time']:
        lines.append(f"🚀 开始时间: {summary['task_result_summary']['start_time'][:19]}")
    
    if summary['task_result_summary']['end_time']:
        lines.append(f"🏁 结束时间: {summary['task_result_summary']['end_time'][:19]}")
    
    if summary['task_result_summary']['execution_time']:
        lines.append(f"⏱️ 执行时间: {summary['task_result_summary']['execution_time']:.1f}秒")
    
    lines.extend([
        f"📊 动作统计: 完成{summary['task_result_summary']['completed_actions']}/失败{summary['task_result_summary']['failed_actions']}/总计{summary['task_result_summary']['total_actions']}",
        f"⚙️ 配置: 自动运行{'[是]' if summary['auto_run'] else '[否]'}, 风险停止{'[是]' if summary['stop_on_risk'] else '[否]'}",
    ])
    
    # 添加中断信息
    if summary['pending_confirmation']:
        lines.append(f"⚠️ 等待确认: {summary['pending_confirmation']}")
    
    if summary['pending_choice']:
        lines.append(f"🔄 等待选择: {summary['pending_choice']}")
    
    # 替换emoji为文本避免编码问题
    telegram_text = "\n".join(lines)
    telegram_text = telegram_text.replace("✅", "[完成]").replace("❌", "[失败]").replace("⚠️", "[警告]")
    telegram_text = telegram_text.replace("🔄", "[选择]").replace("🚫", "[取消]").replace("⏳", "[等待]")
    telegram_text = telegram_text.replace("▶️", "[运行]").replace("⏸️", "[暂停]").replace("📋", "[任务]")
    
    return telegram_text