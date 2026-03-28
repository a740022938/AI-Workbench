#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
closed_loop_manager.py - 闭环修正中心管理器

功能：
1. bad case 收集与列表管理
2. 低表现类别回流入口
3. 结果回流到图片/标注处理
4. 再训练建议摘要
5. 闭环修正报告生成
"""

import os
import json
import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
import shutil


class BadCaseSource(Enum):
    """bad case 来源类型"""
    QUALITY_CHECK = "质检问题回流"
    TRAINING_RESULT = "训练结果人工加入"
    MANUAL_MARK = "手动标记"
    AI_SUGGESTION = "AI建议"
    PERFORMANCE_LOW = "低表现类别回流"
    
    @classmethod
    def from_string(cls, value: str):
        for source in cls:
            if source.value == value:
                return source
        return cls.MANUAL_MARK


class BadCaseStatus(Enum):
    """bad case 状态"""
    PENDING = "待处理"
    PROCESSING = "处理中"
    RESOLVED = "已解决"
    SKIPPED = "已跳过"
    REOPENED = "已重新打开"


@dataclass
class BadCaseRecord:
    """bad case 记录数据结构"""
    # 基础信息
    id: str
    image_name: str
    source_type: BadCaseSource
    problem_summary: str
    create_time: str
    
    # 状态信息
    status: BadCaseStatus = BadCaseStatus.PENDING
    update_time: str = ""
    
    # 问题详情
    issue_type: str = ""  # 问题类型，如"标注错误"、"低置信度"等
    class_name: str = ""  # 相关类别名
    confidence: float = 0.0  # 置信度或严重程度
    file_path: str = ""  # 原始文件路径
    label_path: str = ""  # 标签文件路径
    
    # 处理信息
    assigned_to: str = ""  # 分配给谁处理
    resolution_note: str = ""  # 处理说明
    resolution_time: str = ""  # 处理时间
    
    # AI建议预留字段
    ai_suggestions: List[str] = field(default_factory=list)
    ai_confidence: float = 0.0
    
    # 回流信息
    can_jump_to_image: bool = True
    jump_target: str = ""  # 跳转目标（图片名或文件路径）
    related_modules: List[str] = field(default_factory=list)  # 相关处理模块
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['source_type'] = self.source_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BadCaseRecord':
        """从字典创建实例"""
        # 转换枚举值
        data['source_type'] = BadCaseSource.from_string(data.get('source_type', ''))
        data['status'] = BadCaseStatus(data.get('status', BadCaseStatus.PENDING.value))
        return cls(**data)


@dataclass
class LowPerformanceClass:
    """低表现类别记录"""
    class_name: str
    problem_description: str
    suggested_actions: List[str]
    create_time: str
    update_time: str = ""
    
    # 性能指标（预留）
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    sample_count: int = 0
    error_count: int = 0
    
    # 处理状态
    status: str = "待处理"  # 待处理、处理中、已处理、已忽略
    priority: int = 1  # 优先级 1-5
    
    # 回流信息
    related_bad_cases: List[str] = field(default_factory=list)  # 相关的bad case ID
    jump_targets: List[str] = field(default_factory=list)  # 跳转目标列表
    
    # AI建议预留字段
    ai_analysis: str = ""
    ai_recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ClosedLoopReport:
    """闭环修正报告"""
    report_id: str
    generate_time: str
    
    # 统计信息
    total_bad_cases: int = 0
    pending_bad_cases: int = 0
    resolved_bad_cases: int = 0
    
    total_low_performance_classes: int = 0
    pending_classes: int = 0
    resolved_classes: int = 0
    
    # 时间范围
    time_period_start: str = ""
    time_period_end: str = ""
    
    # 问题分布
    problem_distribution: Dict[str, int] = field(default_factory=dict)
    class_distribution: Dict[str, int] = field(default_factory=dict)
    
    # 建议摘要
    training_suggestions: List[str] = field(default_factory=list)
    quality_suggestions: List[str] = field(default_factory=list)
    urgent_actions: List[str] = field(default_factory=list)
    
    # AI分析预留
    ai_insights: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def get_summary_text(self) -> str:
        """获取文本摘要"""
        lines = []
        lines.append("=" * 60)
        lines.append("闭环修正报告摘要")
        lines.append("=" * 60)
        lines.append(f"报告ID: {self.report_id}")
        lines.append(f"生成时间: {self.generate_time}")
        lines.append("")
        lines.append("【Bad Case 统计】")
        lines.append(f"  总数: {self.total_bad_cases}")
        lines.append(f"  待处理: {self.pending_bad_cases}")
        lines.append(f"  已处理: {self.resolved_bad_cases}")
        lines.append(f"  处理率: {self.resolved_bad_cases/max(self.total_bad_cases,1)*100:.1f}%")
        lines.append("")
        lines.append("【低表现类别统计】")
        lines.append(f"  总数: {self.total_low_performance_classes}")
        lines.append(f"  待处理: {self.pending_classes}")
        lines.append(f"  已处理: {self.resolved_classes}")
        lines.append("")
        lines.append("【建议摘要】")
        if self.urgent_actions:
            lines.append("  紧急行动:")
            for action in self.urgent_actions:
                lines.append(f"    • {action}")
        if self.training_suggestions:
            lines.append("  训练建议:")
            for suggestion in self.training_suggestions:
                lines.append(f"    • {suggestion}")
        if self.quality_suggestions:
            lines.append("  质检建议:")
            for suggestion in self.quality_suggestions:
                lines.append(f"    • {suggestion}")
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)


class ClosedLoopManager:
    """闭环修正中心管理器"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化管理器
        
        Args:
            data_dir: 数据存储目录，如果为None则使用默认目录
        """
        if data_dir is None:
            # 默认目录在当前工作目录下
            data_dir = os.path.join(os.getcwd(), "closed_loop_data")
        
        self.data_dir = data_dir
        self.bad_cases_dir = os.path.join(data_dir, "bad_cases")
        self.low_performance_dir = os.path.join(data_dir, "low_performance")
        self.reports_dir = os.path.join(data_dir, "reports")
        
        # 创建目录
        os.makedirs(self.bad_cases_dir, exist_ok=True)
        os.makedirs(self.low_performance_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # 内存缓存
        self._bad_cases_cache = {}
        self._low_performance_cache = {}
        self._reports_cache = {}
        
        # 加载现有数据
        self._load_all_data()
    
    def _load_all_data(self):
        """加载所有数据"""
        # 加载bad cases
        bad_case_files = [f for f in os.listdir(self.bad_cases_dir) if f.endswith('.json')]
        for file in bad_case_files:
            try:
                with open(os.path.join(self.bad_cases_dir, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    record = BadCaseRecord.from_dict(data)
                    self._bad_cases_cache[record.id] = record
            except Exception:
                continue
        
        # 加载低表现类别
        low_perf_files = [f for f in os.listdir(self.low_performance_dir) if f.endswith('.json')]
        for file in low_perf_files:
            try:
                with open(os.path.join(self.low_performance_dir, file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    record = LowPerformanceClass(**data)
                    # 使用类别名作为key，但实际应该用ID，这里简化处理
                    key = f"{record.class_name}_{record.create_time}"
                    self._low_performance_cache[key] = record
            except Exception:
                continue
    
    def _save_bad_case(self, record: BadCaseRecord) -> bool:
        """保存bad case记录"""
        try:
            file_path = os.path.join(self.bad_cases_dir, f"{record.id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
            self._bad_cases_cache[record.id] = record
            return True
        except Exception:
            return False
    
    def _save_low_performance_class(self, record: LowPerformanceClass) -> bool:
        """保存低表现类别记录"""
        try:
            key = f"{record.class_name}_{record.create_time}"
            file_path = os.path.join(self.low_performance_dir, f"{key}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
            self._low_performance_cache[key] = record
            return True
        except Exception:
            return False
    
    def add_bad_case(self, 
                    image_name: str, 
                    source_type: BadCaseSource,
                    problem_summary: str,
                    **kwargs) -> Tuple[bool, str]:
        """
        添加bad case记录
        
        Args:
            image_name: 图片名
            source_type: 来源类型
            problem_summary: 问题摘要
            **kwargs: 其他字段
            
        Returns:
            (是否成功, 消息)
        """
        try:
            # 生成ID
            import uuid
            import time
            record_id = f"badcase_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # 创建记录
            record = BadCaseRecord(
                id=record_id,
                image_name=image_name,
                source_type=source_type,
                problem_summary=problem_summary,
                create_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                update_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status=BadCaseStatus.PENDING
            )
            
            # 设置可选字段
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            # 自动设置跳转目标
            if not record.jump_target:
                record.jump_target = image_name
            
            # 自动设置相关模块
            if not record.related_modules:
                if source_type in [BadCaseSource.QUALITY_CHECK, BadCaseSource.AI_SUGGESTION]:
                    record.related_modules = ["质检中心", "标注编辑"]
                elif source_type == BadCaseSource.TRAINING_RESULT:
                    record.related_modules = ["训练中心", "标注编辑"]
                else:
                    record.related_modules = ["标注编辑"]
            
            # 保存
            success = self._save_bad_case(record)
            if success:
                return True, f"已添加bad case: {record_id}"
            else:
                return False, "保存失败"
                
        except Exception as e:
            return False, f"添加bad case失败: {str(e)}"
    
    def add_low_performance_class(self,
                                 class_name: str,
                                 problem_description: str,
                                 suggested_actions: List[str],
                                 **kwargs) -> Tuple[bool, str]:
        """
        添加低表现类别记录
        
        Args:
            class_name: 类别名
            problem_description: 问题描述
            suggested_actions: 建议动作列表
            **kwargs: 其他字段
            
        Returns:
            (是否成功, 消息)
        """
        try:
            create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            record = LowPerformanceClass(
                class_name=class_name,
                problem_description=problem_description,
                suggested_actions=suggested_actions,
                create_time=create_time,
                update_time=create_time,
                status="待处理",
                priority=kwargs.get('priority', 1)
            )
            
            # 设置可选字段
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            # 保存
            success = self._save_low_performance_class(record)
            if success:
                return True, f"已添加低表现类别: {class_name}"
            else:
                return False, "保存失败"
                
        except Exception as e:
            return False, f"添加低表现类别失败: {str(e)}"
    
    def get_all_bad_cases(self, 
                         status_filter: Optional[BadCaseStatus] = None,
                         source_filter: Optional[BadCaseSource] = None) -> List[BadCaseRecord]:
        """
        获取所有bad case记录
        
        Args:
            status_filter: 状态过滤器
            source_filter: 来源过滤器
            
        Returns:
            bad case记录列表
        """
        records = list(self._bad_cases_cache.values())
        
        # 应用过滤器
        if status_filter:
            records = [r for r in records if r.status == status_filter]
        if source_filter:
            records = [r for r in records if r.source_type == source_filter]
        
        # 按时间倒序排序
        records.sort(key=lambda x: x.create_time, reverse=True)
        
        return records
    
    def get_all_low_performance_classes(self,
                                       status_filter: Optional[str] = None,
                                       min_priority: Optional[int] = None) -> List[LowPerformanceClass]:
        """
        获取所有低表现类别记录
        
        Args:
            status_filter: 状态过滤器
            min_priority: 最小优先级
            
        Returns:
            低表现类别记录列表
        """
        records = list(self._low_performance_cache.values())
        
        # 应用过滤器
        if status_filter:
            records = [r for r in records if r.status == status_filter]
        if min_priority is not None:
            records = [r for r in records if r.priority >= min_priority]
        
        # 按优先级和时间排序
        records.sort(key=lambda x: (-x.priority, x.create_time))
        
        return records
    
    def update_bad_case_status(self, 
                              case_id: str, 
                              new_status: BadCaseStatus,
                              resolution_note: str = "",
                              assigned_to: str = "") -> Tuple[bool, str]:
        """
        更新bad case状态
        
        Args:
            case_id: bad case ID
            new_status: 新状态
            resolution_note: 处理说明
            assigned_to: 分配给谁
            
        Returns:
            (是否成功, 消息)
        """
        if case_id not in self._bad_cases_cache:
            return False, f"未找到bad case: {case_id}"
        
        try:
            record = self._bad_cases_cache[case_id]
            record.status = new_status
            record.update_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if resolution_note:
                record.resolution_note = resolution_note
            if assigned_to:
                record.assigned_to = assigned_to
            
            if new_status == BadCaseStatus.RESOLVED:
                record.resolution_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            success = self._save_bad_case(record)
            if success:
                return True, f"已更新状态为: {new_status.value}"
            else:
                return False, "保存失败"
                
        except Exception as e:
            return False, f"更新状态失败: {str(e)}"
    
    def get_training_suggestions_summary(self, 
                                       bad_cases: Optional[List[BadCaseRecord]] = None,
                                       low_perf_classes: Optional[List[LowPerformanceClass]] = None) -> str:
        """
        生成再训练建议摘要
        
        Args:
            bad_cases: 指定的bad cases，如果为None则使用所有
            low_perf_classes: 指定的低表现类别，如果为None则使用所有
            
        Returns:
            建议摘要文本
        """
        if bad_cases is None:
            bad_cases = self.get_all_bad_cases()
        
        if low_perf_classes is None:
            low_perf_classes = self.get_all_low_performance_classes()
        
        # 统计
        pending_bad_cases = [c for c in bad_cases if c.status == BadCaseStatus.PENDING]
        pending_classes = [c for c in low_perf_classes if c.status == "待处理"]
        
        lines = []
        lines.append("=" * 60)
        lines.append("再训练建议摘要")
        lines.append("=" * 60)
        lines.append(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        lines.append("【问题统计】")
        lines.append(f"  待处理 bad cases: {len(pending_bad_cases)}")
        lines.append(f"  待处理低表现类别: {len(pending_classes)}")
        lines.append("")
        
        if pending_classes:
            lines.append("【低表现类别分析】")
            for i, cls in enumerate(pending_classes[:5], 1):
                lines.append(f"  {i}. {cls.class_name}: {cls.problem_description}")
                if cls.suggested_actions:
                    lines.append(f"     建议: {', '.join(cls.suggested_actions[:2])}")
            if len(pending_classes) > 5:
                lines.append(f"  还有{len(pending_classes) - 5}个低表现类别未显示...")
            lines.append("")
        
        if pending_bad_cases:
            lines.append("【Bad Case 分析】")
            # 按类别分组
            class_groups = {}
            for case in pending_bad_cases:
                if case.class_name:
                    if case.class_name not in class_groups:
                        class_groups[case.class_name] = 0
                    class_groups[case.class_name] += 1
            
            if class_groups:
                lines.append("  问题类别分布:")
                for class_name, count in sorted(class_groups.items(), key=lambda x: x[1], reverse=True)[:5]:
                    lines.append(f"    • {class_name}: {count}个问题")
            lines.append("")
        
        lines.append("【训练建议】")
        
        # 生成基础建议
        suggestions = []
        
        if len(pending_classes) > 3:
            suggestions.append("多个类别表现不佳，建议重新检查标注数据质量")
        
        if len(pending_bad_cases) > 10:
            suggestions.append("bad cases数量较多，建议优先处理高优先级问题")
        
        if pending_classes:
            class_names = ", ".join([c.class_name for c in pending_classes[:3]])
            suggestions.append(f"低表现类别({class_names})需要额外训练样本")
        
        if not suggestions:
            suggestions.append("当前问题较少，可继续监控")
        
        for i, suggestion in enumerate(suggestions, 1):
            lines.append(f"  {i}. {suggestion}")
        
        lines.append("")
        lines.append("【处理路径】")
        lines.append("  1. 质检中心 → 检查标注质量问题")
        lines.append("  2. 标注编辑 → 修正具体问题")
        lines.append("  3. 数据集制作中心 → 重新划分数据集")
        lines.append("  4. 训练中心 → 启动再训练")
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def generate_closed_loop_report(self, 
                                  time_period_start: str = "",
                                  time_period_end: str = "") -> ClosedLoopReport:
        """
        生成闭环修正报告
        
        Args:
            time_period_start: 时间范围开始
            time_period_end: 时间范围结束
            
        Returns:
            闭环修正报告
        """
        import uuid
        
        # 获取所有数据
        all_bad_cases = self.get_all_bad_cases()
        all_low_perf = self.get_all_low_performance_classes()
        
        # 过滤时间范围
        if time_period_start:
            filtered_bad_cases = []
            for case in all_bad_cases:
                if case.create_time >= time_period_start:
                    if not time_period_end or case.create_time <= time_period_end:
                        filtered_bad_cases.append(case)
            all_bad_cases = filtered_bad_cases
        
        # 统计
        total_bad_cases = len(all_bad_cases)
        pending_bad_cases = len([c for c in all_bad_cases if c.status == BadCaseStatus.PENDING])
        resolved_bad_cases = len([c for c in all_bad_cases if c.status == BadCaseStatus.RESOLVED])
        
        total_low_perf = len(all_low_perf)
        pending_classes = len([c for c in all_low_perf if c.status == "待处理"])
        resolved_classes = len([c for c in all_low_perf if c.status == "已处理"])
        
        # 问题分布
        problem_dist = {}
        for case in all_bad_cases:
            problem_type = case.issue_type or "未分类"
            if problem_type not in problem_dist:
                problem_dist[problem_type] = 0
            problem_dist[problem_type] += 1
        
        # 类别分布
        class_dist = {}
        for case in all_bad_cases:
            if case.class_name:
                if case.class_name not in class_dist:
                    class_dist[case.class_name] = 0
                class_dist[case.class_name] += 1
        
        # 生成报告
        report_id = f"report_{int(datetime.datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        report = ClosedLoopReport(
            report_id=report_id,
            generate_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_bad_cases=total_bad_cases,
            pending_bad_cases=pending_bad_cases,
            resolved_bad_cases=resolved_bad_cases,
            total_low_performance_classes=total_low_perf,
            pending_classes=pending_classes,
            resolved_classes=resolved_classes,
            time_period_start=time_period_start,
            time_period_end=time_period_end,
            problem_distribution=problem_dist,
            class_distribution=class_dist
        )
        
        # 生成建议
        suggestions = self._generate_report_suggestions(report)
        report.training_suggestions = suggestions.get('training', [])
        report.quality_suggestions = suggestions.get('quality', [])
        report.urgent_actions = suggestions.get('urgent', [])
        
        # 保存报告
        try:
            report_path = os.path.join(self.reports_dir, f"{report_id}.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        
        return report
    
    def _generate_report_suggestions(self, report: ClosedLoopReport) -> Dict[str, List[str]]:
        """生成报告建议"""
        suggestions = {
            'training': [],
            'quality': [],
            'urgent': []
        }
        
        # 紧急行动
        if report.pending_bad_cases > 20:
            suggestions['urgent'].append(f"有{report.pending_bad_cases}个bad case待处理，建议优先处理")
        
        if report.pending_classes > 5:
            suggestions['urgent'].append(f"有{report.pending_classes}个低表现类别，建议检查标注数据")
        
        # 训练建议
        if report.resolved_bad_cases > 10:
            suggestions['training'].append("已处理多个bad cases，建议重新训练模型")
        
        if report.total_low_performance_classes > 0:
            suggestions['training'].append("存在低表现类别，建议增加这些类别的训练样本")
        
        # 质检建议
        if report.total_bad_cases > 0:
            suggestions['quality'].append("建议运行数据健康检查，发现潜在问题")
        
        # 如果没有建议，添加默认建议
        if not any(suggestions.values()):
            suggestions['training'].append("当前状态良好，建议定期监控")
        
        return suggestions
    
    def get_jump_target_for_bad_case(self, case_id: str) -> Tuple[bool, str, str]:
        """
        获取bad case的跳转目标
        
        Args:
            case_id: bad case ID
            
        Returns:
            (是否成功, 跳转目标, 消息)
        """
        if case_id not in self._bad_cases_cache:
            return False, "", f"未找到bad case: {case_id}"
        
        record = self._bad_cases_cache[case_id]
        
        if not record.jump_target and not record.image_name:
            return False, "", "未设置跳转目标"
        
        # 优先使用jump_target，其次使用image_name
        target = record.jump_target or record.image_name
        module_hint = ""
        
        if record.related_modules:
            module_hint = f"建议跳转到: {', '.join(record.related_modules)}"
        else:
            module_hint = "建议跳转到标注编辑"
        
        return True, target, module_hint
    
    def get_bad_case_by_id(self, case_id: str) -> Optional[BadCaseRecord]:
        """根据ID获取bad case"""
        return self._bad_cases_cache.get(case_id)
    
    def get_low_performance_class_by_name(self, class_name: str) -> List[LowPerformanceClass]:
        """根据类别名获取低表现类别记录"""
        return [r for r in self._low_performance_cache.values() if r.class_name == class_name]


# ====================== 工具函数 ======================

def create_bad_case_from_quality_check(image_name: str, 
                                      issue_type: str, 
                                      problem_summary: str,
                                      class_name: str = "",
                                      **kwargs) -> Dict[str, Any]:
    """
    从质检问题创建bad case（方便函数）
    
    Returns:
        可用于add_bad_case的参数字典
    """
    return {
        'image_name': image_name,
        'source_type': BadCaseSource.QUALITY_CHECK,
        'problem_summary': problem_summary,
        'issue_type': issue_type,
        'class_name': class_name,
        'related_modules': ["质检中心", "标注编辑"],
        **kwargs
    }


def create_bad_case_from_training_result(image_name: str,
                                        problem_summary: str,
                                        class_name: str = "",
                                        confidence: float = 0.0,
                                        **kwargs) -> Dict[str, Any]:
    """
    从训练结果创建bad case（方便函数）
    
    Returns:
        可用于add_bad_case的参数字典
    """
    return {
        'image_name': image_name,
        'source_type': BadCaseSource.TRAINING_RESULT,
        'problem_summary': problem_summary,
        'class_name': class_name,
        'confidence': confidence,
        'related_modules': ["训练中心", "标注编辑"],
        **kwargs
    }


def create_low_performance_class_simple(class_name: str,
                                       problem: str,
                                       sample_count: int = 0,
                                       **kwargs) -> Dict[str, Any]:
    """
    创建低表现类别记录（方便函数）
    
    Returns:
        可用于add_low_performance_class的参数字典
    """
    suggested_actions = [
        "检查该类别的标注质量",
        "增加该类别的训练样本",
        "验证该类别的评估指标"
    ]
    
    return {
        'class_name': class_name,
        'problem_description': problem,
        'suggested_actions': suggested_actions,
        'sample_count': sample_count,
        'priority': 2,
        **kwargs
    }