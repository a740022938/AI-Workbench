"""
训练器注册表 - 模型/训练器注册中心
负责管理所有可用的训练后端，提供统一的注册、查询和实例化接口。
"""

from typing import Dict, List, Optional, Any, Type
import importlib


class TrainerMetadata:
    """训练器元数据"""
    
    def __init__(
        self,
        trainer_id: str,
        display_name: str,
        task_type: str,
        framework: str,
        backend_class: Type,
        required_config_keys: List[str],
        required_dependencies: List[str],
        required_files: List[str],
        description: str = "",
        default_config: Optional[Dict[str, Any]] = None,
        config_schema: Optional[Dict[str, Any]] = None,
        result_parsers: Optional[List[str]] = None,
        metric_names: Optional[List[str]] = None,
        log_patterns: Optional[Dict[str, str]] = None
    ):
        """
        初始化训练器元数据
        
        Args:
            trainer_id: 训练器唯一标识（小写字母+下划线，如 'yolo_v8'）
            display_name: 显示名称（如 'YOLOv8'）
            task_type: 任务类型（如 'object_detection', 'classification', 'segmentation'）
            framework: 框架名称（如 'ultralytics', 'pytorch', 'tensorflow'）
            backend_class: 后端实现类
            required_config_keys: 必需配置项列表（如 ['data', 'model', 'epochs']）
            required_dependencies: 必需依赖包列表（如 ['torch', 'ultralytics']）
            required_files: 必需文件列表（如 ['data.yaml', 'model.pt']）
            description: 训练器描述
            default_config: 默认配置
            config_schema: 配置字段描述（为动态表单预留）
            result_parsers: 结果解析器列表（为监控适配预留）
            metric_names: 指标名称列表（为监控适配预留）
            log_patterns: 日志解析模式（为监控适配预留）
        """
        self.trainer_id = trainer_id
        self.display_name = display_name
        self.task_type = task_type
        self.framework = framework
        self.backend_class = backend_class
        self.required_config_keys = required_config_keys
        self.required_dependencies = required_dependencies
        self.required_files = required_files
        self.description = description
        self.default_config = default_config or {}
        
        # 第二期新增：动态配置适配口字段
        self.config_schema = config_schema or {}
        self.result_parsers = result_parsers or []
        self.metric_names = metric_names or []
        self.log_patterns = log_patterns or {}
    
    def __repr__(self):
        return f"TrainerMetadata(id={self.trainer_id}, name={self.display_name}, task={self.task_type})"


class PlaceholderTrainingBackend:
    """占位训练后端（用于示例训练器，不实际执行训练）"""
    def __init__(self):
        self.process = None
        self.is_running = False
    
    def start(self, training_config, monitor_window=None):
        if monitor_window:
            monitor_window.append_log(f"[占位训练器] 这是一个示例训练器，不实际执行训练")
            monitor_window.append_log(f"[占位训练器] 训练配置: {training_config}")
        return False
    
    def stop(self, monitor_window=None):
        if monitor_window:
            monitor_window.append_log(f"[占位训练器] 停止训练（占位）")
        return False
    
    def resume(self, training_config, monitor_window=None):
        if monitor_window:
            monitor_window.append_log(f"[占位训练器] 继续训练（占位）")
        return False
    
    def get_status(self):
        return {"is_running": self.is_running, "placeholder": True}


