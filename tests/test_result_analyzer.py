#!/usr/bin/env python3
"""
测试训练结果分析器
"""

import json
import os
import sys
import tempfile
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.training_result_analyzer import get_result_analyzer, ClassificationTrainingResult
from core.trainer_registry import initialize_registry


def create_test_training_log():
    """创建测试训练日志"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="test_classification_")
    log_path = os.path.join(temp_dir, "training_log.json")
    
    # 创建模拟的训练日志
    training_log = {
        "config": {
            "data_dir": "test_data",
            "num_classes": 10,
            "model_name": "resnet18",
            "epochs": 10,
            "batch_size": 32,
            "learning_rate": 0.001,
            "optimizer": "adam",
            "device": "cuda",
            "project": "runs/classification",
            "name": "test_exp",
            "use_augmentation": True,
            "augmentation_random_horizontal_flip": True,
            "augmentation_random_rotation": 10.0,
            "use_pretrained_weights": True,
            "scheduler_type": "step",
            "scheduler_step_size": 5,
            "scheduler_gamma": 0.1,
        },
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "augmentation_used": True,
        "pretrained_used": True,
        "scheduler_used": "step",
        "epochs": []
    }
    
    # 添加模拟的epoch数据
    for epoch in range(1, 11):
        train_loss = 2.0 - (epoch * 0.15)
        val_loss = 1.9 - (epoch * 0.14)
        train_acc = 30.0 + (epoch * 6.0)
        val_acc = 28.0 + (epoch * 6.5)
        
        # 模拟学习率变化
        if epoch <= 5:
            lr = 0.001
        else:
            lr = 0.0001  # 第5轮后学习率衰减
        
        training_log["epochs"].append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_accuracy": train_acc,
            "val_loss": val_loss,
            "val_accuracy": val_acc,
            "learning_rate": lr
        })
    
    # 保存日志
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(training_log, f, indent=2, ensure_ascii=False)
    
    print(f"创建测试训练日志: {log_path}")
    return log_path, temp_dir


def test_result_analyzer():
    """测试结果分析器"""
    print("=== 测试训练结果分析器 ===")
    
    # 创建测试数据
    log_path, temp_dir = create_test_training_log()
    
    try:
        # 初始化注册表
        initialize_registry()
        
        # 测试结果分析器
        analyzer = get_result_analyzer()
        result = analyzer.load_result(log_path)
        
        if not result:
            print("[ERROR] 结果加载失败")
            return False
        
        print(f"[OK] 成功加载训练结果")
        print(f"   训练器ID: {result.trainer_id}")
        print(f"   训练轮数: {len(result.epochs)}")
        print(f"   训练时间: {result.summary.get('training_time', '未知')}")
        
        # 检查是否为分类训练结果
        if isinstance(result, ClassificationTrainingResult):
            print(f"[OK] 成功解析为分类训练结果")
            print(f"   最佳验证准确率: {result.best_val_acc:.2f}% (第 {result.best_epoch} 轮)")
            print(f"   最终训练准确率: {result.final_train_acc:.2f}%")
            print(f"   最终验证准确率: {result.final_val_acc:.2f}%")
            
            # 检查指标序列
            print(f"   训练损失序列: {len(result.train_loss_values)} 个值")
            print(f"   训练准确率序列: {len(result.train_acc_values)} 个值")
            print(f"   验证损失序列: {len(result.val_loss_values)} 个值")
            print(f"   验证准确率序列: {len(result.val_acc_values)} 个值")
            print(f"   学习率序列: {len(result.learning_rate_values)} 个值")
            
            # 检查能力使用情况
            print(f"   数据增强: {'是' if result.capabilities.get('augmentation_used') else '否'}")
            print(f"   预训练权重: {'是' if result.capabilities.get('pretrained_used') else '否'}")
            print(f"   学习率调度器: {result.capabilities.get('scheduler_used', 'none')}")
        
        # 测试结果摘要
        summary_text = analyzer.get_result_summary_text(result)
        print(f"\n=== 结果摘要 ===")
        print(summary_text)
        
        return True
        
    finally:
        # 清理临时文件
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"\n清理临时目录: {temp_dir}")
        except:
            pass


def test_training_center_manager():
    """测试训练中心管理器的结果查找功能"""
    print("\n=== 测试训练中心管理器结果查找 ===")
    
    try:
        from core.training_center_manager import get_training_center
        
        initialize_registry()
        center = get_training_center()
        
        # 测试分类训练器结果查找
        print("测试分类训练器结果查找...")
        result_path = center.find_latest_training_result("classification")
        
        if result_path:
            print(f"找到分类训练结果: {result_path}")
        else:
            print("未找到分类训练结果（这是正常的，如果没有实际训练过）")
        
        # 测试YOLO训练器结果查找
        print("\n测试YOLO训练器结果查找...")
        result_path = center.find_latest_training_result("yolo_v8")
        
        if result_path:
            print(f"找到YOLO训练结果: {result_path}")
        else:
            print("未找到YOLO训练结果（这是正常的，如果没有实际训练过）")
        
        return True
        
    except Exception as e:
        print(f"❌ 训练中心管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_result_window_import():
    """测试结果窗口导入"""
    print("\n=== 测试结果窗口导入 ===")
    
    try:
        from ui.training_result_window import TrainingResultWindow
        print("✅ 成功导入TrainingResultWindow")
        return True
    except Exception as e:
        print(f"❌ 导入TrainingResultWindow失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("训练结果分析入口测试")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 0
    
    # 测试结果分析器
    tests_total += 1
    if test_result_analyzer():
        tests_passed += 1
    
    # 测试训练中心管理器
    tests_total += 1
    if test_training_center_manager():
        tests_passed += 1
    
    # 测试结果窗口导入
    tests_total += 1
    if test_result_window_import():
        tests_passed += 1
    
    print(f"\n{'='*50}")
    print(f"测试结果: {tests_passed}/{tests_total} 通过")
    
    if tests_passed == tests_total:
        print("✅ 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())