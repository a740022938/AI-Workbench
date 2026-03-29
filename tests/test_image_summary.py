#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试图片汇总功能
"""
import sys
import os
sys.path.insert(0, '.')

from core.data_health_manager import DataHealthManager, HealthCheckResult, HealthIssue, IssueSeverity, IssueType

# 创建模拟上下文
class MockContext:
    def __init__(self):
        self.image_dir = "test_images"
        self.label_dir = "test_labels"
        self.current_class_names = ["cat", "dog"]
        self.class_source_name = "manual"
        self.workbench_root = "."
        self.valid_ext = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

# 测试按图片汇总
def test_image_summary():
    print("=== 测试图片汇总功能 ===")
    
    # 创建管理器
    context = MockContext()
    manager = DataHealthManager(context)
    
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
    issues.append(HealthIssue(
        issue_type=IssueType.INVALID_BOUNDING_BOX,
        severity=IssueSeverity.WARNING,
        file_name="image2.txt",
        file_path="test_labels/image2.txt",
        message="宽度为0",
        suggestion="检查标注",
        line_number=4
    ))
    issues.append(HealthIssue(
        issue_type=IssueType.DUPLICATE_BOUNDING_BOX,
        severity=IssueSeverity.INFO,
        file_name="image3.txt",
        file_path="test_labels/image3.txt",
        message="重复框",
        suggestion="删除重复",
        line_number=1
    ))
    
    result.issues = issues
    
    # 测试按图片汇总
    print("1. 测试 get_issues_by_image 方法...")
    try:
        image_stats = manager.get_issues_by_image(result)
        print(f"   找到 {len(image_stats)} 张有问题的图片")
        for img_name, stats in image_stats.items():
            print(f"   - {img_name}: {stats['total']}个问题 (错误:{stats['errors']}, 警告:{stats['warnings']}, 可修复:{stats['auto_fixable']})")
        print("   ✓ 通过")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试图片汇总报告
    print("\n2. 测试 get_image_summary_report 方法...")
    try:
        summary_list = manager.get_image_summary_report(result)
        print(f"   生成 {len(summary_list)} 条汇总记录")
        for item in summary_list:
            print(f"   - {item['image_name']}: 总数{item['total']}, 错误{item['errors']}, 警告{item['warnings']}, 可修复{item['auto_fixable']}")
        print("   ✓ 通过")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n=== 所有测试通过 ===")
    return True

if __name__ == "__main__":
    success = test_image_summary()
    sys.exit(0 if success else 1)