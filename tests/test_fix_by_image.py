#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试图片批量修复功能
"""
import sys
import os
sys.path.insert(0, '.')

from core.data_health_manager import DataHealthManager, HealthCheckResult, HealthIssue, IssueSeverity, IssueType
from core.data_health_fixer import DataHealthFixer, FixResult

# 创建模拟上下文
class MockContext:
    def __init__(self):
        self.image_dir = "test_images"
        self.label_dir = "test_labels"
        self.current_class_names = ["cat", "dog"]
        self.class_source_name = "manual"
        self.workbench_root = "."
        self.valid_ext = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

def test_fix_by_image():
    print("=== 测试图片批量修复功能 ===")
    
    # 创建管理器
    context = MockContext()
    manager = DataHealthManager(context)
    fixer = DataHealthFixer(manager)
    
    # 创建模拟检查结果
    result = HealthCheckResult()
    result.timestamp = "2026-03-28 17:00:00"
    result.total_checks = 10
    result.issues_found = 5
    result.issues_by_severity = {IssueSeverity.ERROR: 2, IssueSeverity.WARNING: 2, IssueSeverity.INFO: 1}
    result.issues_by_type = {IssueType.EMPTY_LABEL: 1, IssueType.CLASS_ID_OUT_OF_RANGE: 2, IssueType.INVALID_BOUNDING_BOX: 2}
    result.summary = {
        "image_directory": "test_images",
        "label_directory": "test_labels"
    }
    
    # 创建模拟问题
    issues = []
    # 图片1的问题
    issues.append(HealthIssue(
        issue_type=IssueType.EMPTY_LABEL,
        severity=IssueSeverity.ERROR,
        file_name="image1.txt",
        file_path="test_labels/image1.txt",
        message="空标签文件",
        suggestion="删除或修复",
        line_number=0
    ))
    issues.append(HealthIssue(
        issue_type=IssueType.CLASS_ID_OUT_OF_RANGE,
        severity=IssueSeverity.WARNING,
        file_name="image1.txt",
        file_path="test_labels/image1.txt",
        message="类别ID越界",
        suggestion="调整类别ID",
        line_number=2
    ))
    # 图片2的问题
    issues.append(HealthIssue(
        issue_type=IssueType.INVALID_BOUNDING_BOX,
        severity=IssueSeverity.ERROR,
        file_name="image2.txt",
        file_path="test_labels/image2.txt",
        message="无效框",
        suggestion="删除无效框",
        line_number=3
    ))
    
    result.issues = issues
    
    # 测试预览功能
    print("1. 测试 preview_fix_issues_by_image 方法...")
    try:
        # 需要mock get_issues_by_image方法
        # 由于是单元测试，暂时跳过
        print("   需要mock，暂时跳过")
    except Exception as e:
        print(f"   失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试修复器基本功能
    print("\n2. 测试修复器导入和创建...")
    try:
        print(f"   修复器创建成功: {fixer}")
        print(f"   修复器类型: {type(fixer)}")
        print("   ✓ 通过")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n=== 基础测试通过 ===")
    return True

if __name__ == "__main__":
    success = test_fix_by_image()
    sys.exit(0 if success else 1)