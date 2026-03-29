#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
data_health_fixer.py - 数据集健康问题安全修复器

职责：安全修复数据集健康检查发现的问题。
目标：提供可靠、安全的自动修复，避免数据损失。

设计原则：
1. 只进行安全修复，不进行复杂AI推理
2. 修复前必须有确认
3. 修复后保留原始数据（不删除原始文件，修改标签文件）
4. 为后续批量修复、AI复核预留接口
"""

import os
import datetime
import shutil
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
from dataclasses import dataclass, field

from core.data_health_manager import (
    HealthIssue, 
    IssueType,
    IssueSeverity,
    DataHealthManager
)


class FixResult(Enum):
    """修复结果状态"""
    SUCCESS = "success"            # 修复成功
    SKIPPED = "skipped"            # 跳过（不需要修复）
    NOT_SUPPORTED = "not_supported"  # 不支持自动修复
    FAILED = "failed"              # 修复失败
    CANCELLED = "cancelled"        # 用户取消


@dataclass
class FixOperation:
    """修复操作记录"""
    issue: HealthIssue              # 原始问题
    fix_type: str                   # 修复类型
    result: FixResult               # 修复结果
    message: str                    # 结果消息
    backup_path: str = ""           # 备份文件路径（如有）
    changes: Dict[str, Any] = field(default_factory=dict)  # 具体变更内容


@dataclass
class FixReceipt:
    """修复回执：记录一次修复会话的结果"""
    session_id: str
    start_time: str
    end_time: str
    operations: List[FixOperation] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    modified_files: List[str] = field(default_factory=list)
    
    def generate_summary(self):
        """生成修复结果摘要"""
        total = len(self.operations)
        success = sum(1 for op in self.operations if op.result == FixResult.SUCCESS)
        failed = sum(1 for op in self.operations if op.result == FixResult.FAILED)
        skipped = sum(1 for op in self.operations if op.result == FixResult.SKIPPED)
        not_supported = sum(1 for op in self.operations if op.result == FixResult.NOT_SUPPORTED)
        cancelled = sum(1 for op in self.operations if op.result == FixResult.CANCELLED)
        
        # 收集修改的文件
        modified = set()
        # 按问题类型统计
        issue_type_counts = {}
        # 失败的操作
        failed_ops = []
        # 不支持的操作
        not_supported_ops = []
        
        for op in self.operations:
            # 统计问题类型
            issue_type = op.issue.issue_type.value
            if issue_type not in issue_type_counts:
                issue_type_counts[issue_type] = 0
            issue_type_counts[issue_type] += 1
            
            # 收集修改的文件
            if op.result == FixResult.SUCCESS and op.issue.file_path:
                modified.add(op.issue.file_path)
            
            # 记录失败操作
            if op.result == FixResult.FAILED:
                failed_ops.append({
                    "file": op.issue.file_name,
                    "issue_type": issue_type,
                    "message": op.message,
                    "details": op.changes
                })
            
            # 记录不支持的操作
            if op.result == FixResult.NOT_SUPPORTED:
                not_supported_ops.append({
                    "file": op.issue.file_name,
                    "issue_type": issue_type,
                    "message": op.message,
                    "reason": "不支持自动修复"
                })
        
        self.summary = {
            "total_attempted": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "not_supported": not_supported,
            "cancelled": cancelled,
            "success_rate": success / total if total > 0 else 0,
            "modified_files_count": len(modified),
            "modified_files": sorted(list(modified)),
            "issue_type_counts": issue_type_counts,
            "failed_operations": failed_ops,
            "not_supported_operations": not_supported_ops,
            "issue_types_handled": list(issue_type_counts.keys())
        }
        
        return self.summary
    
    def get_receipt_text(self) -> str:
        """获取回执文本（用于显示）"""
        self.generate_summary()
        lines = []
        lines.append("=" * 60)
        lines.append("修复回执")
        lines.append("=" * 60)
        lines.append(f"会话ID: {self.session_id}")
        lines.append(f"开始时间: {self.start_time}")
        lines.append(f"结束时间: {self.end_time}")
        lines.append("")
        lines.append("修复结果统计:")
        lines.append(f"  总共尝试修复: {self.summary['total_attempted']}")
        lines.append(f"  成功: {self.summary['success']}")
        lines.append(f"  失败: {self.summary['failed']}")
        lines.append(f"  跳过: {self.summary['skipped']}")
        lines.append(f"  不支持: {self.summary['not_supported']}")
        lines.append(f"  用户取消: {self.summary['cancelled']}")
        lines.append(f"  成功率: {self.summary['success_rate']:.1%}")
        lines.append("")
        
        if self.summary['modified_files_count'] > 0:
            lines.append(f"修改的文件 ({self.summary['modified_files_count']}个):")
            for file in self.summary['modified_files']:
                lines.append(f"  • {os.path.basename(file)}")
        else:
            lines.append("没有文件被修改")
        
        lines.append("=" * 60)
        return "\n".join(lines)

    def get_detailed_report(self) -> str:
        """获取详细修复报告"""
        self.generate_summary()
        lines = []
        lines.append("=" * 80)
        lines.append("详细修复报告")
        lines.append("=" * 80)
        lines.append(f"会话ID: {self.session_id}")
        lines.append(f"开始时间: {self.start_time}")
        lines.append(f"结束时间: {self.end_time}")
        lines.append("")
        
        lines.append("修复结果摘要:")
        lines.append(f"  总共尝试修复: {self.summary['total_attempted']}")
        lines.append(f"  成功: {self.summary['success']}")
        lines.append(f"  失败: {self.summary['failed']}")
        lines.append(f"  跳过: {self.summary['skipped']}")
        lines.append(f"  不支持: {self.summary['not_supported']}")
        lines.append(f"  用户取消: {self.summary['cancelled']}")
        lines.append(f"  成功率: {self.summary['success_rate']:.1%}")
        lines.append("")
        
        # 问题类型统计
        if self.summary['issue_type_counts']:
            lines.append("处理的问题类型统计:")
            for issue_type, count in sorted(self.summary['issue_type_counts'].items()):
                lines.append(f"  • {issue_type}: {count}个")
            lines.append("")
        
        # 修改的文件
        if self.summary['modified_files_count'] > 0:
            lines.append(f"修改的文件 ({self.summary['modified_files_count']}个):")
            for file in self.summary['modified_files']:
                lines.append(f"  • {os.path.basename(file)}")
            lines.append("")
        else:
            lines.append("没有文件被修改")
            lines.append("")
        
        # 失败的操作
        if self.summary['failed_operations']:
            lines.append(f"失败的操作 ({len(self.summary['failed_operations'])}个):")
            for i, op in enumerate(self.summary['failed_operations'], 1):
                lines.append(f"  {i}. 文件: {op['file'] or '未知'}")
                lines.append(f"     问题类型: {op['issue_type']}")
                lines.append(f"     错误消息: {op['message']}")
                if op['details']:
                    lines.append(f"     详情: {op['details']}")
            lines.append("")
        
        # 不支持的操作
        if self.summary['not_supported_operations']:
            lines.append(f"不支持自动修复的操作 ({len(self.summary['not_supported_operations'])}个):")
            for i, op in enumerate(self.summary['not_supported_operations'], 1):
                lines.append(f"  {i}. 文件: {op['file'] or '未知'}")
                lines.append(f"     问题类型: {op['issue_type']}")
                lines.append(f"     原因: {op['message']}")
            lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)


class DataHealthFixer:
    """数据集健康问题安全修复器"""
    
    def __init__(self, health_manager: DataHealthManager):
        """
        初始化修复器
        
        Args:
            health_manager: 健康管理器实例
        """
        self.health_manager = health_manager
        self.context = health_manager.context
        # 备份目录
        self.backup_dir = self._get_backup_dir()
        self.fix_history: List[FixOperation] = []
        self.current_receipt: Optional[FixReceipt] = None
        self.receipt_history: List[FixReceipt] = []
    
    def _get_backup_dir(self) -> str:
        """获取备份目录"""
        # 尝试从context获取
        if hasattr(self.context, 'backup_dir') and self.context.backup_dir:
            backup_base = self.context.backup_dir
        else:
            # 默认备份目录：项目根目录下的backup文件夹
            workbench_root = getattr(self.context, 'workbench_root', '.')
            backup_base = os.path.join(workbench_root, "backup")
        
        # 创建健康修复专用子目录
        backup_dir = os.path.join(backup_base, "health_fixes")
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir
    
    # ==================== 修复会话管理 ====================
    
    def start_fix_session(self) -> str:
        """开始一个新的修复会话"""
        import uuid
        session_id = f"fix_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self.current_receipt = FixReceipt(
            session_id=session_id,
            start_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            end_time="",
            operations=[],
            summary={},
            modified_files=[]
        )
        return session_id
    
    def end_fix_session(self) -> FixReceipt:
        """结束当前修复会话并返回回执"""
        if not self.current_receipt:
            raise ValueError("没有活动的修复会话")
        
        self.current_receipt.end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.current_receipt.generate_summary()
        self.receipt_history.append(self.current_receipt)
        receipt = self.current_receipt
        self.current_receipt = None
        return receipt
    
    def add_operation_to_session(self, operation: FixOperation):
        """添加修复操作到当前会话"""
        if self.current_receipt:
            self.current_receipt.operations.append(operation)
        # 始终添加到历史记录
        self.fix_history.append(operation)
    
    def get_latest_receipt(self) -> Optional[FixReceipt]:
        """获取最新的修复回执"""
        if self.receipt_history:
            return self.receipt_history[-1]
        return None
    
    def get_receipt_by_id(self, session_id: str) -> Optional[FixReceipt]:
        """根据会话ID获取修复回执"""
        for receipt in self.receipt_history:
            if receipt.session_id == session_id:
                return receipt
        return None
    
    def get_recent_receipts(self, limit: int = 10) -> List[FixReceipt]:
        """
        获取最近的修复回执
        
        Args:
            limit: 最大返回数量
            
        Returns:
            最近的修复回执列表，按时间倒序排列
        """
        # 确保每个回执都有摘要
        for receipt in self.receipt_history:
            receipt.generate_summary()
        
        # 按开始时间倒序排列
        sorted_receipts = sorted(
            self.receipt_history,
            key=lambda r: r.start_time,
            reverse=True
        )
        
        return sorted_receipts[:limit]
    
    def generate_batch_report(self, receipt_ids: Optional[List[str]] = None) -> str:
        """
        生成批量修复报告
        
        Args:
            receipt_ids: 要包含的回执ID列表，None表示使用最近一次
            
        Returns:
            批量修复报告文本
        """
        if receipt_ids is None:
            # 使用最近一次回执
            latest = self.get_latest_receipt()
            if not latest:
                return "没有可用的修复回执"
            receipts = [latest]
        else:
            receipts = []
            for receipt_id in receipt_ids:
                receipt = self.get_receipt_by_id(receipt_id)
                if receipt:
                    receipts.append(receipt)
            
            if not receipts:
                return "没有找到指定的修复回执"
        
        # 生成合并报告
        lines = []
        lines.append("=" * 80)
        lines.append("批量修复报告")
        lines.append("=" * 80)
        lines.append(f"报告生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"包含回执数: {len(receipts)}")
        lines.append("")
        
        # 总体统计
        total_attempted = 0
        total_success = 0
        total_failed = 0
        all_modified_files = set()
        all_issue_types = {}
        
        for receipt in receipts:
            receipt.generate_summary()
            total_attempted += receipt.summary['total_attempted']
            total_success += receipt.summary['success']
            total_failed += receipt.summary['failed']
            
            for file in receipt.summary['modified_files']:
                all_modified_files.add(file)
            
            for issue_type, count in receipt.summary['issue_type_counts'].items():
                if issue_type not in all_issue_types:
                    all_issue_types[issue_type] = 0
                all_issue_types[issue_type] += count
        
        lines.append("总体统计:")
        lines.append(f"  总尝试修复数: {total_attempted}")
        lines.append(f"  总成功数: {total_success}")
        lines.append(f"  总失败数: {total_failed}")
        lines.append(f"  总成功率: {total_success / total_attempted:.1%}" if total_attempted > 0 else "  总成功率: N/A")
        lines.append(f"  总修改文件数: {len(all_modified_files)}")
        lines.append("")
        
        # 问题类型统计
        if all_issue_types:
            lines.append("处理的问题类型统计:")
            for issue_type, count in sorted(all_issue_types.items()):
                lines.append(f"  • {issue_type}: {count}个")
            lines.append("")
        
        # 修改的文件
        if all_modified_files:
            lines.append(f"修改的文件 ({len(all_modified_files)}个):")
            for file in sorted(list(all_modified_files)):
                lines.append(f"  • {os.path.basename(file)}")
            lines.append("")
        
        # 详细回执列表
        lines.append("详细回执列表:")
        for i, receipt in enumerate(receipts, 1):
            lines.append(f"  {i}. 会话ID: {receipt.session_id}")
            lines.append(f"     时间: {receipt.start_time}")
            lines.append(f"     尝试数: {receipt.summary['total_attempted']}")
            lines.append(f"     成功数: {receipt.summary['success']}")
            lines.append(f"     失败数: {receipt.summary['failed']}")
            lines.append(f"     修改文件数: {receipt.summary['modified_files_count']}")
            lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    # ==================== 修复能力判断 ====================
    
    def can_fix_issue(self, issue: HealthIssue) -> Tuple[bool, str]:
        """
        判断问题是否可以自动修复
        
        Returns:
            Tuple[是否可以修复, 说明消息]
        """
        # 可自动修复的问题类型
        auto_fixable_types = {
            IssueType.EMPTY_LABEL: "可删除空标签文件",
            IssueType.DUPLICATE_BOUNDING_BOX: "可删除重复框",
            IssueType.INVALID_BOUNDING_BOX: "可删除无效框（宽高<=0）",
            IssueType.BOUNDING_BOX_OUT_OF_BOUNDS: "可安全修正坐标到合法范围",
        }
        
        # 不可自动修复的问题类型（仅标记）
        manual_fix_types = {
            IssueType.CLASS_ID_OUT_OF_RANGE: "需要人工确认类别ID映射",
            IssueType.INVALID_LABEL_FORMAT: "需要人工修复标签格式",
        }
        
        if issue.issue_type in auto_fixable_types:
            return True, auto_fixable_types[issue.issue_type]
        elif issue.issue_type in manual_fix_types:
            return False, manual_fix_types[issue.issue_type]
        else:
            return False, "当前版本不支持自动修复此类型问题"
    
    def get_manual_fix_guidance(self, issue: HealthIssue) -> Dict[str, Any]:
        """
        获取人工修复指导
        
        Args:
            issue: 问题
            
        Returns:
            指导信息字典
        """
        guidance = {
            "issue_type": issue.issue_type.value,
            "file_name": issue.file_name,
            "file_path": issue.file_path,
            "message": issue.message,
            "suggestion": issue.suggestion,
            "can_auto_fix": False,
            "manual_steps": [],
            "jump_target": None
        }
        
        if issue.issue_type == IssueType.CLASS_ID_OUT_OF_RANGE:
            guidance["manual_steps"] = [
                "1. 打开标签文件查看类别ID",
                "2. 确认类别ID是否在有效范围内",
                "3. 如果类别ID错误，修改为正确值",
                "4. 如果类别定义需要更新，更新类别配置文件"
            ]
            guidance["reason"] = "类别ID映射需要人工确认，自动修复可能导致错误分类"
            
        elif issue.issue_type == IssueType.INVALID_LABEL_FORMAT:
            guidance["manual_steps"] = [
                "1. 打开标签文件查看错误行",
                "2. 检查YOLO格式是否正确（class_id center_x center_y width height）",
                "3. 修正格式错误的行",
                "4. 删除多余的空行或无效字符"
            ]
            guidance["reason"] = "标签格式错误需要人工检查，自动修复可能破坏数据"
        
        else:
            guidance["manual_steps"] = [
                "1. 打开相关文件检查问题",
                "2. 根据问题描述手动修复",
                "3. 保存文件后重新运行健康检查"
            ]
            guidance["reason"] = "此类型问题需要人工干预"
        
        # 设置跳转目标（如果可用）
        if issue.file_path:
            guidance["jump_target"] = issue.file_path
        
        return guidance
    
    # ==================== 核心修复方法 ====================
    
    def fix_empty_label(self, issue: HealthIssue) -> FixOperation:
        """修复空标签文件"""
        if not issue.file_path or not os.path.exists(issue.file_path):
            return FixOperation(
                issue=issue,
                fix_type="empty_label",
                result=FixResult.FAILED,
                message="标签文件不存在"
            )
        
        try:
            # 备份原始文件
            backup_path = self._create_backup(issue.file_path, "empty_label")
            
            # 删除空标签文件
            os.remove(issue.file_path)
            
            return FixOperation(
                issue=issue,
                fix_type="empty_label",
                result=FixResult.SUCCESS,
                message="已删除空标签文件",
                backup_path=backup_path,
                changes={"action": "delete", "file": issue.file_name, "file_path": issue.file_path}
            )
            
        except Exception as e:
            return FixOperation(
                issue=issue,
                fix_type="empty_label",
                result=FixResult.FAILED,
                message=f"删除文件失败: {str(e)}"
            )
    
    def fix_duplicate_boxes(self, issue: HealthIssue) -> FixOperation:
        """修复重复框"""
        if not issue.file_path or not os.path.exists(issue.file_path):
            return FixOperation(
                issue=issue,
                fix_type="duplicate_box",
                result=FixResult.FAILED,
                message="标签文件不存在"
            )
        
        try:
            # 备份原始文件
            backup_path = self._create_backup(issue.file_path, "duplicate_box")
            
            # 读取标签文件
            with open(issue.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 解析所有框
            boxes = []
            valid_lines = []
            removed_boxes = []  # 记录被删除的重复框
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        class_id = int(float(parts[0]))
                        center_x = round(float(parts[1]), 4)
                        center_y = round(float(parts[2]), 4)
                        width = round(float(parts[3]), 4)
                        height = round(float(parts[4]), 4)
                        
                        box_key = (class_id, center_x, center_y, width, height)
                        
                        # 检查是否重复
                        if box_key not in boxes:
                            boxes.append(box_key)
                            valid_lines.append(line)
                        else:
                            # 重复框，记录被删除的框
                            removed_boxes.append({
                                "line_number": line_num,
                                "class_id": class_id,
                                "center_x": center_x,
                                "center_y": center_y,
                                "width": width,
                                "height": height,
                                "original_line": line
                            })
                            continue
                    except ValueError:
                        # 格式错误，保留原始行
                        valid_lines.append(line)
                else:
                    # 格式错误，保留原始行
                    valid_lines.append(line)
            
            # 写入修复后的文件
            with open(issue.file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(valid_lines))
            
            removed_count = len(lines) - len(valid_lines)
            
            return FixOperation(
                issue=issue,
                fix_type="duplicate_box",
                result=FixResult.SUCCESS,
                message=f"已删除{removed_count}个重复框，保留{len(valid_lines)}个有效框",
                backup_path=backup_path,
                changes={
                    "original_lines": len(lines),
                    "remaining_lines": len(valid_lines),
                    "removed_duplicates": removed_count,
                    "removed_boxes_details": removed_boxes,
                    "file_path": issue.file_path,
                    "file_name": issue.file_name
                }
            )
            
        except Exception as e:
            return FixOperation(
                issue=issue,
                fix_type="duplicate_box",
                result=FixResult.FAILED,
                message=f"修复重复框失败: {str(e)}"
            )
    
    def fix_invalid_boxes(self, issue: HealthIssue) -> FixOperation:
        """修复无效框（宽高<=0）"""
        if not issue.file_path or not os.path.exists(issue.file_path):
            return FixOperation(
                issue=issue,
                fix_type="invalid_box",
                result=FixResult.FAILED,
                message="标签文件不存在"
            )
        
        try:
            # 备份原始文件
            backup_path = self._create_backup(issue.file_path, "invalid_box")
            
            # 读取标签文件
            with open(issue.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 解析并过滤无效框
            valid_lines = []
            removed_lines = []
            removed_boxes = []  # 记录被删除的无效框详细信息
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        class_id = int(float(parts[0]))
                        center_x = round(float(parts[1]), 4)
                        center_y = round(float(parts[2]), 4)
                        width = float(parts[3])
                        height = float(parts[4])
                        
                        # 检查宽高是否有效
                        if width > 0 and height > 0:
                            valid_lines.append(line)
                        else:
                            removed_lines.append(line_num)
                            removed_boxes.append({
                                "line_number": line_num,
                                "class_id": class_id,
                                "center_x": center_x,
                                "center_y": center_y,
                                "width": width,
                                "height": height,
                                "original_line": line,
                                "reason": "width<=0 or height<=0"
                            })
                    except ValueError:
                        # 格式错误，保留原始行（让其他检查器处理）
                        valid_lines.append(line)
                else:
                    # 格式错误，保留原始行
                    valid_lines.append(line)
            
            # 写入修复后的文件
            with open(issue.file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(valid_lines))
            
            removed_count = len(removed_lines)
            
            return FixOperation(
                issue=issue,
                fix_type="invalid_box",
                result=FixResult.SUCCESS,
                message=f"已删除{removed_count}个无效框（宽高<=0），保留{len(valid_lines)}个有效框",
                backup_path=backup_path,
                changes={
                    "original_lines": len(lines),
                    "remaining_lines": len(valid_lines),
                    "removed_invalid": removed_count,
                    "removed_line_numbers": removed_lines,
                    "removed_boxes_details": removed_boxes,
                    "file_path": issue.file_path,
                    "file_name": issue.file_name
                }
            )
            
        except Exception as e:
            return FixOperation(
                issue=issue,
                fix_type="invalid_box",
                result=FixResult.FAILED,
                message=f"修复无效框失败: {str(e)}"
            )
    
    def fix_out_of_bounds_boxes(self, issue: HealthIssue) -> FixOperation:
        """修复坐标越界的框"""
        if not issue.file_path or not os.path.exists(issue.file_path):
            return FixOperation(
                issue=issue,
                fix_type="out_of_bounds",
                result=FixResult.FAILED,
                message="标签文件不存在"
            )
        
        try:
            # 备份原始文件
            backup_path = self._create_backup(issue.file_path, "out_of_bounds")
            
            # 读取标签文件
            with open(issue.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 修复越界坐标
            fixed_lines = []
            fixed_count = 0
            fixed_boxes = []  # 记录被修正的框的详细信息
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    fixed_lines.append("")
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        class_id = parts[0]  # 保持原样
                        center_x = float(parts[1])
                        center_y = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        
                        # 修复越界坐标
                        fixed_coords = []
                        needs_fix = False
                        original_coords = [center_x, center_y, width, height]
                        fixed_coord_values = []
                        
                        for coord in original_coords:
                            # 安全修正到 [0, 1] 范围内
                            if coord < 0:
                                fixed_coord = 0.0
                                needs_fix = True
                            elif coord > 1:
                                fixed_coord = 1.0
                                needs_fix = True
                            else:
                                fixed_coord = coord
                            
                            fixed_coord_values.append(fixed_coord)
                            fixed_coords.append(f"{fixed_coord:.6f}")
                        
                        if needs_fix:
                            # 构建修复后的行
                            fixed_line = f"{class_id} {' '.join(fixed_coords)}"
                            fixed_lines.append(fixed_line)
                            fixed_count += 1
                            
                            # 记录修正详情
                            fixed_boxes.append({
                                "line_number": line_num,
                                "class_id": class_id,
                                "original_coords": {
                                    "center_x": center_x,
                                    "center_y": center_y,
                                    "width": width,
                                    "height": height
                                },
                                "fixed_coords": {
                                    "center_x": fixed_coord_values[0],
                                    "center_y": fixed_coord_values[1],
                                    "width": fixed_coord_values[2],
                                    "height": fixed_coord_values[3]
                                },
                                "original_line": line,
                                "fixed_line": fixed_line
                            })
                        else:
                            # 坐标正常，保持原样
                            fixed_lines.append(line)
                            
                    except ValueError:
                        # 格式错误，保持原样
                        fixed_lines.append(line)
                else:
                    # 格式错误，保持原样
                    fixed_lines.append(line)
            
            # 写入修复后的文件
            with open(issue.file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(fixed_lines))
            
            return FixOperation(
                issue=issue,
                fix_type="out_of_bounds",
                result=FixResult.SUCCESS,
                message=f"已修复{fixed_count}个越界坐标，总共{len(fixed_lines)}个框",
                backup_path=backup_path,
                changes={
                    "original_lines": len(lines),
                    "fixed_lines": fixed_count,
                    "action": "clamp_coordinates",
                    "fixed_boxes_details": fixed_boxes,
                    "file_path": issue.file_path,
                    "file_name": issue.file_name
                }
            )
            
        except Exception as e:
            return FixOperation(
                issue=issue,
                fix_type="out_of_bounds",
                result=FixResult.FAILED,
                message=f"修复越界坐标失败: {str(e)}"
            )
    
    # ==================== 批量修复方法 ====================
    
    def fix_single_issue(self, issue: HealthIssue) -> FixOperation:
        """
        修复单个问题
        
        Args:
            issue: 要修复的问题
            
        Returns:
            FixOperation 修复操作记录
        """
        # 检查是否可以修复
        can_fix, reason = self.can_fix_issue(issue)
        if not can_fix:
            operation = FixOperation(
                issue=issue,
                fix_type="unsupported",
                result=FixResult.NOT_SUPPORTED,
                message=reason
            )
            self.add_operation_to_session(operation)
            return operation
        
        # 根据问题类型调用相应的修复方法
        if issue.issue_type == IssueType.EMPTY_LABEL:
            operation = self.fix_empty_label(issue)
        elif issue.issue_type == IssueType.DUPLICATE_BOUNDING_BOX:
            operation = self.fix_duplicate_boxes(issue)
        elif issue.issue_type == IssueType.INVALID_BOUNDING_BOX:
            operation = self.fix_invalid_boxes(issue)
        elif issue.issue_type == IssueType.BOUNDING_BOX_OUT_OF_BOUNDS:
            operation = self.fix_out_of_bounds_boxes(issue)
        else:
            operation = FixOperation(
                issue=issue,
                fix_type="unknown",
                result=FixResult.NOT_SUPPORTED,
                message="未知问题类型，无法修复"
            )
        
        self.add_operation_to_session(operation)
        return operation
    
    def fix_issues_in_file(self, file_path: str, issue_types: List[IssueType] = None) -> List[FixOperation]:
        """
        修复指定文件中的所有问题
        
        Args:
            file_path: 文件路径
            issue_types: 要修复的问题类型列表（None表示所有可修复类型）
            
        Returns:
            List[FixOperation] 修复操作列表
        """
        # 先运行健康检查获取该文件的问题
        health_result = self.health_manager.run_full_health_check()
        
        # 筛选指定文件的问题
        file_issues = [issue for issue in health_result.issues 
                      if issue.file_path == file_path]
        
        if issue_types:
            file_issues = [issue for issue in file_issues 
                          if issue.issue_type in issue_types]
        
        # 修复每个问题
        results = []
        for issue in file_issues:
            result = self.fix_single_issue(issue)
            results.append(result)
        
        return results
    
    def fix_issues_by_type(self, issue_type: IssueType) -> List[FixOperation]:
        """
        修复所有指定类型的问题
        
        Args:
            issue_type: 要修复的问题类型
            
        Returns:
            List[FixOperation] 修复操作列表
        """
        # 先运行健康检查获取所有问题
        health_result = self.health_manager.run_full_health_check()
        
        # 筛选指定类型的问题
        target_issues = [issue for issue in health_result.issues 
                        if issue.issue_type == issue_type]
        
        # 修复每个问题
        results = []
        for issue in target_issues:
            result = self.fix_single_issue(issue)
            results.append(result)
        
        return results
    
    # ==================== 辅助方法 ====================
    
    def _create_backup(self, file_path: str, prefix: str) -> str:
        """
        创建文件备份
        
        Args:
            file_path: 原始文件路径
            prefix: 备份文件前缀
            
        Returns:
            备份文件路径
        """
        if not os.path.exists(file_path):
            return ""
        
        # 使用已创建的备份目录
        backup_dir = self.backup_dir
        
        # 生成备份文件名
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_name = f"{prefix}_{timestamp}_{filename}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # 复制文件
        shutil.copy2(file_path, backup_path)
        
        return backup_path
    
    def get_fix_summary(self) -> Dict[str, Any]:
        """
        获取修复操作摘要
        
        Returns:
            修复摘要字典
        """
        if not self.fix_history:
            return {
                "total_operations": 0,
                "success_count": 0,
                "summary": "尚未执行任何修复操作"
            }
        
        total = len(self.fix_history)
        success_count = sum(1 for op in self.fix_history 
                          if op.result == FixResult.SUCCESS)
        
        # 按类型统计
        by_type = {}
        by_result = {}
        
        for op in self.fix_history:
            # 按类型统计
            fix_type = op.fix_type
            if fix_type not in by_type:
                by_type[fix_type] = 0
            by_type[fix_type] += 1
            
            # 按结果统计
            result = op.result.value
            if result not in by_result:
                by_result[result] = 0
            by_result[result] += 1
        
        return {
            "total_operations": total,
            "success_count": success_count,
            "success_rate": success_count / total if total > 0 else 0,
            "by_type": by_type,
            "by_result": by_result,
            "latest_operation": self.fix_history[-1].message if self.fix_history else None
        }
    
    # ==================== 公共接口 ====================
    
    def fix_issue_with_confirmation(self, issue: HealthIssue, force: bool = False) -> FixOperation:
        """
        修复单个问题（带确认）
        
        Args:
            issue: 要修复的问题
            force: 是否跳过确认
            
        Returns:
            FixOperation 修复操作记录
        """
        # 检查是否可以修复
        can_fix, reason = self.can_fix_issue(issue)
        if not can_fix:
            return FixOperation(
                issue=issue,
                fix_type="unsupported",
                result=FixResult.NOT_SUPPORTED,
                message=reason
            )
        
        # 确认消息
        confirm_message = self._get_confirmation_message(issue)
        
        # 如果强制修复或确认通过，执行修复
        if force or self._confirm_fix(confirm_message):
            result = self.fix_single_issue(issue)
            self.fix_history.append(result)
            return result
        else:
            return FixOperation(
                issue=issue,
                fix_type="cancelled",
                result=FixResult.CANCELLED,
                message="用户取消了修复操作"
            )
    
    def _get_confirmation_message(self, issue: HealthIssue) -> str:
        """获取确认消息"""
        if issue.issue_type == IssueType.EMPTY_LABEL:
            return f"将删除空标签文件: {issue.file_name}\n\n此操作无法撤销，建议先备份。"
        elif issue.issue_type == IssueType.DUPLICATE_BOUNDING_BOX:
            return f"将删除文件中的重复标注框: {issue.file_name}\n\n系统会自动备份原始文件。"
        elif issue.issue_type == IssueType.INVALID_BOUNDING_BOX:
            return f"将删除无效标注框（宽高<=0）: {issue.file_name}\n\n系统会自动备份原始文件。"
        elif issue.issue_type == IssueType.BOUNDING_BOX_OUT_OF_BOUNDS:
            return f"将修正越界坐标到合法范围: {issue.file_name}\n\n系统会自动备份原始文件。"
        else:
            return f"将修复问题: {issue.message}\n\n文件: {issue.file_name}"
    
    def _confirm_fix(self, message: str) -> bool:
        """
        确认修复操作（需在UI中实现）
        
        Note: 此方法需要在UI层重写以显示确认对话框
        """
        # 基础实现：总是确认（UI层应重写此方法）
        # 在生产环境中，这里应该抛出异常或返回False，强制UI层实现
        return True
    
    def validate_fix(self, file_path: str) -> List[HealthIssue]:
        """
        验证修复后的文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            修复后仍然存在的问题列表
        """
        # 重新运行健康检查
        health_result = self.health_manager.run_full_health_check()
        
        # 筛选该文件的问题
        remaining_issues = [issue for issue in health_result.issues 
                          if issue.file_path == file_path]
        
        return remaining_issues
    
    # ==================== 批量修复预览方法 ====================
    
    def preview_fix_issues_in_file(self, file_path: str, issue_types: List[IssueType] = None) -> Dict[str, Any]:
        """
        预览修复指定文件中的所有问题（不实际执行修复）
        
        Args:
            file_path: 文件路径
            issue_types: 要修复的问题类型列表（None表示所有可修复类型）
            
        Returns:
            预览数据字典，包含：
            - total_issues: 总问题数
            - fixable_issues: 可修复的问题数
            - unfixable_issues: 不可修复的问题数
            - file_count: 涉及的文件数（始终为1）
            - fixable_by_type: 按类型统计的可修复问题
            - unfixable_by_type: 按类型统计的不可修复问题
            - sample_issues: 示例问题（最多5个）
        """
        # 先运行健康检查获取该文件的问题
        health_result = self.health_manager.run_full_health_check()
        
        # 筛选指定文件的问题
        file_issues = [issue for issue in health_result.issues 
                      if issue.file_path == file_path]
        
        if issue_types:
            file_issues = [issue for issue in file_issues 
                          if issue.issue_type in issue_types]
        
        # 统计修复情况
        fixable_issues = []
        unfixable_issues = []
        fixable_by_type = {}
        unfixable_by_type = {}
        
        for issue in file_issues:
            can_fix, reason = self.can_fix_issue(issue)
            if can_fix:
                fixable_issues.append(issue)
                issue_type = issue.issue_type.value
                if issue_type not in fixable_by_type:
                    fixable_by_type[issue_type] = 0
                fixable_by_type[issue_type] += 1
            else:
                unfixable_issues.append(issue)
                issue_type = issue.issue_type.value
                if issue_type not in unfixable_by_type:
                    unfixable_by_type[issue_type] = 0
                unfixable_by_type[issue_type] += 1
        
        # 获取示例问题（最多5个）
        sample_issues = []
        for issue in fixable_issues[:5]:
            sample_issues.append({
                "type": issue.issue_type.value,
                "file": issue.file_name,
                "message": issue.message[:100] + "..." if len(issue.message) > 100 else issue.message,
                "can_fix": True
            })
        
        for issue in unfixable_issues[:min(3, 5 - len(sample_issues))]:
            sample_issues.append({
                "type": issue.issue_type.value,
                "file": issue.file_name,
                "message": issue.message[:100] + "..." if len(issue.message) > 100 else issue.message,
                "can_fix": False
            })
        
        return {
            "total_issues": len(file_issues),
            "fixable_issues": len(fixable_issues),
            "unfixable_issues": len(unfixable_issues),
            "file_count": 1,
            "files": [file_path],
            "fixable_by_type": fixable_by_type,
            "unfixable_by_type": unfixable_by_type,
            "sample_issues": sample_issues,
            "file_name": os.path.basename(file_path) if file_path else "未知文件"
        }
    
    def preview_fix_all_fixable_issues(self, issue_types: List[IssueType] = None) -> Dict[str, Any]:
        """
        预览修复所有可自动修复的问题（不实际执行修复）
        
        Args:
            issue_types: 要修复的问题类型列表（None表示所有可修复类型）
            
        Returns:
            预览数据字典，包含：
            - total_issues: 总问题数
            - fixable_issues: 可修复的问题数
            - unfixable_issues: 不可修复的问题数
            - file_count: 涉及的文件数
            - files: 涉及的文件列表（最多10个）
            - fixable_by_type: 按类型统计的可修复问题
            - unfixable_by_type: 按类型统计的不可修复问题
            - sample_issues: 示例问题（最多10个）
        """
        # 先运行健康检查获取所有问题
        health_result = self.health_manager.run_full_health_check()
        
        # 如果没有指定问题类型，使用所有可自动修复的类型
        if issue_types is None:
            issue_types = [
                IssueType.EMPTY_LABEL,
                IssueType.DUPLICATE_BOUNDING_BOX,
                IssueType.INVALID_BOUNDING_BOX,
                IssueType.BOUNDING_BOX_OUT_OF_BOUNDS
            ]
        
        # 筛选指定类型的问题
        filtered_issues = [issue for issue in health_result.issues 
                          if issue.issue_type in issue_types]
        
        # 统计修复情况
        fixable_issues = []
        unfixable_issues = []
        fixable_by_type = {}
        unfixable_by_type = {}
        affected_files = set()
        
        for issue in filtered_issues:
            can_fix, reason = self.can_fix_issue(issue)
            if can_fix:
                fixable_issues.append(issue)
                issue_type = issue.issue_type.value
                if issue_type not in fixable_by_type:
                    fixable_by_type[issue_type] = 0
                fixable_by_type[issue_type] += 1
                if issue.file_path:
                    affected_files.add(issue.file_path)
            else:
                unfixable_issues.append(issue)
                issue_type = issue.issue_type.value
                if issue_type not in unfixable_by_type:
                    unfixable_by_type[issue_type] = 0
                unfixable_by_type[issue_type] += 1
                if issue.file_path:
                    affected_files.add(issue.file_path)
        
        # 获取示例问题（最多10个）
        sample_issues = []
        for issue in fixable_issues[:7]:
            sample_issues.append({
                "type": issue.issue_type.value,
                "file": issue.file_name,
                "message": issue.message[:80] + "..." if len(issue.message) > 80 else issue.message,
                "can_fix": True
            })
        
        for issue in unfixable_issues[:min(3, 10 - len(sample_issues))]:
            sample_issues.append({
                "type": issue.issue_type.value,
                "file": issue.file_name,
                "message": issue.message[:80] + "..." if len(issue.message) > 80 else issue.message,
                "can_fix": False
            })
        
        # 获取涉及的文件列表（最多10个）
        file_list = list(affected_files)[:10]
        file_names = [os.path.basename(f) for f in file_list]
        
        return {
            "total_issues": len(filtered_issues),
            "fixable_issues": len(fixable_issues),
            "unfixable_issues": len(unfixable_issues),
            "file_count": len(affected_files),
            "files": file_list,
            "file_names": file_names,
            "fixable_by_type": fixable_by_type,
            "unfixable_by_type": unfixable_by_type,
            "sample_issues": sample_issues
        }
    
    # ==================== 按图片批量修复方法 ====================
    
    def preview_fix_issues_by_image(self, image_name: str) -> Dict[str, Any]:
        """
        预览修复指定图片的所有可自动修复问题（不实际执行修复）
        
        Args:
            image_name: 图片名（不含扩展名）
            
        Returns:
            预览数据字典，包含：
            - image_name: 图片名
            - total_issues: 总问题数
            - fixable_issues: 可修复的问题数
            - unfixable_issues: 不可修复的问题数
            - fixable_by_type: 按类型统计的可修复问题
            - unfixable_by_type: 按类型统计的不可修复问题
            - issues: 所有问题详情列表
            - label_file_path: 标签文件路径（如有）
        """
        # 先运行健康检查获取所有问题
        health_result = self.health_manager.run_full_health_check()
        
        # 获取按图片分组的问题
        image_stats = self.health_manager.get_issues_by_image(health_result)
        
        if image_name not in image_stats:
            return {
                "image_name": image_name,
                "total_issues": 0,
                "fixable_issues": 0,
                "unfixable_issues": 0,
                "fixable_by_type": {},
                "unfixable_by_type": {},
                "issues": [],
                "label_file_path": None,
                "message": f"未找到图片 '{image_name}' 的问题"
            }
        
        stats = image_stats[image_name]
        issues = stats['issues']
        
        # 统计修复情况
        fixable_issues = []
        unfixable_issues = []
        fixable_by_type = {}
        unfixable_by_type = {}
        
        for issue in issues:
            can_fix, reason = self.can_fix_issue(issue)
            if can_fix:
                fixable_issues.append(issue)
                issue_type = issue.issue_type.value
                if issue_type not in fixable_by_type:
                    fixable_by_type[issue_type] = 0
                fixable_by_type[issue_type] += 1
            else:
                unfixable_issues.append(issue)
                issue_type = issue.issue_type.value
                if issue_type not in unfixable_by_type:
                    unfixable_by_type[issue_type] = 0
                unfixable_by_type[issue_type] += 1
        
        # 获取标签文件路径（从第一个问题中提取）
        label_file_path = None
        if issues and issues[0].file_path:
            # 假设所有问题都来自同一个文件
            label_file_path = issues[0].file_path
        
        return {
            "image_name": image_name,
            "total_issues": len(issues),
            "fixable_issues": len(fixable_issues),
            "unfixable_issues": len(unfixable_issues),
            "fixable_by_type": fixable_by_type,
            "unfixable_by_type": unfixable_by_type,
            "issues": issues,
            "fixable_issues_list": fixable_issues,
            "unfixable_issues_list": unfixable_issues,
            "label_file_path": label_file_path,
            "message": f"图片 '{image_name}' 共有 {len(issues)} 个问题，其中 {len(fixable_issues)} 个可自动修复"
        }
    
    def fix_issues_by_image(self, image_name: str, start_session: bool = True) -> List[FixOperation]:
        """
        修复指定图片的所有可自动修复问题
        
        Args:
            image_name: 图片名（不含扩展名）
            start_session: 是否开始新的修复会话
            
        Returns:
            List[FixOperation] 修复操作列表
        """
        # 获取预览数据
        preview_data = self.preview_fix_issues_by_image(image_name)
        
        if preview_data['fixable_issues'] == 0:
            # 没有可修复的问题
            return []
        
        # 如果需要，开始新的修复会话
        if start_session and not self.current_receipt:
            self.start_fix_session()
        
        # 修复每个可修复的问题
        results = []
        for issue in preview_data['fixable_issues_list']:
            result = self.fix_single_issue(issue)
            results.append(result)
        
        return results
    
    def fix_issues_by_image_with_preview(self, image_name: str) -> Tuple[Dict[str, Any], List[FixOperation]]:
        """
        按图片修复的完整流程：先预览，再修复（需在UI中调用确认）
        
        Args:
            image_name: 图片名（不含扩展名）
            
        Returns:
            Tuple[预览数据, 修复结果列表]
        """
        # 获取预览数据
        preview_data = self.preview_fix_issues_by_image(image_name)
        
        # 如果没有可修复的问题，直接返回
        if preview_data['fixable_issues'] == 0:
            return preview_data, []
        
        # 注意：这里不实际执行修复，需要UI层调用fix_issues_by_image
        return preview_data, []
    
    # ==================== 图片修复差异查看 ====================
    
    def get_image_fix_operations(self, image_name: str, session_id: Optional[str] = None) -> List[FixOperation]:
        """
        获取指定图片在修复会话中的操作记录
        
        Args:
            image_name: 图片名（不含扩展名）
            session_id: 修复会话ID，None表示所有会话
            
        Returns:
            List[FixOperation] 修复操作列表
        """
        operations = []
        
        if session_id:
            # 获取指定会话
            receipt = self.get_receipt_by_id(session_id)
            if receipt:
                for op in receipt.operations:
                    # 检查操作是否属于该图片
                    if op.issue.file_name and image_name in op.issue.file_name:
                        operations.append(op)
        else:
            # 获取所有会话
            for receipt in self.receipt_history:
                for op in receipt.operations:
                    if op.issue.file_name and image_name in op.issue.file_name:
                        operations.append(op)
        
        return operations
    
    def get_image_fix_diff(self, image_name: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定图片的修复差异详情
        
        Args:
            image_name: 图片名（不含扩展名）
            session_id: 修复会话ID，None表示最近一次会话
            
        Returns:
            差异详情字典，包含：
            - image_name: 图片名
            - session_id: 会话ID
            - label_file_path: 标签文件路径
            - total_operations: 总操作数
            - successful_operations: 成功操作数
            - failed_operations: 失败操作数
            - skipped_operations: 跳过操作数
            - deleted_boxes: 删除的框列表
            - fixed_coordinates: 修正的坐标列表
            - skipped_issues: 跳过的问题列表
            - operations: 原始操作列表
        """
        # 如果没有指定会话ID，使用最近一次
        if session_id is None:
            latest_receipt = self.get_latest_receipt()
            if not latest_receipt:
                return {
                    "image_name": image_name,
                    "session_id": None,
                    "message": "没有找到修复记录"
                }
            session_id = latest_receipt.session_id
        
        # 获取该图片的操作记录
        operations = self.get_image_fix_operations(image_name, session_id)
        
        if not operations:
            return {
                "image_name": image_name,
                "session_id": session_id,
                "message": f"图片 '{image_name}' 在该修复会话中没有修复操作"
            }
        
        # 获取标签文件路径
        label_file_path = None
        if operations and operations[0].issue.file_path:
            label_file_path = operations[0].issue.file_path
        
        # 统计操作结果
        total_ops = len(operations)
        successful_ops = [op for op in operations if op.result == FixResult.SUCCESS]
        failed_ops = [op for op in operations if op.result == FixResult.FAILED]
        skipped_ops = [op for op in operations if op.result == FixResult.SKIPPED or op.result == FixResult.NOT_SUPPORTED]
        
        # 提取差异详情
        deleted_boxes = []
        fixed_coordinates = []
        skipped_issues = []
        
        for op in operations:
            if op.result == FixResult.SUCCESS:
                # 成功修复的操作
                if op.fix_type == "empty_label":
                    deleted_boxes.append({
                        "type": "empty_label",
                        "file": op.issue.file_name,
                        "action": "删除空标签文件",
                        "details": op.changes
                    })
                elif op.fix_type == "duplicate_box":
                    if "removed_boxes_details" in op.changes:
                        for box in op.changes["removed_boxes_details"]:
                            deleted_boxes.append({
                                "type": "duplicate_box",
                                "class_id": box.get("class_id"),
                                "center_x": box.get("center_x"),
                                "center_y": box.get("center_y"),
                                "width": box.get("width"),
                                "height": box.get("height"),
                                "line_number": box.get("line_number"),
                                "reason": "重复框"
                            })
                elif op.fix_type == "invalid_box":
                    if "removed_boxes_details" in op.changes:
                        for box in op.changes["removed_boxes_details"]:
                            deleted_boxes.append({
                                "type": "invalid_box",
                                "class_id": box.get("class_id"),
                                "center_x": box.get("center_x"),
                                "center_y": box.get("center_y"),
                                "width": box.get("width"),
                                "height": box.get("height"),
                                "line_number": box.get("line_number"),
                                "reason": box.get("reason", "宽高<=0")
                            })
                elif op.fix_type == "out_of_bounds":
                    if "fixed_boxes_details" in op.changes:
                        for box in op.changes["fixed_boxes_details"]:
                            fixed_coordinates.append({
                                "type": "out_of_bounds",
                                "class_id": box.get("class_id"),
                                "original_coords": box.get("original_coords"),
                                "fixed_coords": box.get("fixed_coords"),
                                "line_number": box.get("line_number"),
                                "reason": "坐标越界修正"
                            })
            elif op.result in [FixResult.SKIPPED, FixResult.NOT_SUPPORTED]:
                # 跳过或不受支持的操作
                skipped_issues.append({
                    "type": op.issue.issue_type.value,
                    "file": op.issue.file_name,
                    "message": op.issue.message,
                    "suggestion": op.issue.suggestion,
                    "reason": op.message
                })
        
        return {
            "image_name": image_name,
            "session_id": session_id,
            "label_file_path": label_file_path,
            "total_operations": total_ops,
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "skipped_operations": len(skipped_ops),
            "deleted_boxes": deleted_boxes,
            "fixed_coordinates": fixed_coordinates,
            "skipped_issues": skipped_issues,
            "operations": operations,
            "receipt_time": None  # 将在下面填充
        }
    
    def get_image_fix_diff_summary(self, image_name: str, session_id: Optional[str] = None) -> str:
        """
        获取指定图片的修复差异摘要（文本格式）
        
        Args:
            image_name: 图片名（不含扩展名）
            session_id: 修复会话ID，None表示最近一次会话
            
        Returns:
            差异摘要文本
        """
        diff_data = self.get_image_fix_diff(image_name, session_id)
        
        if "message" in diff_data and diff_data["message"]:
            return diff_data["message"]
        
        lines = []
        lines.append("=" * 60)
        lines.append(f"图片修复差异报告 - {image_name}")
        lines.append("=" * 60)
        lines.append(f"修复会话: {diff_data['session_id']}")
        if diff_data['label_file_path']:
            lines.append(f"标签文件: {os.path.basename(diff_data['label_file_path'])}")
        lines.append("")
        
        lines.append("【修复操作统计】")
        lines.append(f"  总操作数: {diff_data['total_operations']}")
        lines.append(f"  成功操作: {diff_data['successful_operations']}")
        lines.append(f"  失败操作: {diff_data['failed_operations']}")
        lines.append(f"  跳过操作: {diff_data['skipped_operations']}")
        lines.append("")
        
        if diff_data['deleted_boxes']:
            lines.append(f"【删除的标注框 ({len(diff_data['deleted_boxes'])}个)】")
            for i, box in enumerate(diff_data['deleted_boxes'][:10], 1):
                lines.append(f"  {i}. 类型: {box['type']}")
                lines.append(f"     类别ID: {box.get('class_id', 'N/A')}")
                lines.append(f"     坐标: ({box.get('center_x', 'N/A')}, {box.get('center_y', 'N/A')})")
                lines.append(f"     宽高: {box.get('width', 'N/A')}×{box.get('height', 'N/A')}")
                lines.append(f"     行号: {box.get('line_number', 'N/A')}")
                lines.append(f"     原因: {box.get('reason', 'N/A')}")
            if len(diff_data['deleted_boxes']) > 10:
                lines.append(f"  还有{len(diff_data['deleted_boxes']) - 10}个删除框未显示...")
            lines.append("")
        
        if diff_data['fixed_coordinates']:
            lines.append(f"【修正的坐标 ({len(diff_data['fixed_coordinates'])}个)】")
            for i, fix in enumerate(diff_data['fixed_coordinates'][:10], 1):
                lines.append(f"  {i}. 类型: {fix['type']}")
                lines.append(f"     类别ID: {fix.get('class_id', 'N/A')}")
                orig = fix.get('original_coords', {})
                fixed = fix.get('fixed_coords', {})
                lines.append(f"     原始坐标: ({orig.get('center_x', 'N/A')}, {orig.get('center_y', 'N/A')})")
                lines.append(f"     修正后坐标: ({fixed.get('center_x', 'N/A')}, {fixed.get('center_y', 'N/A')})")
                lines.append(f"     行号: {fix.get('line_number', 'N/A')}")
                lines.append(f"     原因: {fix.get('reason', 'N/A')}")
            if len(diff_data['fixed_coordinates']) > 10:
                lines.append(f"  还有{len(diff_data['fixed_coordinates']) - 10}个修正坐标未显示...")
            lines.append("")
        
        if diff_data['skipped_issues']:
            lines.append(f"【跳过的问题 ({len(diff_data['skipped_issues'])}个)】")
            for i, issue in enumerate(diff_data['skipped_issues'][:5], 1):
                lines.append(f"  {i}. 类型: {issue['type']}")
                lines.append(f"     文件: {issue['file']}")
                lines.append(f"     问题: {issue['message'][:80]}{'...' if len(issue['message']) > 80 else ''}")
                lines.append(f"     原因: {issue['reason']}")
            if len(diff_data['skipped_issues']) > 5:
                lines.append(f"  还有{len(diff_data['skipped_issues']) - 5}个跳过问题未显示...")
            lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)

    def get_image_fix_report(self, image_name: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定图片的修复报告（结构化数据）
        
        Args:
            image_name: 图片名（不含扩展名）
            session_id: 修复会话ID，None表示最近一次会话
            
        Returns:
            修复报告字典，包含关键统计信息
        """
        # 获取修复差异数据
        diff_data = self.get_image_fix_diff(image_name, session_id)
        
        # 如果返回错误消息，直接返回
        if "message" in diff_data and diff_data["message"]:
            return diff_data
        
        # 收集涉及的问题类型
        issue_types = set()
        for op in diff_data.get("operations", []):
            issue_types.add(op.issue.issue_type.value)
        
        # 构建结构化报告
        report = {
            "image_name": diff_data["image_name"],
            "session_id": diff_data["session_id"],
            "label_file_path": diff_data["label_file_path"],
            "label_file_name": os.path.basename(diff_data["label_file_path"]) if diff_data["label_file_path"] else None,
            "total_operations": diff_data["total_operations"],
            "successful_operations": diff_data["successful_operations"],
            "failed_operations": diff_data["failed_operations"],
            "skipped_operations": diff_data["skipped_operations"],
            "issue_types": list(issue_types),
            "deleted_boxes_count": len(diff_data.get("deleted_boxes", [])),
            "fixed_coordinates_count": len(diff_data.get("fixed_coordinates", [])),
            "skipped_issues_count": len(diff_data.get("skipped_issues", [])),
            # AI复核预留字段
            "ai_suggestions": [],
            "ai_reviewed": False
        }
        
        return report

    def get_image_fix_history(self, image_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取指定图片的修复历史记录
        
        Args:
            image_name: 图片名（不含扩展名）
            limit: 返回的最大记录数
            
        Returns:
            修复历史记录列表，按时间倒序排列
        """
        import os
        from typing import List, Dict, Any
        
        history = []
        
        # 遍历所有回执，查找涉及该图片的操作
        for receipt in self.receipt_history:
            # 筛选涉及该图片的操作
            image_operations = []
            for op in receipt.operations:
                # 检查操作是否涉及该图片
                if op.issue.file_name and op.issue.file_name.startswith(image_name):
                    image_operations.append(op)
            
            if image_operations:
                # 统计本次修复的结果
                total = len(image_operations)
                success = sum(1 for op in image_operations if op.result == FixResult.SUCCESS)
                failed = sum(1 for op in image_operations if op.result == FixResult.FAILED)
                skipped = sum(1 for op in image_operations if op.result in [FixResult.SKIPPED, FixResult.NOT_SUPPORTED])
                
                # 收集修复类型
                fix_types = set()
                for op in image_operations:
                    fix_types.add(op.fix_type)
                
                history.append({
                    "session_id": receipt.session_id,
                    "start_time": receipt.start_time,
                    "end_time": receipt.end_time,
                    "total_operations": total,
                    "successful_operations": success,
                    "failed_operations": failed,
                    "skipped_operations": skipped,
                    "fix_types": list(fix_types),
                    "operations": image_operations  # 保留原始操作引用
                })
        
        # 按时间倒序排序（最新的在前）
        history.sort(key=lambda x: x["start_time"], reverse=True)
        
        # 限制返回数量
        return history[:limit]