class TrainerRegistry:
    """训练器注册表（单例模式）"""
    
    _instance = None
    _registry: Dict[str, TrainerMetadata] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(
        cls,
        trainer_id: str,
        display_name: str,
        task_type: str,
        framework: str,
        backend_class: Type,
        required_config_keys: List[str],
        required_dependencies: List[str],
        required_files: List[str],
        description: str = "",
        default_config: Optional[Dict[str, Any]] = None,
        config_schema: Optional[Dict[str, Any]] = None,
        result_parsers: Optional[List[str]] = None,
        metric_names: Optional[List[str]] = None,
        log_patterns: Optional[Dict[str, str]] = None
    ) -> None:
        """
        注册训练器
        
        Args:
            参数同 TrainerMetadata
        """
        metadata = TrainerMetadata(
            trainer_id=trainer_id,
            display_name=display_name,
            task_type=task_type,
            framework=framework,
            backend_class=backend_class,
            required_config_keys=required_config_keys,
            required_dependencies=required_dependencies,
            required_files=required_files,
            description=description,
            default_config=default_config or {},
            config_schema=config_schema,
            result_parsers=result_parsers,
            metric_names=metric_names,
            log_patterns=log_patterns
        )
        cls._registry[trainer_id] = metadata
    
    @classmethod
    def get_trainer(cls, trainer_id: str) -> Optional[TrainerMetadata]:
        """获取训练器元数据"""
        return cls._registry.get(trainer_id)
    
    @classmethod
    def list_trainers(cls) -> List[TrainerMetadata]:
        """列出所有已注册训练器"""
        return list(cls._registry.values())
    
    @classmethod
    def get_trainer_ids(cls) -> List[str]:
        """获取所有训练器ID"""
        return list(cls._registry.keys())
    
    @classmethod
    def create_backend(cls, trainer_id: str, **kwargs):
        """
        创建训练器后端实例
        
        Args:
            trainer_id: 训练器ID
            **kwargs: 传递给后端构造函数的参数
            
        Returns:
            后端实例
            
        Raises:
            ValueError: 训练器不存在
        """
        metadata = cls.get_trainer(trainer_id)
        if not metadata:
            raise ValueError(f"训练器 '{trainer_id}' 未注册")
        
        return metadata.backend_class(**kwargs)
    
    @classmethod
    def check_dependency(cls, trainer_id: str) -> Dict[str, bool]:
        """
        检查训练器依赖是否满足
        
        Args:
            trainer_id: 训练器ID
            
        Returns:
            字典 {依赖包: 是否可用}
        """
        metadata = cls.get_trainer(trainer_id)
        if not metadata:
            return {}
        
        result = {}
        for dep in metadata.required_dependencies:
            try:
                importlib.import_module(dep)
                result[dep] = True
            except ImportError:
                result[dep] = False
        
        return result
    
    @classmethod
    def validate_config(cls, trainer_id: str, config: Dict[str, Any]) -> List[str]:
        """
        验证配置是否满足训练器要求
        
        Args:
            trainer_id: 训练器ID
            config: 配置字典
            
        Returns:
            缺失的必需配置项列表
        """
        metadata = cls.get_trainer(trainer_id)
        if not metadata:
            return [f"训练器 '{trainer_id}' 未注册"]
        
        missing = []
        for key in metadata.required_config_keys:
            if key not in config or config[key] is None or config[key] == "":
                missing.append(key)
        
        return missing


# 全局注册表实例
registry = TrainerRegistry()


def register_yolo_trainer():
    """注册YOLO训练器（默认实现）"""
    try:
        from core.training_backends.yolo_backend import YoloTrainingBackend
        
        # YOLO配置字段描述（为动态表单预留）
        yolo_config_schema = {
            "data": {"type": "string", "label": "数据配置文件", "required": True, "description": "YOLO格式的数据配置文件路径 (data.yaml)"},
            "model": {"type": "string", "label": "模型文件", "required": True, "description": "预训练模型权重文件路径 (.pt)"},
            "epochs": {"type": "integer", "label": "训练轮数", "required": True, "default": 100, "min": 1, "max": 1000},
            "batch_size": {"type": "integer", "label": "批大小", "required": False, "default": 16, "min": 1, "max": 256},
            "imgsz": {"type": "integer", "label": "图像尺寸", "required": False, "default": 640, "min": 32, "max": 2048},
            "device": {"type": "string", "label": "训练设备", "required": False, "default": "0", "description": "GPU设备ID或'cpu'"},
            "project": {"type": "string", "label": "项目目录", "required": False, "default": "runs/train"},
            "name": {"type": "string", "label": "实验名称", "required": False, "default": "exp"},
        }
        
        # YOLO日志解析模式
        yolo_log_patterns = {
            "epoch": r"epoch\s+(\d+)/(\d+)",
            "loss": r"loss:\s+([\d.]+)",
            "metrics": r"metrics/([\w-]+):\s+([\d.]+)",
            "lr": r"lr:\s+([\d.e+-]+)",
        }
        
        TrainerRegistry.register(
            trainer_id="yolo_v8",
            display_name="YOLOv8",
            task_type="object_detection",
            framework="ultralytics",
            backend_class=YoloTrainingBackend,
            required_config_keys=["data", "model", "epochs"],
            required_dependencies=["torch", "ultralytics"],
            required_files=["data.yaml", "model.pt"],
            description="YOLOv8目标检测训练器，基于Ultralytics框架",
            default_config={
                "epochs": 100,
                "batch_size": 16,
                "imgsz": 640,
                "device": "0",
                "project": "runs/train",
                "name": "exp",
                "workers": 4,
                "patience": 50,
                "exist_ok": True,
                "save": True,
                "cache": False,
                "resume": False
            },
            config_schema=yolo_config_schema,
            result_parsers=["yolo_results_parser"],
            metric_names=["mAP50", "mAP50-95", "precision", "recall"],
            log_patterns=yolo_log_patterns
        )
        return True
    except ImportError as e:
        print(f"[注册表] 无法注册YOLO训练器: {e}")
        return False


