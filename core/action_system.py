#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
action_system.py - AI协作操作系统核心模块

功能：
1. 动作词典定义
2. 动作注册表管理
3. 前置条件检查
4. 状态快照生成
5. 统一命令入口
6. 动作执行回执
"""

import json
import inspect
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field, asdict
import datetime


# ====================== 基础数据结构 ======================

class ActionCategory(Enum):
    """动作类别"""
    NAVIGATION = "图片导航"
    BOX_SELECTION = "选框控制"
    BOX_EDIT = "框编辑"
    BOX_ANALYSIS = "框分析"
    CLASS_MANAGEMENT = "类别管理"
    DATA_HEALTH = "数据健康"
    TRAINING = "训练相关"
    CLOSED_LOOP = "闭环修正"
    SYSTEM = "系统操作"
    
    @classmethod
    def from_string(cls, value: str):
        for category in cls:
            if category.value == value:
                return category
        return cls.SYSTEM


@dataclass
class ActionDefinition:
    """动作定义"""
    # 基础信息
    action_id: str
    display_name: str
    description: str
    category: ActionCategory
    
    # 执行信息
    handler: Optional[Callable] = None
    handler_module: str = ""
    handler_function: str = ""
    
    # 参数信息
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    required_parameters: List[str] = field(default_factory=list)
    optional_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 前置条件
    preconditions: List[str] = field(default_factory=list)
    min_box_count: int = 0  # 需要的最小框数
    needs_selected_box: bool = False  # 是否需要选中框
    needs_current_image: bool = True  # 是否需要当前图片
    needs_class_list: bool = False  # 是否需要类别列表
    
    # 状态影响
    changes_state: bool = True  # 是否改变状态
    changes_image: bool = False  # 是否改变当前图片
    changes_boxes: bool = False  # 是否改变框数据
    
    # 安全限制
    risk_level: int = 1  # 风险等级 1-5
    requires_confirmation: bool = False  # 是否需要确认
    confirmation_message: str = ""
    
    # AI相关
    ai_suggestable: bool = True  # AI是否可建议此动作
    ai_confidence_threshold: float = 0.7  # AI建议置信度阈值
    
    # 元数据
    enabled: bool = True
    created_time: str = ""
    updated_time: str = ""
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['category'] = self.category.value
        
        # 处理函数（不序列化）
        if 'handler' in data:
            data.pop('handler')
        
        return data
    
    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """验证参数"""
        # 检查必需参数
        for param_name in self.required_parameters:
            if param_name not in params:
                return False, f"缺少必需参数: {param_name}"
        
        # 检查参数类型（简化版）
        for param_name, param_value in params.items():
            if param_name in self.parameters:
                param_def = self.parameters[param_name]
                expected_type = param_def.get('type', str)
                
                # 简单类型检查
                if expected_type == int and not isinstance(param_value, int):
                    try:
                        int(param_value)
                    except (ValueError, TypeError):
                        return False, f"参数 {param_name} 应为整数类型"
                
                if expected_type == float and not isinstance(param_value, (int, float)):
                    try:
                        float(param_value)
                    except (ValueError, TypeError):
                        return False, f"参数 {param_name} 应为数值类型"
        
        return True, "参数验证通过"


@dataclass
class StateSnapshot:
    """状态快照"""
    snapshot_id: str
    timestamp: str
    
    # 图片状态
    current_image_name: str = ""
    current_image_index: int = -1
    total_image_count: int = 0
    has_current_image: bool = False
    image_directory: str = ""
    label_directory: str = ""
    
    # 框状态
    box_count: int = 0
    has_selected_box: bool = False
    selected_box_index: int = -1
    selected_box_class: str = ""
    selected_box_confidence: float = 0.0
    
    # 类别状态
    class_list: List[str] = field(default_factory=list)
    class_count: int = 0
    current_class_name: str = ""
    
    # 系统状态
    has_unsaved_changes: bool = False
    auto_save_enabled: bool = False
    project_loaded: bool = False
    
    # 模块状态
    data_health_available: bool = False
    training_center_available: bool = False
    closed_loop_available: bool = False
    dataset_export_available: bool = False
    
    # 动作状态
    available_actions: List[str] = field(default_factory=list)
    enabled_action_count: int = 0
    recently_executed_actions: List[str] = field(default_factory=list)
    
    # AI协作状态
    ai_enabled: bool = False
    ai_confidence: float = 0.0
    last_ai_suggestion_time: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def get_summary_text(self) -> str:
        """获取文本摘要"""
        lines = []
        lines.append("=" * 60)
        lines.append("AI协作操作系统 - 状态快照")
        lines.append("=" * 60)
        lines.append(f"快照ID: {self.snapshot_id}")
        lines.append(f"时间戳: {self.timestamp}")
        lines.append("")
        
        lines.append("【图片状态】")
        if self.has_current_image:
            lines.append(f"  当前图片: {self.current_image_name}")
            lines.append(f"  位置: {self.current_image_index + 1}/{self.total_image_count}")
        else:
            lines.append("  无当前图片")
        lines.append("")
        
        lines.append("【标注状态】")
        lines.append(f"  标注框数量: {self.box_count}")
        if self.has_selected_box:
            lines.append(f"  选中框索引: {self.selected_box_index}")
            lines.append(f"  选中框类别: {self.selected_box_class}")
        else:
            lines.append("  无选中框")
        lines.append("")
        
        lines.append("【类别状态】")
        lines.append(f"  类别数量: {self.class_count}")
        if self.current_class_name:
            lines.append(f"  当前类别: {self.current_class_name}")
        lines.append("")
        
        lines.append("【系统状态】")
        lines.append(f"  项目已加载: {'是' if self.project_loaded else '否'}")
        lines.append(f"  有未保存更改: {'是' if self.has_unsaved_changes else '否'}")
        lines.append(f"  自动保存: {'启用' if self.auto_save_enabled else '禁用'}")
        lines.append("")
        
        lines.append("【模块状态】")
        lines.append(f"  数据健康检查: {'可用' if self.data_health_available else '不可用'}")
        lines.append(f"  训练中心: {'可用' if self.training_center_available else '不可用'}")
        lines.append(f"  闭环修正中心: {'可用' if self.closed_loop_available else '不可用'}")
        lines.append(f"  数据集导出: {'可用' if self.dataset_export_available else '不可用'}")
        lines.append("")
        
        lines.append("【动作状态】")
        lines.append(f"  可用动作数: {self.enabled_action_count}")
        if self.available_actions:
            lines.append(f"  最近执行动作: {', '.join(self.recently_executed_actions[:3])}")
        lines.append("")
        
        lines.append("【AI协作状态】")
        lines.append(f"  AI启用: {'是' if self.ai_enabled else '否'}")
        if self.ai_enabled:
            lines.append(f"  AI置信度: {self.ai_confidence:.2f}")
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


@dataclass
class ActionReceipt:
    """动作执行回执"""
    receipt_id: str
    action_id: str
    timestamp: str
    
    # 执行结果
    success: bool = False
    message: str = ""
    error: Optional[str] = None
    
    # 执行上下文
    parameters: Dict[str, Any] = field(default_factory=dict)
    preconditions_passed: bool = False
    preconditions_failed: List[str] = field(default_factory=list)
    
    # 状态变化
    changed_state: bool = False
    changed_fields: List[str] = field(default_factory=list)
    old_state_snapshot: Optional[Dict[str, Any]] = None
    new_state_snapshot: Optional[Dict[str, Any]] = None
    
    # 性能指标
    execution_time_ms: int = 0
    memory_usage_kb: int = 0
    
    # AI相关
    ai_suggested: bool = False
    ai_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def get_summary_text(self) -> str:
        """获取文本摘要"""
        lines = []
        lines.append("=" * 60)
        lines.append("动作执行回执")
        lines.append("=" * 60)
        lines.append(f"回执ID: {self.receipt_id}")
        lines.append(f"动作ID: {self.action_id}")
        lines.append(f"时间戳: {self.timestamp}")
        lines.append(f"执行结果: {'✅ 成功' if self.success else '❌ 失败'}")
        lines.append(f"执行消息: {self.message}")
        lines.append("")
        
        if self.parameters:
            lines.append("【执行参数】")
            for param, value in self.parameters.items():
                lines.append(f"  {param}: {value}")
            lines.append("")
        
        if not self.preconditions_passed and self.preconditions_failed:
            lines.append("【前置条件失败】")
            for condition in self.preconditions_failed:
                lines.append(f"  • {condition}")
            lines.append("")
        
        if self.error:
            lines.append("【错误信息】")
            lines.append(f"  {self.error}")
            lines.append("")
        
        if self.changed_state and self.changed_fields:
            lines.append("【状态变化】")
            for field in self.changed_fields:
                lines.append(f"  • {field}")
            lines.append("")
        
        lines.append("【性能指标】")
        lines.append(f"  执行时间: {self.execution_time_ms}ms")
        lines.append(f"  内存使用: {self.memory_usage_kb}KB")
        lines.append("")
        
        if self.ai_suggested:
            lines.append("【AI建议】")
            lines.append(f"  AI建议置信度: {self.ai_confidence:.2f}")
            lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)


# ====================== 动作注册表 ======================

class ActionRegistry:
    """动作注册表"""
    
    def __init__(self):
        self.actions: Dict[str, ActionDefinition] = {}
        self.categories: Dict[ActionCategory, List[str]] = {}
        self._initialize_default_actions()
    
    def _initialize_default_actions(self):
        """初始化默认动作词典"""
        default_actions = [
            # ========== 图片导航动作 ==========
            ActionDefinition(
                action_id="prev_image",
                display_name="上一张图片",
                description="切换到上一张图片",
                category=ActionCategory.NAVIGATION,
                needs_current_image=True,
                risk_level=1
            ),
            ActionDefinition(
                action_id="next_image",
                display_name="下一张图片",
                description="切换到下一张图片",
                category=ActionCategory.NAVIGATION,
                needs_current_image=True,
                risk_level=1
            ),
            ActionDefinition(
                action_id="jump_to_image",
                display_name="跳转到指定图片",
                description="跳转到指定名称或索引的图片",
                category=ActionCategory.NAVIGATION,
                parameters={
                    "image_name": {"type": str, "description": "图片名称"},
                    "image_index": {"type": int, "description": "图片索引"}
                },
                optional_parameters={"image_name": "", "image_index": -1},
                needs_current_image=False,
                risk_level=2
            ),
            
            # ========== 选框控制动作 ==========
            ActionDefinition(
                action_id="select_next_box",
                display_name="选中下一个框",
                description="选中当前图片的下一个标注框",
                category=ActionCategory.BOX_SELECTION,
                needs_current_image=True,
                min_box_count=1,
                risk_level=1
            ),
            ActionDefinition(
                action_id="select_prev_box",
                display_name="选中上一个框",
                description="选中当前图片的上一个标注框",
                category=ActionCategory.BOX_SELECTION,
                needs_current_image=True,
                min_box_count=1,
                risk_level=1
            ),
            ActionDefinition(
                action_id="select_box_by_index",
                display_name="按索引选中框",
                description="按索引选中指定标注框",
                category=ActionCategory.BOX_SELECTION,
                parameters={
                    "box_index": {"type": int, "description": "框索引"}
                },
                required_parameters=["box_index"],
                needs_current_image=True,
                min_box_count=1,
                risk_level=1
            ),
            
            # ========== 框编辑动作 ==========
            ActionDefinition(
                action_id="delete_selected_box",
                display_name="删除选中框",
                description="删除当前选中的标注框",
                category=ActionCategory.BOX_EDIT,
                needs_current_image=True,
                needs_selected_box=True,
                changes_boxes=True,
                risk_level=3,
                requires_confirmation=True,
                confirmation_message="确认删除选中框吗？"
            ),
            ActionDefinition(
                action_id="delete_box_by_index",
                display_name="按索引删除框",
                description="按索引删除指定标注框",
                category=ActionCategory.BOX_EDIT,
                parameters={
                    "box_index": {"type": int, "description": "框索引"}
                },
                required_parameters=["box_index"],
                needs_current_image=True,
                min_box_count=1,
                changes_boxes=True,
                risk_level=4,
                requires_confirmation=True,
                confirmation_message="确认删除指定框吗？"
            ),
            ActionDefinition(
                action_id="change_box_class_by_index",
                display_name="修改框类别",
                description="修改指定框的类别",
                category=ActionCategory.BOX_EDIT,
                parameters={
                    "box_index": {"type": int, "description": "框索引"},
                    "class_name": {"type": str, "description": "新类别名"}
                },
                required_parameters=["box_index", "class_name"],
                needs_current_image=True,
                min_box_count=1,
                changes_boxes=True,
                risk_level=2,
                requires_confirmation=False
            ),
            ActionDefinition(
                action_id="copy_labels_from_previous_image",
                display_name="复制上一张标签",
                description="复制上一张图片的标注到当前图片",
                category=ActionCategory.BOX_EDIT,
                needs_current_image=True,
                changes_boxes=True,
                risk_level=3,
                requires_confirmation=True,
                confirmation_message="确认复制上一张图片的标注吗？"
            ),
            
            # ========== 框分析动作 ==========
            ActionDefinition(
                action_id="analyze_box_by_index",
                display_name="分析指定框",
                description="分析指定标注框，提供建议",
                category=ActionCategory.BOX_ANALYSIS,
                parameters={
                    "box_index": {"type": int, "description": "框索引"}
                },
                required_parameters=["box_index"],
                needs_current_image=True,
                min_box_count=1,
                risk_level=1
            ),
            ActionDefinition(
                action_id="analyze_all_boxes",
                display_name="分析所有框",
                description="分析当前图片的所有标注框",
                category=ActionCategory.BOX_ANALYSIS,
                needs_current_image=True,
                risk_level=1
            ),
            
            # ========== 类别管理动作 ==========
            ActionDefinition(
                action_id="change_current_class",
                display_name="修改当前类别",
                description="修改当前选中的类别",
                category=ActionCategory.CLASS_MANAGEMENT,
                parameters={
                    "class_name": {"type": str, "description": "类别名"}
                },
                required_parameters=["class_name"],
                needs_class_list=True,
                risk_level=1
            ),
            
            # ========== 数据健康动作 ==========
            ActionDefinition(
                action_id="open_data_health_check",
                display_name="打开数据健康检查",
                description="打开数据健康检查窗口",
                category=ActionCategory.DATA_HEALTH,
                risk_level=1
            ),
            ActionDefinition(
                action_id="run_data_health_check",
                display_name="运行数据健康检查",
                description="运行数据健康检查",
                category=ActionCategory.DATA_HEALTH,
                risk_level=1
            ),
            
            # ========== 训练相关动作 ==========
            ActionDefinition(
                action_id="open_training_center",
                display_name="打开训练中心",
                description="打开训练中心窗口",
                category=ActionCategory.TRAINING,
                risk_level=1
            ),
            ActionDefinition(
                action_id="open_training_monitor",
                display_name="打开训练监控",
                description="打开训练监控窗口",
                category=ActionCategory.TRAINING,
                risk_level=1
            ),
            
            # ========== 闭环修正动作 ==========
            ActionDefinition(
                action_id="open_closed_loop_center",
                display_name="打开闭环修正中心",
                description="打开闭环修正中心窗口",
                category=ActionCategory.CLOSED_LOOP,
                risk_level=1
            ),
            ActionDefinition(
                action_id="add_bad_case",
                display_name="添加bad case",
                description="添加bad case记录",
                category=ActionCategory.CLOSED_LOOP,
                parameters={
                    "image_name": {"type": str, "description": "图片名"},
                    "problem_summary": {"type": str, "description": "问题摘要"}
                },
                required_parameters=["image_name", "problem_summary"],
                risk_level=2
            ),
            
            # ========== 系统动作 ==========
            ActionDefinition(
                action_id="save_current_labels",
                display_name="保存当前标注",
                description="保存当前图片的标注",
                category=ActionCategory.SYSTEM,
                needs_current_image=True,
                risk_level=1
            ),
            ActionDefinition(
                action_id="export_dataset",
                display_name="导出数据集",
                description="导出数据集",
                category=ActionCategory.SYSTEM,
                risk_level=2,
                requires_confirmation=True,
                confirmation_message="确认要导出数据集吗？"
            ),
            ActionDefinition(
                action_id="run_openclaw_analysis",
                display_name="运行OpenClaw分析",
                description="运行OpenClaw分析当前图片",
                category=ActionCategory.SYSTEM,
                needs_current_image=True,
                risk_level=1
            )
        ]
        
        for action in default_actions:
            self.register_action(action)
    
    def register_action(self, action_def: ActionDefinition):
        """注册动作"""
        action_def.updated_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not action_def.created_time:
            action_def.created_time = action_def.updated_time
        
        self.actions[action_def.action_id] = action_def
        
        # 更新类别索引
        if action_def.category not in self.categories:
            self.categories[action_def.category] = []
        if action_def.action_id not in self.categories[action_def.category]:
            self.categories[action_def.category].append(action_def.action_id)
    
    def get_action(self, action_id: str) -> Optional[ActionDefinition]:
        """获取动作定义"""
        return self.actions.get(action_id)
    
    def get_actions_by_category(self, category: ActionCategory) -> List[ActionDefinition]:
        """获取指定类别的动作"""
        action_ids = self.categories.get(category, [])
        return [self.actions[action_id] for action_id in action_ids if action_id in self.actions]
    
    def get_all_actions(self, enabled_only: bool = True) -> List[ActionDefinition]:
        """获取所有动作"""
        actions = list(self.actions.values())
        if enabled_only:
            actions = [a for a in actions if a.enabled]
        return actions
    
    def update_action_handler(self, action_id: str, handler: Callable):
        """更新动作处理器"""
        if action_id in self.actions:
            self.actions[action_id].handler = handler
            self.actions[action_id].handler_module = handler.__module__
            self.actions[action_id].handler_function = handler.__name__
            self.actions[action_id].updated_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def enable_action(self, action_id: str, enabled: bool = True):
        """启用/禁用动作"""
        if action_id in self.actions:
            self.actions[action_id].enabled = enabled
            self.actions[action_id].updated_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def increment_usage_count(self, action_id: str):
        """增加动作使用计数"""
        if action_id in self.actions:
            self.actions[action_id].usage_count += 1


# ====================== 前置条件检查器 ======================

class PreconditionChecker:
    """前置条件检查器"""
    
    @staticmethod
    def check_action_preconditions(action_def: ActionDefinition, 
                                  state_snapshot: StateSnapshot) -> Tuple[bool, List[str]]:
        """检查动作前置条件"""
        failed_conditions = []
        
        # 检查动作是否启用
        if not action_def.enabled:
            failed_conditions.append("动作未启用")
        
        # 检查是否需要当前图片
        if action_def.needs_current_image and not state_snapshot.has_current_image:
            failed_conditions.append("需要当前图片")
        
        # 检查最小框数要求
        if action_def.min_box_count > 0 and state_snapshot.box_count < action_def.min_box_count:
            failed_conditions.append(f"需要至少 {action_def.min_box_count} 个标注框，当前只有 {state_snapshot.box_count} 个")
        
        # 检查是否需要选中框
        if action_def.needs_selected_box and not state_snapshot.has_selected_box:
            failed_conditions.append("需要选中框")
        
        # 检查是否需要类别列表
        if action_def.needs_class_list and not state_snapshot.class_list:
            failed_conditions.append("需要类别列表")
        
        # 检查特定动作的额外条件
        if action_def.action_id == "jump_to_image":
            # 跳转图片需要图片目录
            if not state_snapshot.image_directory:
                failed_conditions.append("需要图片目录")
        
        if action_def.action_id == "export_dataset":
            # 导出数据集需要项目已加载
            if not state_snapshot.project_loaded:
                failed_conditions.append("需要加载项目")
        
        # 检查其他自定义前置条件
        for condition in action_def.preconditions:
            # 这里可以扩展为更复杂的条件检查
            if condition == "has_training_config" and not state_snapshot.training_center_available:
                failed_conditions.append("需要训练配置")
            elif condition == "has_health_check_data" and not state_snapshot.data_health_available:
                failed_conditions.append("需要健康检查数据")
        
        return len(failed_conditions) == 0, failed_conditions
    
    @staticmethod
    def get_precondition_summary(action_def: ActionDefinition, 
                                state_snapshot: StateSnapshot) -> str:
        """获取前置条件摘要"""
        passed, failed = PreconditionChecker.check_action_preconditions(action_def, state_snapshot)
        
        lines = []
        lines.append(f"动作: {action_def.display_name} ({action_def.action_id})")
        lines.append(f"前置条件检查: {'✅ 通过' if passed else '❌ 失败'}")
        
        if failed:
            lines.append("失败条件:")
            for condition in failed:
                lines.append(f"  • {condition}")
        
        # 添加状态信息
        lines.append("")
        lines.append("当前状态:")
        lines.append(f"  有当前图片: {state_snapshot.has_current_image}")
        lines.append(f"  标注框数量: {state_snapshot.box_count}")
        lines.append(f"  有选中框: {state_snapshot.has_selected_box}")
        lines.append(f"  类别数量: {state_snapshot.class_count}")
        lines.append(f"  项目已加载: {state_snapshot.project_loaded}")
        
        return "\n".join(lines)


# ====================== 状态快照生成器 ======================

class StateSnapshotGenerator:
    """状态快照生成器"""
    
    def __init__(self, main_window=None):
        self.main_window = main_window
    
    def generate_snapshot(self) -> StateSnapshot:
        """生成状态快照"""
        import uuid
        import time
        
        snapshot_id = f"snapshot_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        snapshot = StateSnapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp
        )
        
        if not self.main_window:
            return snapshot
        
        try:
            # 从主窗口获取状态
            # 图片状态
            if hasattr(self.main_window, 'current_image_name') and self.main_window.current_image_name:
                snapshot.current_image_name = self.main_window.current_image_name
                snapshot.has_current_image = True
            
            if hasattr(self.main_window, 'current_index'):
                snapshot.current_image_index = self.main_window.current_index
            
            if hasattr(self.main_window, 'image_files'):
                snapshot.total_image_count = len(self.main_window.image_files)
            
            if hasattr(self.main_window, 'image_dir'):
                snapshot.image_directory = self.main_window.image_dir
            
            if hasattr(self.main_window, 'label_dir'):
                snapshot.label_directory = self.main_window.label_dir
            
            # 框状态
            if hasattr(self.main_window, 'boxes'):
                snapshot.box_count = len(self.main_window.boxes)
            
            if hasattr(self.main_window, 'selected_idx') and self.main_window.selected_idx is not None:
                snapshot.has_selected_box = True
                snapshot.selected_box_index = self.main_window.selected_idx
                
                # 获取选中框类别
                if (snapshot.selected_box_index >= 0 and 
                    snapshot.selected_box_index < snapshot.box_count and
                    hasattr(self.main_window, 'boxes')):
                    box = self.main_window.boxes[snapshot.selected_box_index]
                    if len(box) >= 1:
                        class_id = box[0]
                        if (hasattr(self.main_window, 'current_class_names') and 
                            self.main_window.current_class_names and
                            0 <= class_id < len(self.main_window.current_class_names)):
                            snapshot.selected_box_class = self.main_window.current_class_names[class_id]
            
            # 类别状态
            if hasattr(self.main_window, 'current_class_names'):
                snapshot.class_list = self.main_window.current_class_names.copy()
                snapshot.class_count = len(snapshot.class_list)
            
            if hasattr(self.main_window, 'class_var'):
                snapshot.current_class_name = self.main_window.class_var.get()
            
            # 系统状态
            if hasattr(self.main_window, 'auto_save'):
                snapshot.auto_save_enabled = self.main_window.auto_save
            
            snapshot.project_loaded = bool(snapshot.image_directory and snapshot.label_directory)
            
            # 模块状态（通过检查按钮状态或窗口属性）
            snapshot.data_health_available = hasattr(self.main_window, 'data_health_check_btn')
            snapshot.training_center_available = hasattr(self.main_window, 'training_center_btn')
            snapshot.closed_loop_available = hasattr(self.main_window, 'closed_loop_btn')
            snapshot.dataset_export_available = hasattr(self.main_window, 'export_dataset_action')
            
            # AI状态（简化处理）
            snapshot.ai_enabled = True  # 假设启用
            
        except Exception as e:
            # 记录错误但不中断
            import traceback
            traceback.print_exc()
        
        return snapshot


# ====================== 动作分发器 ======================

class ActionDispatcher:
    """动作分发器"""
    
    def __init__(self, main_window=None):
        self.main_window = main_window
        self.registry = ActionRegistry()
        self.checker = PreconditionChecker()
        self.generator = StateSnapshotGenerator(main_window)
        
        # 历史记录
        self.execution_history: List[ActionReceipt] = []
        self.max_history_size = 100
        
        # 注册主窗口的动作处理器
        if main_window:
            self._register_main_window_handlers()
    
    def _register_main_window_handlers(self):
        """注册主窗口的动作处理器"""
        if not self.main_window:
            return
        
        # 映射动作ID到主窗口方法
        action_handlers = {
            # 图片导航
            "prev_image": getattr(self.main_window, 'prev_image', None),
            "next_image": getattr(self.main_window, 'next_image', None),
            "jump_to_image": getattr(self.main_window, '_jump_to_image_by_name', None),
            
            # 选框控制
            "select_next_box": getattr(self.main_window, 'select_next_box', None),
            "select_prev_box": getattr(self.main_window, 'select_prev_box', None),
            "select_box_by_index": getattr(self.main_window, 'select_box_by_index', None),
            
            # 框编辑
            "delete_selected_box": getattr(self.main_window, 'delete_selected_box', None),
            "delete_box_by_index": getattr(self.main_window, 'delete_box_by_index', None),
            "change_box_class_by_index": getattr(self.main_window, 'change_box_class_by_index', None),
            "copy_labels_from_previous_image": getattr(self.main_window, 'copy_labels_from_previous_image', None),
            
            # 框分析
            "analyze_box_by_index": getattr(self.main_window, 'analyze_box_by_index', None),
            "analyze_all_boxes": getattr(self.main_window, 'analyze_all_boxes', None),
            
            # 类别管理
            "change_current_class": getattr(self.main_window, 'change_selected_class', None),
            
            # 数据健康
            "open_data_health_check": getattr(self.main_window, 'open_data_health_check', None),
            
            # 训练相关
            "open_training_center": lambda: None,  # 需要特殊处理
            "open_training_monitor": lambda: None,  # 需要特殊处理
            
            # 闭环修正
            "open_closed_loop_center": lambda: None,  # 需要特殊处理
            
            # 系统动作
            "save_current_labels": getattr(self.main_window, 'save_current_labels', None),
            "export_dataset": getattr(self.main_window, 'export_dataset_action', None),
            "run_openclaw_analysis": getattr(self.main_window, 'run_openclaw_analysis', None),
        }
        
        # 更新动作处理器
        for action_id, handler in action_handlers.items():
            if handler:
                self.registry.update_action_handler(action_id, handler)
    
    def execute_action(self, action_id: str, **kwargs) -> ActionReceipt:
        """执行动作（统一入口）"""
        import uuid
        import time
        start_time = time.time()
        
        receipt_id = f"receipt_{int(start_time)}_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 创建基础回执
        receipt = ActionReceipt(
            receipt_id=receipt_id,
            action_id=action_id,
            timestamp=timestamp,
            parameters=kwargs,
            ai_suggested=kwargs.get('ai_suggested', False),
            ai_confidence=kwargs.get('ai_confidence', 0.0)
        )
        
        try:
            # 1. 获取动作定义
            action_def = self.registry.get_action(action_id)
            if not action_def:
                receipt.success = False
                receipt.message = f"未知动作: {action_id}"
                receipt.error = f"动作 '{action_id}' 未在注册表中找到"
                self._add_to_history(receipt)
                return receipt
            
            # 2. 生成状态快照（执行前）
            old_state = self.generator.generate_snapshot()
            receipt.old_state_snapshot = old_state.to_dict()
            
            # 3. 检查前置条件
            preconditions_passed, failed_conditions = self.checker.check_action_preconditions(action_def, old_state)
            receipt.preconditions_passed = preconditions_passed
            receipt.preconditions_failed = failed_conditions
            
            if not preconditions_passed:
                receipt.success = False
                receipt.message = "前置条件检查失败"
                receipt.error = f"前置条件不满足: {', '.join(failed_conditions)}"
                self._add_to_history(receipt)
                return receipt
            
            # 4. 参数验证
            if kwargs:
                params_valid, params_message = action_def.validate_parameters(kwargs)
                if not params_valid:
                    receipt.success = False
                    receipt.message = "参数验证失败"
                    receipt.error = params_message
                    self._add_to_history(receipt)
                    return receipt
            
            # 5. 如果需要确认，检查确认状态
            if action_def.requires_confirmation and not kwargs.get('confirmed', False):
                receipt.success = False
                receipt.message = "需要用户确认"
                receipt.error = f"动作需要确认: {action_def.confirmation_message}"
                receipt.changed_fields = ["confirmation_required"]
                self._add_to_history(receipt)
                return receipt
            
            # 6. 执行动作
            if action_def.handler:
                # 调用处理器
                try:
                    # 执行动作
                    result = action_def.handler(**kwargs) if kwargs else action_def.handler()
                    
                    # 处理返回结果
                    if isinstance(result, dict) and 'success' in result:
                        # 假设返回标准格式
                        receipt.success = result.get('success', False)
                        receipt.message = result.get('message', '动作执行完成')
                        receipt.error = result.get('error')
                    else:
                        receipt.success = True
                        receipt.message = f"动作 '{action_def.display_name}' 执行成功"
                        
                except Exception as e:
                    receipt.success = False
                    receipt.message = "动作执行时发生异常"
                    receipt.error = f"{type(e).__name__}: {str(e)}"
            else:
                # 没有处理器，尝试调用主窗口的execute_action（向后兼容）
                if self.main_window and hasattr(self.main_window, 'execute_action'):
                    try:
                        result = self.main_window.execute_action(action_id, **kwargs)
                        receipt.success = result.get('success', False)
                        receipt.message = result.get('message', '')
                        receipt.error = result.get('error')
                    except Exception as e:
                        receipt.success = False
                        receipt.message = "通过主窗口执行动作时发生异常"
                        receipt.error = f"{type(e).__name__}: {str(e)}"
                else:
                    receipt.success = False
                    receipt.message = "动作处理器未注册"
                    receipt.error = f"动作 '{action_id}' 没有注册的处理器"
            
            # 7. 更新状态变化
            if receipt.success:
                # 生成新状态快照
                new_state = self.generator.generate_snapshot()
                receipt.new_state_snapshot = new_state.to_dict()
                
                # 检测状态变化
                receipt.changed_state = self._detect_state_changes(old_state, new_state)
                if receipt.changed_state:
                    receipt.changed_fields = self._get_changed_fields(old_state, new_state)
                
                # 增加使用计数
                self.registry.increment_usage_count(action_id)
            
            # 8. 计算执行时间
            end_time = time.time()
            receipt.execution_time_ms = int((end_time - start_time) * 1000)
            
        except Exception as e:
            # 捕获未处理的异常
            import traceback
            receipt.success = False
            receipt.message = "动作分发过程中发生未处理异常"
            receipt.error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        
        # 9. 添加到历史记录
        self._add_to_history(receipt)
        
        return receipt
    
    def _detect_state_changes(self, old_state: StateSnapshot, new_state: StateSnapshot) -> bool:
        """检测状态变化"""
        # 简化实现：检查关键字段
        key_fields = [
            'current_image_name',
            'current_image_index',
            'box_count',
            'selected_box_index',
            'has_unsaved_changes'
        ]
        
        for field in key_fields:
            old_value = getattr(old_state, field, None)
            new_value = getattr(new_state, field, None)
            if old_value != new_value:
                return True
        
        return False
    
    def _get_changed_fields(self, old_state: StateSnapshot, new_state: StateSnapshot) -> List[str]:
        """获取变化字段列表"""
        changed_fields = []
        
        # 获取所有字段
        fields = [f for f in dir(old_state) if not f.startswith('_') and not callable(getattr(old_state, f))]
        
        for field in fields:
            try:
                old_value = getattr(old_state, field)
                new_value = getattr(new_state, field)
                
                if old_value != new_value:
                    changed_fields.append(field)
            except AttributeError:
                continue
        
        return changed_fields
    
    def _add_to_history(self, receipt: ActionReceipt):
        """添加到历史记录"""
        self.execution_history.append(receipt)
        
        # 限制历史记录大小
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size:]
    
    def get_recent_receipts(self, limit: int = 10) -> List[ActionReceipt]:
        """获取最近的动作回执"""
        return self.execution_history[-limit:] if self.execution_history else []
    
    def get_action_summary(self, action_id: str) -> Dict[str, Any]:
        """获取动作摘要"""
        action_def = self.registry.get_action(action_id)
        if not action_def:
            return {"error": f"动作 '{action_id}' 未找到"}
        
        # 获取相关回执
        related_receipts = [r for r in self.execution_history if r.action_id == action_id]
        
        summary = {
            "action_id": action_id,
            "display_name": action_def.display_name,
            "description": action_def.description,
            "category": action_def.category.value,
            "enabled": action_def.enabled,
            "usage_count": action_def.usage_count,
            "success_rate": 0.0,
            "recent_executions": len(related_receipts),
            "last_execution_time": action_def.updated_time
        }
        
        # 计算成功率
        if related_receipts:
            successful = sum(1 for r in related_receipts if r.success)
            summary["success_rate"] = successful / len(related_receipts)
        
        return summary
    
    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统摘要"""
        all_actions = self.registry.get_all_actions()
        enabled_actions = [a for a in all_actions if a.enabled]
        
        # 按类别统计
        category_stats = {}
        for action in enabled_actions:
            category = action.category.value
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
        
        # 历史统计
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for r in self.execution_history if r.success)
        
        return {
            "total_actions": len(all_actions),
            "enabled_actions": len(enabled_actions),
            "category_stats": category_stats,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / max(total_executions, 1),
            "recent_history_size": len(self.execution_history),
            "dispatcher_ready": True
        }


