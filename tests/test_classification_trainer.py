#!/usr/bin/env python3
"""测试分类训练器第四期功能"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.trainer_registry import initialize_registry
from core.training_center_manager import training_center

def test_classification_registration():
    """测试分类训练器注册"""
    print("=== 测试分类训练器注册 ===")
    
    initialize_registry()
    trainers = training_center.get_available_trainers()
    
    print(f"已注册训练器: {len(trainers)}个")
    
    classification_trainer = None
    for t in trainers:
        print(f"  - {t['trainer_id']}: {t['display_name']}")
        print(f"    占位训练器: {t.get('is_placeholder', False)}, 可训练: {t.get('can_train', False)}")
        print(f"    任务类型: {t['task_type']}, 框架: {t['framework']}")
        if t['trainer_id'] == 'classification':
            classification_trainer = t
    
    if classification_trainer:
        print(f"\n✅ 分类训练器已注册:")
        print(f"   可训练: {classification_trainer.get('can_train', False)}")
        print(f"   占位: {classification_trainer.get('is_placeholder', False)}")
        
        if classification_trainer.get('is_placeholder', True):
            print("⚠️ 警告: 分类训练器仍然是占位状态，可能torch未安装")
        else:
            print("🎉 分类训练器已升级为真实可训练!")
    else:
        print("❌ 错误: 分类训练器未找到")
        return False
    
    return True

def test_classification_info():
    """测试分类训练器详细信息"""
    print("\n=== 测试分类训练器详细信息 ===")
    
    info = training_center.get_trainer_info('classification')
    if info:
        print(f"训练器: {info['display_name']} (classification)")
        print(f"描述: {info['description']}")
        print(f"配置schema字段数: {len(info.get('config_schema', {}))}")
        print(f"必需配置项: {info['required_config_keys']}")
        print(f"必需依赖: {info['required_dependencies']}")
        
        # 检查config_schema
        schema = info.get('config_schema', {})
        if schema:
            print(f"\n配置字段:")
            for key, field_schema in schema.items():
                field_type = field_schema.get('type', 'string')
                required = field_schema.get('required', False)
                default = field_schema.get('default', '无')
                print(f"  - {key}: {field_type} {'🔴' if required else '⚪'} 默认={default}")
        else:
            print("⚠️ 警告: 配置schema为空")
        
        return True
    else:
        print("❌ 错误: 无法获取分类训练器信息")
        return False

def test_classification_template():
    """测试分类训练器配置模板"""
    print("\n=== 测试分类训练器配置模板 ===")
    
    template = training_center.generate_config_template('classification')
    if template:
        print(f"配置模板字段数: {len(template)}")
        print("模板内容:")
        for key, value in template.items():
            print(f"  {key}: {value}")
        return True
    else:
        print("❌ 错误: 无法生成配置模板")
        return False

def test_classification_backend_creation():
    """测试创建分类训练后端"""
    print("\n=== 测试创建分类训练后端 ===")
    
    try:
        backend = training_center.create_backend('classification')
        print(f"后端类型: {type(backend).__name__}")
        
        status = backend.get_status()
        print(f"后端状态: {status}")
        
        if backend.__class__.__name__ == 'PlaceholderTrainingBackend':
            print("⚠️ 警告: 创建的是占位后端，真实后端可能无法导入")
            return False
        else:
            print("✅ 成功创建真实分类训练后端")
            return True
    except Exception as e:
        print(f"❌ 创建后端失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_classification_health_check():
    """测试分类训练器体检"""
    print("\n=== 测试分类训练器体检 ===")
    
    test_config = {
        "data_dir": "data/classification",
        "num_classes": 10,
        "model_name": "resnet18",
        "epochs": 2,
        "batch_size": 4,
        "learning_rate": 0.001,
        "optimizer": "adam",
        "device": "cpu",
        "project": "runs/test_classification",
        "name": "test"
    }
    
    try:
        report = training_center.run_health_check('classification', test_config)
        report_dict = report.to_dict()
        
        print(f"体检状态: {report_dict.get('overall_status')}")
        print(f"可启动训练: {report_dict.get('can_start_training')}")
        
        summary = report_dict.get("environment_check", {}).get("summary", {})
        print(f"检查项: 通过={summary.get('passed', 0)}, 警告={summary.get('warnings', 0)}, 错误={summary.get('errors', 0)}")
        
        # 显示具体错误和警告
        env_check = report_dict.get("environment_check", {})
        if env_check.get('errors'):
            print(f"错误项:")
            for error in env_check['errors']:
                print(f"  - {error.get('name')}: {error.get('message')}")
        
        if env_check.get('warnings'):
            print(f"警告项:")
            for warning in env_check['warnings']:
                print(f"  - {warning.get('name')}: {warning.get('message')}")
        
        return True
    except Exception as e:
        print(f"❌ 体检过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("训练中心第四期 - 分类训练器测试")
    print("=" * 60)
    
    all_passed = True
    
    all_passed &= test_classification_registration()
    all_passed &= test_classification_info()
    all_passed &= test_classification_template()
    all_passed &= test_classification_backend_creation()
    all_passed &= test_classification_health_check()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！分类训练器已成功接入训练中心")
        print("   下一步: 在训练中心中选择'图像分类'训练器进行真实训练")
    else:
        print("⚠️ 部分测试失败，分类训练器可能无法完全工作")
        print("   请检查torch和torchvision是否安装: pip install torch torchvision")
    
    print("\n✅ 测试完成")