def register_classification_trainer():
    """注册分类训练器（真实可训练）"""
    try:
        from core.training_backends.classification_backend import ClassificationTrainingBackend
        
        # 分类训练器配置字段描述（增强版）
        classification_config_schema = {
            "data_dir": {"type": "string", "label": "数据目录", "required": True, "description": "分类数据集目录路径", "subtype": "path"},
            "num_classes": {"type": "int", "label": "类别数量", "required": True, "default": 10, "min": 2, "max": 1000},
            "model_name": {"type": "choice", "label": "模型名称", "required": True, "default": "resnet18", 
                          "choices": ["resnet18", "resnet34", "resnet50", "simple_cnn"]},
            "epochs": {"type": "int", "label": "训练轮数", "required": True, "default": 10, "min": 1, "max": 1000},
            "batch_size": {"type": "int", "label": "批大小", "required": False, "default": 32, "min": 1, "max": 256},
            "learning_rate": {"type": "float", "label": "学习率", "required": False, "default": 0.001, "min": 0.00001, "max": 1.0},
            "optimizer": {"type": "choice", "label": "优化器", "required": False, "default": "adam", 
                         "choices": ["adam", "sgd"]},
            "device": {"type": "choice", "label": "训练设备", "required": False, "default": "cuda", 
                      "choices": ["cuda", "cpu"], "description": "cuda: GPU训练, cpu: CPU训练"},
            "project": {"type": "string", "label": "项目目录", "required": False, "default": "runs/classification"},
            "name": {"type": "string", "label": "实验名称", "required": False, "default": "exp"},
            
            # 数据增强配置
            "use_augmentation": {"type": "bool", "label": "启用数据增强", "required": False, "default": True, 
                               "description": "是否对训练数据进行增强"},
            "augmentation_random_horizontal_flip": {"type": "bool", "label": "随机水平翻转", "required": False, "default": True,
                                                  "description": "随机水平翻转增强，概率0.5"},
            "augmentation_random_rotation": {"type": "float", "label": "随机旋转角度", "required": False, "default": 10.0,
                                           "min": 0.0, "max": 45.0, "description": "随机旋转角度范围（度），0表示禁用"},
            "augmentation_color_jitter": {"type": "bool", "label": "颜色抖动", "required": False, "default": False,
                                        "description": "是否启用颜色抖动增强"},
            "augmentation_color_jitter_brightness": {"type": "float", "label": "亮度抖动", "required": False, "default": 0.2,
                                                   "min": 0.0, "max": 1.0, "description": "亮度抖动强度，0表示无抖动"},
            "augmentation_color_jitter_contrast": {"type": "float", "label": "对比度抖动", "required": False, "default": 0.2,
                                                 "min": 0.0, "max": 1.0, "description": "对比度抖动强度"},
            "augmentation_color_jitter_saturation": {"type": "float", "label": "饱和度抖动", "required": False, "default": 0.2,
                                                   "min": 0.0, "max": 1.0, "description": "饱和度抖动强度"},
            "augmentation_color_jitter_hue": {"type": "float", "label": "色相抖动", "required": False, "default": 0.1,
                                            "min": 0.0, "max": 0.5, "description": "色相抖动强度"},
            
            # 预训练权重配置
            "use_pretrained_weights": {"type": "bool", "label": "使用预训练权重", "required": False, "default": True,
                                     "description": "是否使用ImageNet预训练权重（仅支持ResNet系列）"},
            
            # 学习率调度配置
            "scheduler_type": {"type": "choice", "label": "学习率调度器", "required": False, "default": "none",
                             "choices": ["none", "step", "cosine"], "description": "学习率调度器类型"},
            "scheduler_step_size": {"type": "int", "label": "调度步长", "required": False, "default": 30,
                                  "min": 1, "max": 1000, "description": "StepLR调度器的步长（epochs）"},
            "scheduler_gamma": {"type": "float", "label": "调度衰减率", "required": False, "default": 0.1,
                              "min": 0.01, "max": 1.0, "description": "学习率衰减因子"},
            "scheduler_t_max": {"type": "int", "label": "余弦调度周期", "required": False, "default": 10,
                              "min": 1, "max": 1000, "description": "CosineAnnealingLR的T_max参数"},
        }
        
        # 分类训练器日志模式
        classification_log_patterns = {
            "epoch": r"Epoch (\d+)/(\d+)",
            "train_loss": r"Train Loss: ([\d.]+)",
            "train_acc": r"Train Acc: ([\d.]+)%",
            "val_loss": r"Val Loss: ([\d.]+)",
            "val_acc": r"Val Acc: ([\d.]+)%",
            "batch_loss": r"Batch \d+, Loss: ([\d.]+)",
        }
        
        TrainerRegistry.register(
            trainer_id="classification",
            display_name="图像分类",
            task_type="classification",
            framework="pytorch",
            backend_class=ClassificationTrainingBackend,
            required_config_keys=["data_dir", "num_classes", "model_name", "epochs"],
            required_dependencies=["torch", "torchvision"],
            required_files=[],  # 分类训练器不需要特定文件，只需要数据目录结构
            description="基于PyTorch的图像分类训练器，支持ResNet等常见模型。需要真实数据集目录结构：data_dir/train/类别1/, data_dir/val/类别1/。数据目录必须存在且包含至少2个类别。",
            default_config={
                "data_dir": "data/classification",
                "num_classes": 10,
                "model_name": "resnet18",
                "epochs": 10,
                "batch_size": 32,
                "learning_rate": 0.001,
                "optimizer": "adam",
                "device": "cuda",
                "project": "runs/classification",
                "name": "exp",
                
                # 数据增强默认配置
                "use_augmentation": True,
                "augmentation_random_horizontal_flip": True,
                "augmentation_random_rotation": 10.0,
                "augmentation_color_jitter": False,
                "augmentation_color_jitter_brightness": 0.2,
                "augmentation_color_jitter_contrast": 0.2,
                "augmentation_color_jitter_saturation": 0.2,
                "augmentation_color_jitter_hue": 0.1,
                
                # 预训练权重默认配置
                "use_pretrained_weights": True,
                
                # 学习率调度默认配置
                "scheduler_type": "none",
                "scheduler_step_size": 30,
                "scheduler_gamma": 0.1,
                "scheduler_t_max": 10,
            },
            config_schema=classification_config_schema,
            result_parsers=["classification_results_parser"],
            metric_names=["train_loss", "train_accuracy", "val_loss", "val_accuracy"],
            log_patterns=classification_log_patterns
        )
        return True
    except ImportError as e:
        print(f"[注册表] 无法注册分类训练器: {e}")
        # 如果分类后端不可用，注册为占位训练器
        TrainerRegistry.register(
            trainer_id="classification",
            display_name="图像分类（需要安装torch）",
            task_type="classification",
            framework="pytorch",
            backend_class=PlaceholderTrainingBackend,
            required_config_keys=["data_dir", "num_classes", "model_name", "epochs"],
            required_dependencies=["torch", "torchvision"],
            required_files=[],
            description="基于PyTorch的图像分类训练器（需要安装torch和torchvision）",
            default_config={
                "data_dir": "data/classification",
                "num_classes": 10,
                "model_name": "resnet18",
                "epochs": 10,
                "batch_size": 32,
                "learning_rate": 0.001,
                "optimizer": "adam",
                "device": "cuda"
            }
        )
        return False


