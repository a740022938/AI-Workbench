"""
分类训练后端 - 基于PyTorch的图像分类训练器
支持ResNet等常见分类模型，使用虚拟数据或真实数据集进行训练
"""

import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

from core.training_backends.base_backend import BaseTrainingBackend


class ClassificationTrainingBackend(BaseTrainingBackend):
    """分类训练后端"""
    
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.last_project = None
        self.last_name = None
        self.last_run_dir = None
        self.last_model_path = None
        self.last_log_path = None
    
    def _emit(self, monitor_window, message):
        """向监控窗口发送日志"""
        try:
            if monitor_window is not None:
                monitor_window.append_log(message)
        except:
            pass
    
    def _set_status(self, monitor_window, text):
        """设置训练状态"""
        try:
            if monitor_window is not None:
                monitor_window.set_status(text)
        except:
            pass
    
    def _update_run_paths(self, cfg):
        """更新运行路径"""
        project = str(cfg.get("project", "runs/classification"))
        name = str(cfg.get("name", "exp"))
        
        self.last_project = project
        self.last_name = name
        self.last_run_dir = os.path.join(project, name)
        self.last_model_path = os.path.join(self.last_run_dir, "model.pth")
        self.last_log_path = os.path.join(self.last_run_dir, "training_log.json")
    
    def _build_train_script(self):
        """构建分类训练脚本（增强版：支持数据增强、预训练权重、学习率调度）"""
        return r'''
import json
import sys
import os
import time
from datetime import datetime

# 配置解析
cfg = json.loads(sys.argv[1])

print("[分类训练] PyTorch 分类训练启动（增强版）")
print(f"[分类训练] 配置: {json.dumps(cfg, indent=2)}")

# 解析配置
data_dir = cfg.get("data_dir", "data/classification")
num_classes = int(cfg.get("num_classes", 10))
model_name = cfg.get("model_name", "resnet18")
epochs = int(cfg.get("epochs", 10))
batch_size = int(cfg.get("batch_size", 32))
learning_rate = float(cfg.get("learning_rate", 0.001))
optimizer_name = cfg.get("optimizer", "adam")
device = cfg.get("device", "cuda" if torch.cuda.is_available() else "cpu")
project = cfg.get("project", "runs/classification")
name = cfg.get("name", "exp")

# 新增配置：数据增强
use_augmentation = cfg.get("use_augmentation", True)
augmentation_random_horizontal_flip = cfg.get("augmentation_random_horizontal_flip", True)
augmentation_random_rotation = float(cfg.get("augmentation_random_rotation", 10.0))  # 旋转角度范围
augmentation_color_jitter = cfg.get("augmentation_color_jitter", False)
augmentation_color_jitter_brightness = float(cfg.get("augmentation_color_jitter_brightness", 0.2))
augmentation_color_jitter_contrast = float(cfg.get("augmentation_color_jitter_contrast", 0.2))
augmentation_color_jitter_saturation = float(cfg.get("augmentation_color_jitter_saturation", 0.2))
augmentation_color_jitter_hue = float(cfg.get("augmentation_color_jitter_hue", 0.1))

# 新增配置：预训练权重
use_pretrained_weights = cfg.get("use_pretrained_weights", True)

# 新增配置：学习率调度
scheduler_type = cfg.get("scheduler_type", "none")  # none, step, cosine
scheduler_step_size = int(cfg.get("scheduler_step_size", 30))
scheduler_gamma = float(cfg.get("scheduler_gamma", 0.1))
scheduler_t_max = int(cfg.get("scheduler_t_max", epochs))

# 创建输出目录
output_dir = os.path.join(project, name)
os.makedirs(output_dir, exist_ok=True)

print(f"[分类训练] 输出目录: {output_dir}")
print(f"[分类训练] 模型: {model_name}, 类别数: {num_classes}")
print(f"[分类训练] 轮数: {epochs}, 批大小: {batch_size}, 学习率: {learning_rate}")
print(f"[分类训练] 设备: {device}")
print(f"[分类训练] 数据增强: {'启用' if use_augmentation else '禁用'}")
print(f"[分类训练] 预训练权重: {'启用' if use_pretrained_weights else '禁用'}")
print(f"[分类训练] 学习率调度器: {scheduler_type}")

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    import torchvision
    import torchvision.transforms as transforms
    from torchvision import models
    
    print("[分类训练] PyTorch 导入成功")
    
    # 设置设备
    device = torch.device(device if torch.cuda.is_available() else "cpu")
    print(f"[分类训练] 使用设备: {device}")
    
    # 检查数据目录是否存在
    if not os.path.exists(data_dir):
        print(f"[分类训练] ❌ 错误: 数据目录不存在: {data_dir}")
        print(f"[分类训练] 请创建以下目录结构:")
        print(f"  {data_dir}/train/class1/")
        print(f"  {data_dir}/train/class2/")
        print(f"  ...")
        print(f"  {data_dir}/val/class1/")
        print(f"  {data_dir}/val/class2/")
        print(f"  ...")
        print(f"[分类训练] 或者使用虚拟数据模式，将数据目录留空")
        sys.exit(1)
    
    # 检查目录结构
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")
    
    if not os.path.exists(train_dir):
        print(f"[分类训练] ❌ 错误: 训练目录不存在: {train_dir}")
        print(f"[分类训练] 请确保数据目录包含 'train' 子目录")
        sys.exit(1)
    
    if not os.path.exists(val_dir):
        print(f"[分类训练] ⚠️ 警告: 验证目录不存在: {val_dir}")
        print(f"[分类训练] 将使用训练数据进行验证")
        val_dir = train_dir
    
    # 获取类别
    try:
        class_names = sorted([d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))])
        actual_num_classes = len(class_names)
        
        if actual_num_classes < 2:
            print(f"[分类训练] ❌ 错误: 训练目录中类别数量不足: {actual_num_classes}")
            print(f"[分类训练] 需要至少2个类别，请确保每个类别是一个子目录")
            sys.exit(1)
        
        print(f"[分类训练] 发现 {actual_num_classes} 个类别: {class_names}")
        
        # 检查配置中的类别数是否与实际情况匹配
        if num_classes != actual_num_classes:
            print(f"[分类训练] ⚠️ 注意: 配置的类别数({num_classes})与实际类别数({actual_num_classes})不一致")
            print(f"[分类训练] 将使用实际类别数: {actual_num_classes}")
            num_classes = actual_num_classes
        
        # 统计样本数量
        train_counts = {}
        total_train = 0
        for class_name in class_names:
            class_dir = os.path.join(train_dir, class_name)
            if os.path.isdir(class_dir):
                images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
                count = len(images)
                train_counts[class_name] = count
                total_train += count
        
        val_counts = {}
        total_val = 0
        for class_name in class_names:
            class_dir = os.path.join(val_dir, class_name)
            if os.path.isdir(class_dir):
                images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
                count = len(images)
                val_counts[class_name] = count
                total_val += count
        
        print(f"[分类训练] 训练集: {total_train} 张图片")
        for class_name, count in train_counts.items():
            print(f"  {class_name}: {count} 张")
        
        print(f"[分类训练] 验证集: {total_val} 张图片")
        for class_name, count in val_counts.items():
            print(f"  {class_name}: {count} 张")
        
        if total_train == 0:
            print(f"[分类训练] ❌ 错误: 训练集中没有找到图片")
            print(f"[分类训练] 请确保每个类别目录中包含图片文件")
            sys.exit(1)
        
        # 数据转换 - 训练集（支持增强）
        train_transform_list = [
            transforms.Resize((224, 224)),
        ]
        
        if use_augmentation:
            print(f"[分类训练] 启用数据增强")
            if augmentation_random_horizontal_flip:
                train_transform_list.append(transforms.RandomHorizontalFlip(p=0.5))
                print(f"  - 随机水平翻转 (p=0.5)")
            if augmentation_random_rotation > 0:
                train_transform_list.append(transforms.RandomRotation(degrees=augmentation_random_rotation))
                print(f"  - 随机旋转 (±{augmentation_random_rotation}度)")
            if augmentation_color_jitter:
                train_transform_list.append(transforms.ColorJitter(
                    brightness=augmentation_color_jitter_brightness,
                    contrast=augmentation_color_jitter_contrast,
                    saturation=augmentation_color_jitter_saturation,
                    hue=augmentation_color_jitter_hue
                ))
                print(f"  - 颜色抖动: brightness={augmentation_color_jitter_brightness}, contrast={augmentation_color_jitter_contrast}")
        
        train_transform_list.extend([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        train_transform = transforms.Compose(train_transform_list)
        
        # 验证集转换（无增强）
        val_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # 加载数据集
        train_dataset = torchvision.datasets.ImageFolder(root=train_dir, transform=train_transform)
        val_dataset = torchvision.datasets.ImageFolder(root=val_dir, transform=val_transform)
        
        print(f"[分类训练] 成功加载数据集:")
        print(f"  训练集: {len(train_dataset)} 张图片 (转换: {'增强' if use_augmentation else '基础'})")
        print(f"  验证集: {len(val_dataset)} 张图片")
        
        # 创建数据加载器
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
        
    except Exception as e:
        print(f"[分类训练] ❌ 加载数据集时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 创建模型（支持预训练权重）
    print(f"[分类训练] 创建模型: {model_name}")
    
    # 处理预训练权重（兼容不同torchvision版本）
    pretrained_param = None
    if use_pretrained_weights:
        try:
            # 尝试新版本API (torchvision >= 0.13)
            import torchvision
            weights_attr = getattr(torchvision.models, f"{model_name.upper()}_Weights", None)
            if weights_attr is not None:
                pretrained_param = weights_attr.DEFAULT
                print(f"[分类训练] 使用预训练权重 (新API): {pretrained_param}")
            else:
                # 回退到旧版本API
                pretrained_param = True
                print(f"[分类训练] 使用预训练权重 (旧API)")
        except Exception as e:
            print(f"[分类训练] ⚠️ 无法确定预训练权重API，将尝试旧模式: {e}")
            pretrained_param = True
    
    if model_name == "resnet18":
        if pretrained_param is not None:
            model = models.resnet18(weights=pretrained_param if isinstance(pretrained_param, str) else pretrained_param)
        else:
            model = models.resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif model_name == "resnet34":
        if pretrained_param is not None:
            model = models.resnet34(weights=pretrained_param if isinstance(pretrained_param, str) else pretrained_param)
        else:
            model = models.resnet34(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif model_name == "resnet50":
        if pretrained_param is not None:
            model = models.resnet50(weights=pretrained_param if isinstance(pretrained_param, str) else pretrained_param)
        else:
            model = models.resnet50(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif model_name == "simple_cnn":
        print(f"[分类训练] 使用简单CNN（不支持预训练）")
        class SimpleCNN(nn.Module):
            def __init__(self, num_classes):
                super(SimpleCNN, self).__init__()
                self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
                self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
                self.pool = nn.MaxPool2d(2, 2)
                self.fc1 = nn.Linear(64 * 56 * 56, 512)
                self.fc2 = nn.Linear(512, num_classes)
                self.relu = nn.ReLU()
                self.dropout = nn.Dropout(0.5)
            
            def forward(self, x):
                x = self.pool(self.relu(self.conv1(x)))
                x = self.pool(self.relu(self.conv2(x)))
                x = x.view(x.size(0), -1)
                x = self.relu(self.fc1(x))
                x = self.dropout(x)
                x = self.fc2(x)
                return x
        
        model = SimpleCNN(num_classes)
    else:
        print(f"[分类训练] ❌ 错误: 未知模型 {model_name}")
        sys.exit(1)
    
    model = model.to(device)
    print(f"[分类训练] 模型创建完成: {model_name} (预训练: {'是' if use_pretrained_weights else '否'})")
    
    # 损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    
    if optimizer_name == "adam":
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        print(f"[分类训练] 优化器: Adam (lr={learning_rate})")
    elif optimizer_name == "sgd":
        optimizer = optim.SGD(model.parameters(), lr=learning_rate, momentum=0.9)
        print(f"[分类训练] 优化器: SGD (lr={learning_rate}, momentum=0.9)")
    else:
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        print(f"[分类训练] 优化器: Adam (默认, lr={learning_rate})")
    
    # 学习率调度器
    scheduler = None
    if scheduler_type == "step":
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=scheduler_step_size, gamma=scheduler_gamma)
        print(f"[分类训练] 学习率调度器: StepLR (step_size={scheduler_step_size}, gamma={scheduler_gamma})")
    elif scheduler_type == "cosine":
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=scheduler_t_max)
        print(f"[分类训练] 学习率调度器: CosineAnnealingLR (T_max={scheduler_t_max})")
    else:
        print(f"[分类训练] 学习率调度器: 无")
    
    # 训练循环
    print("[分类训练] 开始训练...")
    training_log = {
        "config": cfg,
        "start_time": datetime.now().isoformat(),
        "epochs": [],
        "metrics": {},
        "augmentation_used": use_augmentation,
        "pretrained_used": use_pretrained_weights,
        "scheduler_used": scheduler_type,
        "notes": cfg.get("notes", {}),  # 实验批注
        "tags": cfg.get("tags", []),    # 实验标签
        "is_favorite": cfg.get("is_favorite", False),  # 是否收藏
        "is_important": cfg.get("is_important", False),  # 是否重要
        "is_archived": cfg.get("is_archived", False)  # 是否归档
    }
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for i, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            if i % 10 == 0:
                current_lr = optimizer.param_groups[0]['lr']
                print(f"[分类训练] Epoch {epoch+1}/{epochs}, Batch {i}, Loss: {loss.item():.4f}, LR: {current_lr:.6f}")
        
        # 验证
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
        
        # 更新学习率（如果使用了调度器）
        current_lr = optimizer.param_groups[0]['lr']
        if scheduler is not None:
            scheduler.step()
            new_lr = optimizer.param_groups[0]['lr']
            if new_lr != current_lr:
                print(f"[分类训练] Epoch {epoch+1}: 学习率更新 {current_lr:.6f} -> {new_lr:.6f}")
        
        # 计算指标
        train_loss = running_loss / len(train_loader)
        train_acc = 100. * correct / total
        val_loss_val = val_loss / len(val_loader)
        val_acc = 100. * val_correct / val_total
        
        # 记录日志
        epoch_log = {
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "train_accuracy": train_acc,
            "val_loss": val_loss_val,
            "val_accuracy": val_acc,
            "learning_rate": current_lr
        }
        training_log["epochs"].append(epoch_log)
        
        print(f"[分类训练] Epoch {epoch+1}/{epochs}: "
              f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%, "
              f"Val Loss: {val_loss_val:.4f}, Val Acc: {val_acc:.2f}%, "
              f"LR: {current_lr:.6f}")
    
    # 保存模型
    model_save_path = os.path.join(output_dir, "model.pth")
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': cfg,
        'training_log': training_log,
        'num_classes': num_classes,
        'model_name': model_name,
        'class_names': class_names if 'class_names' in locals() else []
    }, model_save_path)
    
    training_log["end_time"] = datetime.now().isoformat()
    training_log["model_saved"] = model_save_path
    
    # 保存训练日志
    log_path = os.path.join(output_dir, "training_log.json")
    with open(log_path, "w", encoding='utf-8') as f:
        json.dump(training_log, f, indent=2, ensure_ascii=False)
    
    print(f"[分类训练] 训练完成，模型保存到: {model_save_path}")
    print(f"[分类训练] 训练日志保存到: {log_path}")
    print(f"[分类训练] 最终验证准确率: {training_log['epochs'][-1]['val_accuracy']:.2f}%")
    print(f"[分类训练] 使用能力总结:")
    print(f"  - 数据增强: {'是' if use_augmentation else '否'}")
    print(f"  - 预训练权重: {'是' if use_pretrained_weights else '否'}")
    print(f"  - 学习率调度: {scheduler_type}")
    
except ImportError as e:
    print(f"[分类训练] 导入错误: {e}")
    print("[分类训练] 请确保已安装 torch 和 torchvision: pip install torch torchvision")
    sys.exit(1)
except Exception as e:
    print(f"[分类训练] 训练过程出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("[分类训练] 训练进程结束")
'''

    def _start_worker(self, training_config, monitor_window=None):
        """启动训练工作线程"""
        try:
            cfg = dict(training_config or {})
            self._update_run_paths(cfg)
            
            self._set_status(monitor_window, "训练中")
            self._emit(monitor_window, "[分类训练] 正在启动分类训练...")
            
            # 构建训练命令
            cmd = [
                sys.executable,
                "-u",
                "-c",
                self._build_train_script(),
                json.dumps(cfg, ensure_ascii=False),
            ]
            
            self._emit(monitor_window, "[分类训练] 正在启动训练进程...")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )
            
            # 实时输出日志
            if self.process.stdout is not None:
                for line in self.process.stdout:
                    self._emit(monitor_window, line.rstrip())
            
            # 等待进程完成
            return_code = self.process.wait()
            
            if return_code == 0:
                self._set_status(monitor_window, "已完成")
                self._emit(monitor_window, f"[分类训练] 训练成功完成，返回码={return_code}")
                self._emit(monitor_window, f"[分类训练] 模型保存到: {self.last_model_path}")
            else:
                self._set_status(monitor_window, "启动失败")
                self._emit(monitor_window, f"[分类训练] 训练失败，返回码={return_code}")
            
        except Exception as e:
            self._set_status(monitor_window, "启动失败")
            self._emit(monitor_window, f"[分类训练] 启动失败: {e}")
            import traceback
            self._emit(monitor_window, f"[分类训练] 错误详情: {traceback.format_exc()}")
        finally:
            self.is_running = False
            self.process = None
    
    def start(self, training_config, monitor_window=None):
        """启动训练"""
        if self.is_running:
            self._set_status(monitor_window, "已有任务")
            self._emit(monitor_window, "[分类训练] 已有任务在运行中")
            return False
        
        self.is_running = True
        self._set_status(monitor_window, "准备启动")
        
        self.worker_thread = threading.Thread(
            target=self._start_worker,
            args=(training_config, monitor_window),
            daemon=True
        )
        self.worker_thread.start()
        return True
    
    def stop(self, monitor_window=None):
        """停止训练"""
        try:
            if self.process is not None and self.is_running:
                self.process.terminate()
                self._set_status(monitor_window, "已停止")
                self._emit(monitor_window, "[分类训练] 已发送停止信号")
                return True
            self._emit(monitor_window, "[分类训练] 当前没有运行中的训练任务")
            return False
        except Exception as e:
            self._emit(monitor_window, f"[分类训练] 停止失败: {e}")
            return False
    
    def resume(self, training_config, monitor_window=None):
        """继续训练（分类训练暂不支持断点续训）"""
        self._emit(monitor_window, "[分类训练] 分类训练暂不支持断点续训，将从头开始训练")
        return self.start(training_config, monitor_window)
    
    def get_status(self):
        """获取训练状态"""
        return {
            "is_running": self.is_running,
            "last_run_dir": self.last_run_dir,
            "last_model_path": self.last_model_path,
            "backend_type": "classification"
        }


if __name__ == "__main__":
    # 测试代码
    backend = ClassificationTrainingBackend()
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
    
    print("测试分类训练后端...")
    print(f"配置: {json.dumps(test_config, indent=2)}")
    print("注意：此测试需要安装 torch 和 torchvision")