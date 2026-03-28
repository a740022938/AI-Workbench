#!/usr/bin/env python3
"""测试训练中心第二期功能"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.trainer_registry import initialize_registry
from core.training_center_manager import training_center

def test_registry():
    """测试注册表"""
    print("=== 测试训练器注册表 ===")
    
    initialize_registry()
    trainers = training_center.get_available_trainers()
    
    print(f"已注册训练器: {len(trainers)}个")
    for t in trainers:
        print(f"  - {t['trainer_id']}: {t['display_name']}")
        print(f"    任务类型: {t['task_type']}, 框架: {t['framework']}")
        print(f"    占位训练器: {t.get('is_placeholder', False)}, 可训练: {t.get('can_train', False)}")
        print(f"    必需配置: {t['required_config_keys']}")
        print()

def test_trainer_info():
    """测试训练器信息"""
    print("\n=== 测试训练器详细信息 ===")
    
    trainer_ids = ["yolo_v8", "classification_example", "segmentation_example", "custom_script"]
    
    for trainer_id in trainer_ids:
        info = training_center.get_trainer_info(trainer_id)
        if info:
            print(f"\n训练器: {info['display_name']} ({trainer_id})")
            print(f"配置schema字段数: {len(info.get('config_schema', {}))}")
            print(f"指标名称: {info.get('metric_names', [])}")
            print(f"日志模式: {list(info.get('log_patterns', {}).keys())}")
        else:
            print(f"\n训练器 {trainer_id} 未找到")

def test_config_templates():
    """测试配置模板"""
    print("\n=== 测试配置模板 ===")
    
    trainer_ids = ["yolo_v8", "classification_example"]
    
    for trainer_id in trainer_ids:
        template = training_center.generate_config_template(trainer_id)
        print(f"\n{trainer_id} 配置模板:")
        for key, value in template.items():
            print(f"  {key}: {value}")

def test_health_check():
    """测试训练前体检"""
    print("\n=== 测试训练前体检 ===")
    
    test_config = {
        "data": "data.yaml",
        "model": "yolov8n.pt",
        "epochs": 100,
    }
    
    report = training_center.run_health_check("yolo_v8", test_config)
    report_dict = report.to_dict()
    print(f"体检状态: {report_dict.get('overall_status')}")
    print(f"可启动训练: {report_dict.get('can_start_training')}")
    
    summary = report_dict.get("environment_check", {}).get("summary", {})
    print(f"检查项: 通过={summary.get('passed', 0)}, 警告={summary.get('warnings', 0)}, 错误={summary.get('errors', 0)}")

if __name__ == "__main__":
    test_registry()
    test_trainer_info()
    test_config_templates()
    test_health_check()
    print("\n✅ 训练中心第二期测试完成")