# ====================== 全局实例和工具函数 ======================

# 全局分发器实例
_global_dispatcher = None

def get_global_dispatcher(main_window=None) -> ActionDispatcher:
    """获取全局动作分发器实例"""
    global _global_dispatcher
    if _global_dispatcher is None:
        _global_dispatcher = ActionDispatcher(main_window)
    return _global_dispatcher

def execute_action_unified(action_id: str, **kwargs) -> ActionReceipt:
    """统一动作执行入口（工具函数）"""
    dispatcher = get_global_dispatcher()
    return dispatcher.execute_action(action_id, **kwargs)

def get_state_snapshot() -> StateSnapshot:
    """获取当前状态快照（工具函数）"""
    dispatcher = get_global_dispatcher()
    return dispatcher.generator.generate_snapshot()

def get_action_registry() -> ActionRegistry:
    """获取动作注册表（工具函数）"""
    dispatcher = get_global_dispatcher()
    return dispatcher.registry

def get_precondition_check(action_id: str) -> str:
    """获取动作前置条件检查结果（工具函数）"""
    dispatcher = get_global_dispatcher()
    action_def = dispatcher.registry.get_action(action_id)
    
    if not action_def:
        return f"动作 '{action_id}' 未找到"
    
    state_snapshot = get_state_snapshot()
    return PreconditionChecker.get_precondition_summary(action_def, state_snapshot)