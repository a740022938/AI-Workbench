import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.trainer_registry import initialize_registry
from core.training_center_manager import training_center

initialize_registry()
trainers = training_center.get_available_trainers()

for t in trainers:
    print(f"{t['trainer_id']}: {t['display_name']}")
    print(f"  is_placeholder: {t.get('is_placeholder')}")
    print(f"  can_train: {t.get('can_train')}")
    print()

# 测试分类训练器
if 'classification' in [t['trainer_id'] for t in trainers]:
    print("分类训练器已注册!")
    
    info = training_center.get_trainer_info('classification')
    if info:
        print(f"描述: {info['description']}")
        print(f"config_schema字段数: {len(info.get('config_schema', {}))}")
        
    # 测试创建后端
    try:
        backend = training_center.create_backend('classification')
        print(f"后端类型: {type(backend).__name__}")
        if type(backend).__name__ != 'PlaceholderTrainingBackend':
            print("真实分类后端已创建!")
    except Exception as e:
        print(f"创建后端错误: {e}")
        
    # 测试配置模板
    template = training_center.generate_config_template('classification')
    print(f"配置模板: {len(template)}个字段")
    
    # 测试体检
    test_config = {
        "data_dir": "data/classification",
        "num_classes": 10,
        "model_name": "resnet18",
        "epochs": 2,
        "device": "cpu"
    }
    
    try:
        report = training_center.run_health_check('classification', test_config)
        report_dict = report.to_dict()
        print(f"体检状态: {report_dict.get('overall_status')}")
        print(f"可启动训练: {report_dict.get('can_start_training')}")
    except Exception as e:
        print(f"体检错误: {e}")