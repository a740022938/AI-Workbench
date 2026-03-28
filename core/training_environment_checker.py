"""
训练环境检测器 - 检查Python环境、依赖包、文件存在性、GPU可用性等
"""

import os
import sys
import importlib
import subprocess
from typing import Dict, List, Tuple, Optional, Any
import json

from core.trainer_registry import TrainerRegistry


class EnvironmentCheckResult:
    """环境检查结果"""
    
    def __init__(self):
        self.passed: List[Dict[str, Any]] = []  # 通过项
        self.warnings: List[Dict[str, Any]] = []  # 警告项
        self.errors: List[Dict[str, Any]] = []  # 错误项
        self.can_train: bool = False  # 是否可以启动训练
    
    def add_passed(self, check_name: str, message: str, details: Any = None):
        """添加通过项"""
        self.passed.append({
            "name": check_name,
            "message": message,
            "details": details
        })
    
    def add_warning(self, check_name: str, message: str, details: Any = None):
        """添加警告项"""
        self.warnings.append({
            "name": check_name,
            "message": message,
            "details": details
        })
    
    def add_error(self, check_name: str, message: str, details: Any = None):
        """添加错误项"""
        self.errors.append({
            "name": check_name,
            "message": message,
            "details": details
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors,
            "can_train": self.can_train and len(self.errors) == 0,
            "summary": {
                "total_checks": len(self.passed) + len(self.warnings) + len(self.errors),
                "passed": len(self.passed),
                "warnings": len(self.warnings),
                "errors": len(self.errors)
            }
        }
    
    def __repr__(self):
        return f"EnvironmentCheckResult(passed={len(self.passed)}, warnings={len(self.warnings)}, errors={len(self.errors)}, can_train={self.can_train})"


class TrainingEnvironmentChecker:
    """训练环境检测器"""
    
    def __init__(self):
        self.result = EnvironmentCheckResult()
    
    def check_all(self, trainer_id: str, config: Dict[str, Any]) -> EnvironmentCheckResult:
        """
        执行全套环境检查
        
        Args:
            trainer_id: 训练器ID
            config: 训练配置
            
        Returns:
            检查结果
        """
        self.result = EnvironmentCheckResult()
        
        # 1. 基础环境检查
        self._check_python_environment()
        
        # 2. 训练器存在性检查
        self._check_trainer_exists(trainer_id)
        
        # 3. 依赖包检查
        self._check_dependencies(trainer_id)
        
        # 4. 文件存在性检查
        self._check_required_files(trainer_id, config)
        
        # 5. 配置完整性检查
        self._check_config_completeness(trainer_id, config)
        
        # 6. 输出目录可写检查
        self._check_output_directory(config)
        
        # 7. GPU/设备可用性检查
        self._check_device_availability(config)
        
        # 8. 训练器特定要求检查
        self._check_trainer_specific_requirements(trainer_id, config)
        
        # 判断是否可以启动训练
        self.result.can_train = len(self.result.errors) == 0
        
        return self.result
    
    def _check_python_environment(self):
        """检查Python环境"""
        # Python版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 7):
            self.result.add_passed("python_version", f"Python版本 {python_version} 符合要求", python_version)
        else:
            self.result.add_error("python_version", f"Python版本 {python_version} 过低，需要3.7+", python_version)
        
        # 当前工作目录
        cwd = os.getcwd()
        self.result.add_passed("working_directory", f"工作目录: {cwd}", cwd)
        
        # 操作系统
        os_name = os.name
        platform = sys.platform
        self.result.add_passed("operating_system", f"操作系统: {platform}", {"os": os_name, "platform": platform})
    
    def _check_trainer_exists(self, trainer_id: str):
        """检查训练器是否存在"""
        metadata = TrainerRegistry.get_trainer(trainer_id)
        if metadata:
            self.result.add_passed("trainer_exists", f"训练器 '{metadata.display_name}' 可用", {
                "trainer_id": metadata.trainer_id,
                "display_name": metadata.display_name,
                "task_type": metadata.task_type
            })
        else:
            self.result.add_error("trainer_exists", f"训练器 '{trainer_id}' 未注册", trainer_id)
    
    def _check_dependencies(self, trainer_id: str):
        """检查依赖包"""
        metadata = TrainerRegistry.get_trainer(trainer_id)
        if not metadata:
            return
        
        dependency_status = TrainerRegistry.check_dependency(trainer_id)
        
        all_passed = True
        missing_deps = []
        
        for dep, available in dependency_status.items():
            if available:
                self.result.add_passed(f"dependency_{dep}", f"依赖包 '{dep}' 可用", dep)
            else:
                self.result.add_error(f"dependency_{dep}", f"依赖包 '{dep}' 未安装", dep)
                missing_deps.append(dep)
                all_passed = False
        
        if all_passed:
            self.result.add_passed("all_dependencies", "所有依赖包检查通过", list(dependency_status.keys()))
        elif missing_deps:
            self.result.add_warning("missing_dependencies", f"缺失依赖包: {', '.join(missing_deps)}", missing_deps)
    
    def _check_required_files(self, trainer_id: str, config: Dict[str, Any]):
        """检查必需文件"""
        metadata = TrainerRegistry.get_trainer(trainer_id)
        if not metadata:
            return
        
        # 分类训练器不需要data.yaml和model.pt，跳过这些检查
        if trainer_id == "classification":
            # 分类训练器只需要数据目录，在特定检查中处理
            pass
        else:
            # 检查模型文件（针对YOLO等需要预训练权重的训练器）
            model_path = config.get("model") or config.get("weights")
            if model_path and os.path.exists(model_path):
                self.result.add_passed("model_file", f"模型文件存在: {model_path}", model_path)
            elif model_path:
                self.result.add_error("model_file", f"模型文件不存在: {model_path}", model_path)
            else:
                self.result.add_warning("model_file", "未指定模型文件，将使用默认模型", None)
            
            # 检查数据配置文件（针对YOLO等需要data.yaml的训练器）
            data_path = config.get("data") or config.get("data_yaml") or config.get("dataset")
            if data_path and os.path.exists(data_path):
                self.result.add_passed("data_config", f"数据配置文件存在: {data_path}", data_path)
            elif data_path:
                self.result.add_error("data_config", f"数据配置文件不存在: {data_path}", data_path)
            else:
                self.result.add_error("data_config", "未指定数据配置文件", None)
        
        # 检查其他必需文件
        for file_pattern in metadata.required_files:
            # 简单的文件存在性检查
            if trainer_id != "classification":  # 分类训练器不需要这些文件
                data_path = config.get("data") or config.get("data_yaml") or config.get("dataset")
                if file_pattern == "data.yaml" and data_path and os.path.exists(data_path):
                    continue  # 已检查过
                elif file_pattern == "model.pt":
                    model_path = config.get("model") or config.get("weights")
                    if model_path and os.path.exists(model_path):
                        continue  # 已检查过
            
            # 对于其他文件，暂时只记录
            self.result.add_warning("other_required_files", f"需要文件: {file_pattern}（未检查）", file_pattern)
    
    def _check_config_completeness(self, trainer_id: str, config: Dict[str, Any]):
        """检查配置完整性"""
        missing_keys = TrainerRegistry.validate_config(trainer_id, config)
        
        if not missing_keys:
            self.result.add_passed("config_completeness", "配置完整性检查通过", config)
        else:
            for key in missing_keys:
                self.result.add_error("config_missing", f"缺少必需配置项: {key}", key)
    
    def _check_output_directory(self, config: Dict[str, Any]):
        """检查输出目录是否可写"""
        project = config.get("project", "runs/train")
        name = config.get("name", "exp")
        output_dir = os.path.join(project, name)
        
        # 尝试创建目录（如果不存在）
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # 测试写入权限
            test_file = os.path.join(output_dir, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            self.result.add_passed("output_directory", f"输出目录可写: {output_dir}", output_dir)
        except Exception as e:
            self.result.add_error("output_directory", f"输出目录无法写入: {output_dir} ({str(e)})", output_dir)
    
    def _check_device_availability(self, config: Dict[str, Any]):
        """检查设备可用性"""
        device = config.get("device", "0")
        
        if device.lower() == "cpu":
            self.result.add_passed("device", "使用CPU进行训练", "cpu")
            return
        
        # 尝试检查GPU
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                if gpu_count > 0:
                    gpu_name = torch.cuda.get_device_name(0)
                    self.result.add_passed("gpu_available", f"GPU可用: {gpu_name} (共{gpu_count}个)", {
                        "count": gpu_count,
                        "name": gpu_name,
                        "device_ids": list(range(gpu_count))
                    })
                    
                    # 检查请求的设备ID是否有效
                    try:
                        device_id = int(device)
                        if 0 <= device_id < gpu_count:
                            self.result.add_passed("gpu_device_id", f"GPU设备ID {device_id} 有效", device_id)
                        else:
                            self.result.add_error("gpu_device_id", f"GPU设备ID {device_id} 超出范围 (0-{gpu_count-1})", device_id)
                    except ValueError:
                        self.result.add_warning("gpu_device_id", f"设备ID格式无效: {device}，将使用默认设备", device)
                else:
                    self.result.add_warning("gpu_available", "CUDA可用但未检测到GPU设备", None)
            else:
                self.result.add_warning("gpu_available", "CUDA不可用，将使用CPU", None)
        except ImportError:
            self.result.add_warning("gpu_check", "无法导入torch进行GPU检查", None)
        except Exception as e:
            self.result.add_warning("gpu_check", f"GPU检查出错: {str(e)}", str(e))
    
    def _check_trainer_specific_requirements(self, trainer_id: str, config: Dict[str, Any]):
        """检查训练器特定要求"""
        metadata = TrainerRegistry.get_trainer(trainer_id)
        if not metadata:
            return
        
        # 分类训练器特定检查
        if trainer_id == "classification":
            self._check_classification_dataset(config)
        # 可以在这里添加其他训练器的特定检查
    
    def _check_classification_dataset(self, config: Dict[str, Any]):
        """检查分类数据集目录结构"""
        data_dir = config.get("data_dir", "")
        
        if not data_dir:
            self.result.add_error("classification_data_dir", "未指定数据目录(data_dir)", None)
            return
        
        if not os.path.exists(data_dir):
            self.result.add_error("classification_data_dir", f"数据目录不存在: {data_dir}", data_dir)
            return
        
        # 检查训练目录
        train_dir = os.path.join(data_dir, "train")
        if not os.path.exists(train_dir):
            self.result.add_error("classification_train_dir", f"训练目录不存在: {train_dir}", train_dir)
            return
        
        # 检查验证目录（可选，但建议有）
        val_dir = os.path.join(data_dir, "val")
        if not os.path.exists(val_dir):
            self.result.add_warning("classification_val_dir", f"验证目录不存在: {val_dir}，将使用训练数据进行验证", val_dir)
            val_dir = train_dir
        
        # 检查类别目录
        try:
            # 获取训练目录中的类别
            train_classes = [d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]
            actual_num_classes = len(train_classes)
            
            if actual_num_classes < 2:
                self.result.add_error("classification_classes", f"训练目录中类别数量不足: {actual_num_classes}，需要至少2个类别", {
                    "found_classes": train_classes,
                    "actual_num_classes": actual_num_classes
                })
                return
            
            self.result.add_passed("classification_classes", f"发现 {actual_num_classes} 个类别: {', '.join(train_classes[:5])}{'...' if len(train_classes) > 5 else ''}", {
                "class_names": train_classes,
                "actual_num_classes": actual_num_classes
            })
            
            # 检查配置中的类别数
            config_num_classes = config.get("num_classes")
            if config_num_classes is not None:
                config_num_classes = int(config_num_classes)
                if config_num_classes != actual_num_classes:
                    self.result.add_warning("classification_num_classes", 
                                          f"配置的类别数({config_num_classes})与实际类别数({actual_num_classes})不一致，将使用实际类别数",
                                          {"config_num_classes": config_num_classes, "actual_num_classes": actual_num_classes})
            
            # 统计样本数量
            train_counts = {}
            total_train = 0
            for class_name in train_classes:
                class_dir = os.path.join(train_dir, class_name)
                if os.path.isdir(class_dir):
                    images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
                    count = len(images)
                    train_counts[class_name] = count
                    total_train += count
            
            if total_train == 0:
                self.result.add_error("classification_train_samples", "训练目录中没有找到图片文件", {
                    "train_dir": train_dir,
                    "class_counts": train_counts
                })
                return
            
            # 检查验证目录中的类别（如果存在）
            if os.path.exists(val_dir) and val_dir != train_dir:
                val_classes = [d for d in os.listdir(val_dir) if os.path.isdir(os.path.join(val_dir, d))]
                val_counts = {}
                total_val = 0
                
                for class_name in val_classes:
                    class_dir = os.path.join(val_dir, class_name)
                    if os.path.isdir(class_dir):
                        images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
                        count = len(images)
                        val_counts[class_name] = count
                        total_val += count
                
                if total_val == 0:
                    self.result.add_warning("classification_val_samples", "验证目录中没有找到图片文件", {
                        "val_dir": val_dir,
                        "class_counts": val_counts
                    })
                else:
                    self.result.add_passed("classification_val_samples", f"验证集包含 {total_val} 张图片", {
                        "total_val": total_val,
                        "class_counts": val_counts
                    })
            
            self.result.add_passed("classification_train_samples", f"训练集包含 {total_train} 张图片", {
                "total_train": total_train,
                "class_counts": train_counts
            })
            
            # 显示样本分布
            if total_train > 0:
                sample_info = []
                for class_name in sorted(train_counts.keys())[:5]:  # 只显示前5个类别
                    count = train_counts[class_name]
                    percentage = (count / total_train) * 100
                    sample_info.append(f"{class_name}: {count}张({percentage:.1f}%)")
                
                if len(train_counts) > 5:
                    sample_info.append(f"...共{len(train_counts)}个类别")
                
                self.result.add_passed("classification_sample_distribution", 
                                     f"样本分布: {'; '.join(sample_info)}", 
                                     {"distribution": train_counts})
                
        except Exception as e:
            self.result.add_error("classification_dataset_check", f"检查分类数据集时出错: {str(e)}", str(e))


def check_training_environment(trainer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    快速检查训练环境（便捷函数）
    
    Args:
        trainer_id: 训练器ID
        config: 训练配置
        
    Returns:
        检查结果字典
    """
    checker = TrainingEnvironmentChecker()
    result = checker.check_all(trainer_id, config)
    return result.to_dict()


if __name__ == "__main__":
    # 测试代码
    test_config = {
        "data": "data.yaml",
        "model": "yolov8n.pt",
        "epochs": 100,
        "batch_size": 16,
        "device": "0",
        "project": "runs/train",
        "name": "test_check"
    }
    
    from core.trainer_registry import initialize_registry
    initialize_registry()
    
    result = check_training_environment("yolo_v8", test_config)
    print(json.dumps(result, indent=2, ensure_ascii=False))