#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
data_health_manager.py - 数据集健康检查与整理管理器

职责：执行数据集健康检查，识别问题，提供整理建议。
目标：为训练前数据质量提供保障，作为数据整理中心的核心模块。

设计原则：
1. 专注于数据检查逻辑，不涉及UI
2. 通过 WorkbenchContext 访问当前数据集状态
3. 提供详细的检查结果和修复建议
4. 为后续扩展（自动修复、批量操作）预留接口
"""

import os
import json
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class IssueSeverity(Enum):
    """问题严重程度"""
    INFO = "info"        # 信息性提示
    WARNING = "warning"  # 警告，可能影响训练
    ERROR = "error"      # 错误，必须修复


class IssueType(Enum):
    """问题类型"""
    DIRECTORY_MISSING = "directory_missing"          # 目录不存在
    FILES_COUNT_MISMATCH = "files_count_mismatch"    # 文件数量不匹配
    MISSING_LABEL = "missing_label"                  # 图片缺少对应标签
    MISSING_IMAGE = "missing_image"                  # 标签缺少对应图片
    EMPTY_LABEL = "empty_label"                      # 标签文件为空
    INVALID_LABEL_FORMAT = "invalid_label_format"    # 标签格式错误
    CLASS_ID_OUT_OF_RANGE = "class_id_out_of_range"  # 类别ID超出范围
    BOUNDING_BOX_OUT_OF_BOUNDS = "bounding_box_out_of_bounds"  # 框坐标越界
    INVALID_BOUNDING_BOX = "invalid_bounding_box"    # 无效框（宽高<=0）
    DUPLICATE_BOUNDING_BOX = "duplicate_bounding_box"  # 重复框
    DUPLICATE_FILENAME = "duplicate_filename"        # 重复文件名
    UNSUPPORTED_IMAGE_FORMAT = "unsupported_image_format"  # 不支持的图片格式
    CORRUPTED_IMAGE = "corrupted_image"              # 损坏的图片文件


@dataclass
class HealthIssue:
    """健康检查问题"""
    issue_type: IssueType
    severity: IssueSeverity
    file_path: str = ""                # 相关文件路径
    file_name: str = ""                # 相关文件名
    message: str = ""                  # 问题描述
    suggestion: str = ""               # 修复建议
    line_number: int = 0               # 对于标签文件，出错的行号
    details: Dict[str, Any] = field(default_factory=dict)  # 额外详情


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    total_checks: int = 0                          # 检查项总数
    issues_found: int = 0                          # 发现的问题数
    issues_by_severity: Dict[IssueSeverity, int] = field(default_factory=lambda: {
        IssueSeverity.INFO: 0,
        IssueSeverity.WARNING: 0,
        IssueSeverity.ERROR: 0
    })
    issues_by_type: Dict[IssueType, int] = field(default_factory=dict)  # 按类型统计
    issues: List[HealthIssue] = field(default_factory=list)  # 详细问题列表
    summary: Dict[str, Any] = field(default_factory=dict)    # 汇总统计
    timestamp: str = ""                            # 检查时间


class DataHealthManager:
    """数据集健康检查管理器"""
    
    def __init__(self, context):
        """
        初始化管理器
        
        Args:
            context: WorkbenchContext 实例
        """
        self.context = context
        self._valid_ext = context.valid_ext
    
    # ==================== 基础检查方法 ====================
    
    def check_directory_exists(self) -> List[HealthIssue]:
        """检查目录是否存在"""
        issues = []
        
        # 检查图片目录
        if not self.context.image_dir or not os.path.isdir(self.context.image_dir):
            issues.append(HealthIssue(
                issue_type=IssueType.DIRECTORY_MISSING,
                severity=IssueSeverity.ERROR,
                file_path=self.context.image_dir or "",
                message="图片目录不存在或无法访问",
                suggestion="请检查 config.json 中的 image_dir 设置"
            ))
        
        # 检查标签目录
        if not self.context.label_dir or not os.path.isdir(self.context.label_dir):
            issues.append(HealthIssue(
                issue_type=IssueType.DIRECTORY_MISSING,
                severity=IssueSeverity.ERROR,
                file_path=self.context.label_dir or "",
                message="标签目录不存在或无法访问",
                suggestion="请检查 config.json 中的 label_dir 设置，或手动创建目录"
            ))
        
        return issues
    
    def get_image_files(self) -> List[str]:
        """获取图片文件列表"""
        if not self.context.image_dir or not os.path.isdir(self.context.image_dir):
            return []
        
        image_files = []
        for f in os.listdir(self.context.image_dir):
            if f.lower().endswith(self._valid_ext):
                image_files.append(f)
        
        return sorted(image_files)
    
    def get_label_files(self) -> List[str]:
        """获取标签文件列表"""
        if not self.context.label_dir or not os.path.isdir(self.context.label_dir):
            return []
        
        label_files = []
        for f in os.listdir(self.context.label_dir):
            if f.lower().endswith('.txt'):
                label_files.append(f)
        
        return sorted(label_files)
    
    def check_file_counts(self, image_files: List[str], label_files: List[str]) -> List[HealthIssue]:
        """检查文件数量"""
        issues = []
        
        image_count = len(image_files)
        label_count = len(label_files)
        
        if image_count == 0:
            issues.append(HealthIssue(
                issue_type=IssueType.FILES_COUNT_MISMATCH,
                severity=IssueSeverity.ERROR,
                message="图片目录中没有找到任何图片文件",
                suggestion=f"请确认图片目录中有支持的图片格式: {', '.join(self._valid_ext)}"
            ))
        
        if image_count != label_count:
            issues.append(HealthIssue(
                issue_type=IssueType.FILES_COUNT_MISMATCH,
                severity=IssueSeverity.WARNING,
                message=f"图片数量 ({image_count}) 与标签数量 ({label_count}) 不匹配",
                suggestion="可能存在缺失的配对文件，建议运行详细配对检查"
            ))
        
        return issues
    
    def check_file_pairing(self, image_files: List[str], label_files: List[str]) -> List[HealthIssue]:
        """检查图片与标签的配对关系"""
        issues = []
        
        # 提取文件名（不带扩展名）
        image_bases = {os.path.splitext(f)[0]: f for f in image_files}
        label_bases = {os.path.splitext(f)[0]: f for f in label_files}
        
        # 检查缺失标签的图片
        missing_labels = image_bases.keys() - label_bases.keys()
        for base in sorted(missing_labels):
            issues.append(HealthIssue(
                issue_type=IssueType.MISSING_LABEL,
                severity=IssueSeverity.WARNING,
                file_name=image_bases[base],
                file_path=os.path.join(self.context.image_dir, image_bases[base]) if self.context.image_dir else "",
                message=f"图片 '{image_bases[base]}' 缺少对应的标签文件",
                suggestion="可以为该图片创建标签文件，或删除该图片"
            ))
        
        # 检查缺失图片的标签
        missing_images = label_bases.keys() - image_bases.keys()
        for base in sorted(missing_images):
            issues.append(HealthIssue(
                issue_type=IssueType.MISSING_IMAGE,
                severity=IssueSeverity.WARNING,
                file_name=label_bases[base],
                file_path=os.path.join(self.context.label_dir, label_bases[base]) if self.context.label_dir else "",
                message=f"标签文件 '{label_bases[base]}' 缺少对应的图片文件",
                suggestion="可以为该标签创建图片文件，或删除该标签文件"
            ))
        
        return issues
    
    def check_label_files_content(self, label_files: List[str]) -> List[HealthIssue]:
        """检查标签文件内容"""
        issues = []
        
        if not self.context.label_dir:
            return issues
        
        for label_file in label_files:
            label_path = os.path.join(self.context.label_dir, label_file)
            
            try:
                # 检查文件是否为空
                if os.path.getsize(label_path) == 0:
                    issues.append(HealthIssue(
                        issue_type=IssueType.EMPTY_LABEL,
                        severity=IssueSeverity.INFO,
                        file_name=label_file,
                        file_path=label_path,
                        message=f"标签文件 '{label_file}' 为空",
                        suggestion="可以删除该文件，或为其添加标注"
                    ))
                    continue
                
                # 读取并检查每一行
                with open(label_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 用于检测重复框的集合（基础版：检查完全相同的框）
                seen_boxes = set()
                box_positions = {}  # 记录框的位置（行号）
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split()
                    
                    # 检查格式是否正确（至少5个字段）
                    if len(parts) < 5:
                        issues.append(HealthIssue(
                            issue_type=IssueType.INVALID_LABEL_FORMAT,
                            severity=IssueSeverity.ERROR,
                            file_name=label_file,
                            file_path=label_path,
                            message=f"标签文件 '{label_file}' 第 {line_num} 行格式错误",
                            suggestion="YOLO格式应为: class_id center_x center_y width height",
                            line_number=line_num,
                            details={"line_content": line, "parts_count": len(parts)}
                        ))
                        continue
                    
                    # 检查类别ID
                    try:
                        class_id = int(float(parts[0]))
                        if self.context.current_class_names:
                            if class_id < 0 or class_id >= len(self.context.current_class_names):
                                issues.append(HealthIssue(
                                    issue_type=IssueType.CLASS_ID_OUT_OF_RANGE,
                                    severity=IssueSeverity.ERROR,
                                    file_name=label_file,
                                    file_path=label_path,
                                    message=f"标签文件 '{label_file}' 第 {line_num} 行类别ID {class_id} 超出范围",
                                    suggestion=f"有效类别ID范围: 0-{len(self.context.current_class_names)-1}",
                                    line_number=line_num,
                                    details={"class_id": class_id, "max_class_id": len(self.context.current_class_names)-1}
                                ))
                    except ValueError:
                        issues.append(HealthIssue(
                            issue_type=IssueType.INVALID_LABEL_FORMAT,
                            severity=IssueSeverity.ERROR,
                            file_name=label_file,
                            file_path=label_path,
                            message=f"标签文件 '{label_file}' 第 {line_num} 行类别ID不是有效数字",
                            suggestion="类别ID应为整数或浮点数",
                            line_number=line_num,
                            details={"class_id_str": parts[0]}
                        ))
                        continue  # 类别ID错误，跳过坐标检查
                    
                    # 检查坐标值
                    try:
                        # 解析坐标值
                        center_x = float(parts[1])
                        center_y = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])
                        
                        # 检查坐标是否在有效范围内
                        for i, (val, name) in enumerate(zip([center_x, center_y, width, height], 
                                                          ["center_x", "center_y", "width", "height"]), 1):
                            if val < 0 or val > 1:
                                issues.append(HealthIssue(
                                    issue_type=IssueType.BOUNDING_BOX_OUT_OF_BOUNDS,
                                    severity=IssueSeverity.WARNING,
                                    file_name=label_file,
                                    file_path=label_path,
                                    message=f"标签文件 '{label_file}' 第 {line_num} 行{name}值 {val:.4f} 超出范围",
                                    suggestion="YOLO格式坐标应在 0-1 范围内",
                                    line_number=line_num,
                                    details={"value": val, "coordinate_type": name}
                                ))
                        
                        # 检查框宽高是否有效
                        if width <= 0 or height <= 0:
                            issues.append(HealthIssue(
                                issue_type=IssueType.INVALID_BOUNDING_BOX,
                                severity=IssueSeverity.ERROR,
                                file_name=label_file,
                                file_path=label_path,
                                message=f"标签文件 '{label_file}' 第 {line_num} 行框宽高无效 (width={width:.4f}, height={height:.4f})",
                                suggestion="框的宽度和高度必须大于0",
                                line_number=line_num,
                                details={"width": width, "height": height}
                            ))
                        
                        # 检查重复框（基础版：检查完全相同的框）
                        box_key = (class_id, round(center_x, 4), round(center_y, 4), round(width, 4), round(height, 4))
                        if box_key in seen_boxes:
                            first_line = box_positions[box_key]
                            issues.append(HealthIssue(
                                issue_type=IssueType.DUPLICATE_BOUNDING_BOX,
                                severity=IssueSeverity.WARNING,
                                file_name=label_file,
                                file_path=label_path,
                                message=f"标签文件 '{label_file}' 第 {line_num} 行与第 {first_line} 行的框完全相同",
                                suggestion="检查是否为标注错误，可以删除其中一个重复框",
                                line_number=line_num,
                                details={"class_id": class_id, "first_line": first_line}
                            ))
                        else:
                            seen_boxes.add(box_key)
                            box_positions[box_key] = line_num
                    
                    except ValueError:
                        issues.append(HealthIssue(
                            issue_type=IssueType.INVALID_LABEL_FORMAT,
                            severity=IssueSeverity.ERROR,
                            file_name=label_file,
                            file_path=label_path,
                            message=f"标签文件 '{label_file}' 第 {line_num} 行坐标值不是有效数字",
                            suggestion="坐标值应为浮点数",
                            line_number=line_num,
                            details={"parts": parts[1:5]}
                        ))
            
            except Exception as e:
                issues.append(HealthIssue(
                    issue_type=IssueType.INVALID_LABEL_FORMAT,
                    severity=IssueSeverity.ERROR,
                    file_name=label_file,
                    file_path=label_path,
                    message=f"读取标签文件 '{label_file}' 时发生错误",
                    suggestion="请检查文件权限和编码格式",
                    details={"error": str(e)}
                ))
        
        return issues
    
    def check_duplicate_filenames(self, image_files: List[str], label_files: List[str]) -> List[HealthIssue]:
        """检查重复文件名"""
        issues = []
        
        # 检查图片文件中的重复（考虑大小写不敏感）
        seen_images = {}
        for img in image_files:
            lower = img.lower()
            if lower in seen_images:
                issues.append(HealthIssue(
                    issue_type=IssueType.DUPLICATE_FILENAME,
                    severity=IssueSeverity.WARNING,
                    file_name=img,
                    message=f"图片文件名 '{img}' 与 '{seen_images[lower]}' 重复（大小写不敏感）",
                    suggestion="重命名其中一个文件以避免混淆"
                ))
            else:
                seen_images[lower] = img
        
        # 检查标签文件中的重复
        seen_labels = {}
        for lbl in label_files:
            lower = lbl.lower()
            if lower in seen_labels:
                issues.append(HealthIssue(
                    issue_type=IssueType.DUPLICATE_FILENAME,
                    severity=IssueSeverity.WARNING,
                    file_name=lbl,
                    message=f"标签文件名 '{lbl}' 与 '{seen_labels[lower]}' 重复（大小写不敏感）",
                    suggestion="重命名其中一个文件以避免混淆"
                ))
            else:
                seen_labels[lower] = lbl
        
        return issues
    
    # ==================== 主检查方法 ====================
    
    def run_full_health_check(self) -> HealthCheckResult:
        """
        执行完整的数据集健康检查
        
        Returns:
            HealthCheckResult 包含所有检查结果
        """
        from datetime import datetime
        
        result = HealthCheckResult()
        result.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 执行各项检查
        all_issues = []
        
        # 1. 目录检查
        all_issues.extend(self.check_directory_exists())
        
        # 如果目录有问题，提前返回
        has_critical_dir_issue = any(
            issue.severity == IssueSeverity.ERROR and 
            issue.issue_type == IssueType.DIRECTORY_MISSING
            for issue in all_issues
        )
        
        if has_critical_dir_issue:
            result.total_checks = 1
            result.issues = all_issues
            self._update_result_statistics(result)
            return result
        
        # 获取文件列表
        image_files = self.get_image_files()
        label_files = self.get_label_files()
        
        # 2. 文件数量检查
        all_issues.extend(self.check_file_counts(image_files, label_files))
        
        # 3. 文件配对检查
        all_issues.extend(self.check_file_pairing(image_files, label_files))
        
        # 4. 标签内容检查
        all_issues.extend(self.check_label_files_content(label_files))
        
        # 5. 重复文件名检查
        all_issues.extend(self.check_duplicate_filenames(image_files, label_files))
        
        # 更新结果统计
        result.total_checks = 6  # 目录、数量、配对、标签内容、重复、汇总
        result.issues = all_issues
        self._update_result_statistics(result)
        
        # 添加汇总信息
        result.summary = {
            "image_directory": self.context.image_dir or "未设置",
            "label_directory": self.context.label_dir or "未设置",
            "image_files_count": len(image_files),
            "label_files_count": len(label_files),
            "valid_image_extensions": self._valid_ext,
            "current_class_names_count": len(self.context.current_class_names),
            "current_class_names_source": self.context.class_source_name,
        }
        
        return result
    
    def _update_result_statistics(self, result: HealthCheckResult) -> None:
        """更新结果统计信息"""
        result.issues_found = len(result.issues)
        
        # 按严重程度统计
        for issue in result.issues:
            result.issues_by_severity[issue.severity] += 1
            
            # 按类型统计
            if issue.issue_type not in result.issues_by_type:
                result.issues_by_type[issue.issue_type] = 0
            result.issues_by_type[issue.issue_type] += 1
    
    # ==================== 导出与报告 ====================
    
    def export_report_txt(self, result: HealthCheckResult, output_path: str) -> bool:
        """导出检查报告为TXT格式"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("数据集健康检查报告\n")
                f.write("=" * 60 + "\n")
                f.write(f"检查时间: {result.timestamp}\n")
                f.write(f"图片目录: {result.summary.get('image_directory', '未设置')}\n")
                f.write(f"标签目录: {result.summary.get('label_directory', '未设置')}\n")
                f.write(f"图片数量: {result.summary.get('image_files_count', 0)}\n")
                f.write(f"标签数量: {result.summary.get('label_files_count', 0)}\n")
                f.write(f"类别数量: {result.summary.get('current_class_names_count', 0)}\n")
                f.write(f"类别来源: {result.summary.get('current_class_names_source', '未知')}\n")
                f.write("\n")
                
                f.write("检查结果汇总:\n")
                f.write(f"  检查项总数: {result.total_checks}\n")
                f.write(f"  发现问题数: {result.issues_found}\n")
                f.write(f"  信息提示: {result.issues_by_severity[IssueSeverity.INFO]}\n")
                f.write(f"  警告: {result.issues_by_severity[IssueSeverity.WARNING]}\n")
                f.write(f"  错误: {result.issues_by_severity[IssueSeverity.ERROR]}\n")
                f.write("\n")
                
                if result.issues_found > 0:
                    f.write("详细问题列表:\n")
                    f.write("-" * 60 + "\n")
                    
                    # 按严重程度分组
                    for severity in [IssueSeverity.ERROR, IssueSeverity.WARNING, IssueSeverity.INFO]:
                        severity_issues = [i for i in result.issues if i.severity == severity]
                        if not severity_issues:
                            continue
                            
                        severity_name = severity.value.upper()
                        f.write(f"\n{severity_name}级别问题 ({len(severity_issues)}个):\n")
                        
                        for i, issue in enumerate(severity_issues, 1):
                            f.write(f"\n{i}. [{issue.issue_type.value}] {issue.message}\n")
                            if issue.file_name:
                                f.write(f"   文件: {issue.file_name}\n")
                            if issue.file_path:
                                f.write(f"   路径: {issue.file_path}\n")
                            if issue.line_number > 0:
                                f.write(f"   行号: {issue.line_number}\n")
                            if issue.suggestion:
                                f.write(f"   建议: {issue.suggestion}\n")
                            if issue.details:
                                f.write(f"   详情: {issue.details}\n")
                
                else:
                    f.write("✅ 数据集健康检查通过！未发现任何问题。\n")
                
                f.write("\n" + "=" * 60 + "\n")
                f.write("报告结束\n")
            
            return True
            
        except Exception as e:
            print(f"导出报告失败: {e}")
            return False
    
    def export_report_json(self, result: HealthCheckResult, output_path: str) -> bool:
        """导出检查报告为JSON格式"""
        try:
            # 转换为可序列化的字典
            report = {
                "timestamp": result.timestamp,
                "summary": result.summary,
                "statistics": {
                    "total_checks": result.total_checks,
                    "issues_found": result.issues_found,
                    "issues_by_severity": {
                        severity.value: count 
                        for severity, count in result.issues_by_severity.items()
                    },
                    "issues_by_type": {
                        issue_type.value: count 
                        for issue_type, count in result.issues_by_type.items()
                    }
                },
                "issues": [
                    {
                        "issue_type": issue.issue_type.value,
                        "severity": issue.severity.value,
                        "file_name": issue.file_name,
                        "file_path": issue.file_path,
                        "message": issue.message,
                        "suggestion": issue.suggestion,
                        "line_number": issue.line_number,
                        "details": issue.details
                    }
                    for issue in result.issues
                ]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"导出JSON报告失败: {e}")
            return False
    
    # ==================== 按图片汇总统计 ====================
    
    def get_issues_by_image(self, result: HealthCheckResult) -> Dict[str, Dict[str, Any]]:
        """
        按图片汇总问题统计
        
        Args:
            result: 健康检查结果
            
        Returns:
            字典，键为图片名（不含扩展名），值为统计信息：
            - total: 问题总数
            - errors: 错误数
            - warnings: 警告数
            - infos: 信息数
            - auto_fixable: 可自动修复数
            - manual_fix: 需人工处理数
            - issues: 该图片下的所有问题列表
        """
        from core.data_health_fixer import DataHealthFixer
        
        # 初始化修复器用于判断可修复性
        fixer = DataHealthFixer(self)
        
        # 按图片名分组
        image_stats = {}
        
        for issue in result.issues:
            # 获取图片名（如果问题关联的是标签文件，需要转换为图片名）
            image_name = None
            
            if issue.file_name:
                # 检查文件扩展名
                if any(issue.file_name.lower().endswith(ext) for ext in self._valid_ext):
                    # 是图片文件
                    image_name = os.path.splitext(issue.file_name)[0]
                elif issue.file_name.lower().endswith('.txt'):
                    # 是标签文件，转换为对应的图片名（假设同名）
                    image_name = os.path.splitext(issue.file_name)[0]
                else:
                    # 其他文件，尝试提取基本名
                    image_name = os.path.splitext(issue.file_name)[0]
            else:
                # 没有文件名的问题，跳过
                continue
            
            if not image_name:
                continue
            
            # 初始化图片统计
            if image_name not in image_stats:
                image_stats[image_name] = {
                    'image_name': image_name,
                    'total': 0,
                    'errors': 0,
                    'warnings': 0,
                    'infos': 0,
                    'auto_fixable': 0,
                    'manual_fix': 0,
                    'issues': []
                }
            
            # 更新统计
            stats = image_stats[image_name]
            stats['total'] += 1
            stats['issues'].append(issue)
            
            # 按严重程度统计
            if issue.severity == IssueSeverity.ERROR:
                stats['errors'] += 1
            elif issue.severity == IssueSeverity.WARNING:
                stats['warnings'] += 1
            elif issue.severity == IssueSeverity.INFO:
                stats['infos'] += 1
            
            # 判断是否可自动修复
            can_fix, _ = fixer.can_fix_issue(issue)
            if can_fix:
                stats['auto_fixable'] += 1
            else:
                stats['manual_fix'] += 1
        
        return image_stats
    
    def get_image_summary_report(self, result: HealthCheckResult) -> List[Dict[str, Any]]:
        """
        获取按图片汇总的统计报告（用于UI展示）
        
        Args:
            result: 健康检查结果
            
        Returns:
            排序后的图片统计列表，每项包含：
            - image_name: 图片名
            - total: 问题总数
            - errors: 错误数
            - warnings: 警告数
            - infos: 信息数
            - auto_fixable: 可自动修复数
            - manual_fix: 需人工处理数
        """
        image_stats = self.get_issues_by_image(result)
        
        # 转换为列表并按问题总数降序排列
        summary_list = []
        for image_name, stats in image_stats.items():
            summary_list.append({
                'image_name': stats['image_name'],
                'total': stats['total'],
                'errors': stats['errors'],
                'warnings': stats['warnings'],
                'infos': stats['infos'],
                'auto_fixable': stats['auto_fixable'],
                'manual_fix': stats['manual_fix']
            })
        
        # 默认按问题总数降序排列
        summary_list.sort(key=lambda x: x['total'], reverse=True)
        
        return summary_list
    
    # ==================== 快速检查方法 ====================
    
    def quick_health_check(self) -> Tuple[bool, str]:
        """
        快速健康检查（返回是否通过和简要消息）
        
        Returns:
            Tuple[是否通过, 消息]
        """
        # 检查目录
        dir_issues = self.check_directory_exists()
        if any(issue.severity == IssueSeverity.ERROR for issue in dir_issues):
            return False, "目录配置错误，请检查config.json"
        
        # 获取文件列表
        image_files = self.get_image_files()
        label_files = self.get_label_files()
        
        if not image_files:
            return False, "图片目录中没有找到任何图片文件"
        
        # 检查基本配对
        image_bases = {os.path.splitext(f)[0] for f in image_files}
        label_bases = {os.path.splitext(f)[0] for f in label_files}
        
        missing_labels = len(image_bases - label_bases)
        missing_images = len(label_bases - image_bases)
        
        if missing_labels > 0 or missing_images > 0:
            msg_parts = []
            if missing_labels > 0:
                msg_parts.append(f"{missing_labels}张图片缺少标签")
            if missing_images > 0:
                msg_parts.append(f"{missing_images}个标签缺少图片")
            return False, f"文件配对不完整: {', '.join(msg_parts)}"
        
        return True, f"数据集基本健康: {len(image_files)}张图片, {len(label_files)}个标签"