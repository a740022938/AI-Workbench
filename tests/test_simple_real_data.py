import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.trainer_registry import initialize_registry
from core.training_center_manager import training_center

# 创建测试数据集
def create_test_dataset():
    temp_dir = tempfile.mkdtemp(prefix="test_classification_")
    train_dir = os.path.join(temp_dir, "train")
    val_dir = os.path.join(temp_dir, "val")
    
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(val_dir, exist_ok=True)
    
    classes = ["cat", "dog", "bird"]
    
    for class_name in classes:
        # 训练集
        class_train_dir = os.path.join(train_dir, class_name)
        os.makedirs(class_train_dir, exist_ok=True)
        
        for i in range(3):  # 每个类别3张训练图片
            img_file = os.path.join(class_train_dir, f"{class_name}_{i}.jpg")
            with open(img_file, 'w') as f:
                f.write(f"virtual image: {class_name}_{i}")
        
        # 验证集
        class_val_dir = os.path.join(val_dir, class_name)
        os.makedirs(class_val_dir, exist_ok=True)
        
        for i in range(2):  # 每个类别2张验证图片
            img_file = os.path.join(class_val_dir, f"{class_name}_{i}_val.jpg")
            with open(img_file, 'w') as f:
                f.write(f"virtual val image: {class_name}_{i}")
    
    return temp_dir

# 初始化
initialize_registry()

# 创建测试数据集
data_dir = create_test_dataset()
print(f"Created test dataset: {data_dir}")

try:
    # 测试配置
    test_config = {
        "data_dir": data_dir,
        "num_classes": 3,
        "model_name": "resnet18",
        "epochs": 2,
        "batch_size": 4,
        "learning_rate": 0.001,
        "optimizer": "adam",
        "device": "cpu",
        "project": "runs/test_classification_real",
        "name": "test"
    }
    
    print("\nTest configuration:")
    for key, value in test_config.items():
        print(f"  {key}: {value}")
    
    # 运行体检
    print("\nRunning health check...")
    report = training_center.run_health_check('classification', test_config)
    report_dict = report.to_dict()
    
    print(f"Health check status: {report_dict.get('overall_status')}")
    print(f"Can start training: {report_dict.get('can_start_training')}")
    
    # 显示数据集相关检查
    env_check = report_dict.get("environment_check", {})
    
    print("\nDataset-specific checks:")
    dataset_checks = ['classification_data_dir', 'classification_train_dir', 
                     'classification_classes', 'classification_train_samples',
                     'classification_val_samples', 'classification_sample_distribution']
    
    for check_name in dataset_checks:
        found = False
        for passed in env_check.get('passed', []):
            if check_name in passed.get('name', ''):
                found = True
                print(f"  PASSED - {check_name}: {passed.get('message')}")
                break
        
        if not found:
            for error in env_check.get('errors', []):
                if check_name in error.get('name', ''):
                    print(f"  ERROR - {check_name}: {error.get('message')}")
                    break
            for warning in env_check.get('warnings', []):
                if check_name in warning.get('name', ''):
                    print(f"  WARNING - {check_name}: {warning.get('message')}")
                    break
    
    # 统计
    summary = env_check.get("summary", {})
    print(f"\nSummary: passed={summary.get('passed', 0)}, warnings={summary.get('warnings', 0)}, errors={summary.get('errors', 0)}")
    
    # 测试后端创建
    print("\nTesting backend creation...")
    try:
        backend = training_center.create_backend('classification')
        print(f"Backend type: {type(backend).__name__}")
        
        if type(backend).__name__ != 'PlaceholderTrainingBackend':
            print("SUCCESS: Real classification backend created")
        else:
            print("WARNING: Placeholder backend created (torch may not be installed)")
            
    except Exception as e:
        print(f"ERROR creating backend: {e}")
        
finally:
    # 清理
    try:
        shutil.rmtree(data_dir)
        print(f"\nCleaned up: {data_dir}")
    except:
        pass

print("\nTest completed!")