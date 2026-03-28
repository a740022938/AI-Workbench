#!/usr/bin/env python3
"""
调试结果分析器
"""

import json
import os
import sys
import tempfile
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.training_result_analyzer import get_result_analyzer, ClassificationTrainingResult


def test_detect_trainer_type():
    """测试训练器类型检测"""
    print("测试训练器类型检测...")
    
    analyzer = get_result_analyzer()
    
    # 测试分类训练器配置
    classification_config = {
        "data_dir": "test_data",
        "num_classes": 10,
        "model_name": "resnet18",
        "epochs": 10,
    }
    
    classification_log = {"config": classification_config}
    
    # 使用反射调用私有方法
    trainer_type = analyzer._detect_trainer_type(classification_log)
    print(f"分类训练器检测结果: {trainer_type}")
    
    # 测试YOLO配置
    yolo_config = {
        "data": "data.yaml",
        "model": "yolov8n.pt",
        "epochs": 100,
    }
    
    yolo_log = {"config": yolo_config}
    trainer_type = analyzer._detect_trainer_type(yolo_log)
    print(f"YOLO训练器检测结果: {trainer_type}")
    
    # 测试未知配置
    unknown_config = {
        "some_key": "some_value",
    }
    
    unknown_log = {"config": unknown_config}
    trainer_type = analyzer._detect_trainer_type(unknown_log)
    print(f"未知训练器检测结果: {trainer_type}")


def test_load_result():
    """测试结果加载"""
    print("\n测试结果加载...")
    
    # 创建测试数据
    temp_dir = tempfile.mkdtemp(prefix="test_debug_")
    log_path = os.path.join(temp_dir, "training_log.json")
    
    # 创建正确的分类训练日志结构
    training_log = {
        "config": {
            "data_dir": "test_data",
            "num_classes": 10,
            "model_name": "resnet18",
            "epochs": 10,
            "batch_size": 32,
            "learning_rate": 0.001,
        },
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "augmentation_used": True,
        "pretrained_used": True,
        "scheduler_used": "step",
        "epochs": [
            {
                "epoch": 1,
                "train_loss": 2.1,
                "train_accuracy": 30.5,
                "val_loss": 2.0,
                "val_accuracy": 35.2,
                "learning_rate": 0.001
            },
            {
                "epoch": 2,
                "train_loss": 1.8,
                "train_accuracy": 45.3,
                "val_loss": 1.9,
                "val_accuracy": 40.1,
                "learning_rate": 0.001
            }
        ]
    }
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(training_log, f, indent=2, ensure_ascii=False)
    
    print(f"创建测试日志: {log_path}")
    
    # 测试加载
    analyzer = get_result_analyzer()
    result = analyzer.load_result(log_path)
    
    if result:
        print(f"成功加载结果")
        print(f"训练器ID: {result.trainer_id}")
        print(f"训练轮数: {len(result.epochs)}")
        
        if isinstance(result, ClassificationTrainingResult):
            print("是ClassificationTrainingResult类型")
            print(f"训练损失值: {result.train_loss_values}")
        else:
            print(f"不是ClassificationTrainingResult类型，而是: {type(result)}")
    else:
        print("结果加载失败")
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """主函数"""
    print("调试训练结果分析器")
    print("=" * 50)
    
    test_detect_trainer_type()
    test_load_result()


if __name__ == "__main__":
    main()