def initialize_registry():
    """初始化注册表（注册所有可用训练器）"""
    # 清空注册表（防止重复注册）
    TrainerRegistry._registry.clear()
    
    # 注册YOLO训练器
    yolo_registered = register_yolo_trainer()
    
    # 注册分类训练器（真实可训练）
    classification_registered = register_classification_trainer()
    
    # 注册其他训练器（示例/占位）
    
    # 2. 分割训练器示例
    TrainerRegistry.register(
        trainer_id="segmentation_example",
        display_name="语义分割示例",
        task_type="segmentation",
        framework="pytorch",
        backend_class=PlaceholderTrainingBackend,
        required_config_keys=["image_dir", "mask_dir", "num_classes"],
        required_dependencies=["torch", "segmentation_models_pytorch"],
        required_files=["train_images", "train_masks", "class_colors.json"],
        description="语义分割训练器示例（占位），基于PyTorch和segmentation-models-pytorch",
        default_config={
            "image_dir": "data/images",
            "mask_dir": "data/masks",
            "num_classes": 21,
            "model_name": "unet",
            "encoder": "resnet34",
            "epochs": 100,
            "batch_size": 4,
            "learning_rate": 0.0001
        }
    )
    
    # 3. 自定义脚本训练器
    TrainerRegistry.register(
        trainer_id="custom_script",
        display_name="自定义脚本",
        task_type="custom",
        framework="python",
        backend_class=PlaceholderTrainingBackend,
        required_config_keys=["script_path", "requirements"],
        required_dependencies=[],
        required_files=["train_script.py", "requirements.txt"],
        description="自定义训练脚本执行器（占位），支持任意Python训练脚本",
        default_config={
            "script_path": "train.py",
            "requirements": "requirements.txt",
            "python_path": "python",
            "args": "--epochs 100 --batch-size 32",
            "env": {}
        }
    )
    
    trainers = TrainerRegistry.list_trainers()
    print(f"[注册表] 初始化完成，已注册 {len(trainers)} 个训练器: {[t.trainer_id for t in trainers]}")
    
    # 显示训练器状态
    for trainer in trainers:
        is_placeholder = trainer.backend_class.__name__ == "PlaceholderTrainingBackend"
        status = "可训练" if not is_placeholder else "占位"
        print(f"  - {trainer.trainer_id}: {status}")
    
    return len(trainers) > 0


# 自动初始化
if __name__ != "__main__":
    initialize_registry()