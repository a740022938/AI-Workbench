"""
训练中心管理器 - 训练中心的核心协调器
负责整合注册表、环境检查、体检报告，提供统一的训练中心接口
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from core.trainer_registry import TrainerRegistry, registry
from core.training_environment_checker import TrainingEnvironmentChecker, check_training_environment


class TrainingHealthReport:
    """训练前体检报告"""
    
    def __init__(self, trainer_id: str, config: Dict[str, Any]):
        self.trainer_id = trainer_id
        self.config = config
        self.check_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.environment_result = None
        self.trainer_metadata = None
        self.overall_status = "pending"  # pending, checking, passed, warning, error
        self.can_start_training = False
        self.suggestions = []
        
    def run_full_check(self) -> Dict[str, Any]:
        """执行完整检查"""
        self.overall_status = "checking"
        
        # 获取训练器元数据
        self.trainer_metadata = TrainerRegistry.get_trainer(self.trainer_id)
        if not self.trainer_metadata:
            self.overall_status = "error"
            self.can_start_training = False
            self.suggestions.append(f"训练器 '{self.trainer_id}' 未注册")
            return self.to_dict()
        
        # 执行环境检查
        checker = TrainingEnvironmentChecker()
        self.environment_result = checker.check_all(self.trainer_id, self.config)
        
        # 评估整体状态
        if self.environment_result.errors:
            self.overall_status = "error"
            self.can_start_training = False
        elif self.environment_result.warnings:
            self.overall_status = "warning"
            self.can_start_training = True
        else:
            self.overall_status = "passed"
            self.can_start_training = True
        
        # 生成建议
        self._generate_suggestions()
        
        return self.to_dict()
    
    def _generate_suggestions(self):
        """生成训练建议"""
        if not self.environment_result:
            return
        
        # 基于错误生成建议
        for error in self.environment_result.errors:
            if "dependency" in error["name"]:
                dep = error.get("details", "未知")
                self.suggestions.append(f"安装依赖包: pip install {dep}")
            elif "model_file" in error["name"]:
                self.suggestions.append("下载或指定正确的模型权重文件")
            elif "data_config" in error["name"]:
                self.suggestions.append("创建或指定正确的数据配置文件 (data.yaml)")
            elif "output_directory" in error["name"]:
                self.suggestions.append("检查输出目录权限或更改输出路径")
        
        # 基于警告生成建议
        for warning in self.environment_result.warnings:
            if "missing_dependencies" in warning["name"]:
                deps = warning.get("details", [])
                if deps:
                    self.suggestions.append(f"安装缺失依赖: pip install {' '.join(deps)}")
            elif "gpu" in warning["name"]:
                self.suggestions.append("考虑使用CPU训练或检查CUDA安装")
        
        # 通用建议
        if self.can_start_training:
            if "epochs" not in self.config or self.config.get("epochs", 0) <= 0:
                self.suggestions.append("建议设置合理的训练轮数 (epochs)")
            if "batch_size" not in self.config or self.config.get("batch_size", 0) <= 0:
                self.suggestions.append("建议根据GPU显存设置合适的批大小 (batch_size)")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "trainer_id": self.trainer_id,
            "check_time": self.check_time,
            "overall_status": self.overall_status,
            "can_start_training": self.can_start_training,
            "suggestions": self.suggestions,
            "trainer_metadata": {
                "trainer_id": self.trainer_metadata.trainer_id if self.trainer_metadata else None,
                "display_name": self.trainer_metadata.display_name if self.trainer_metadata else None,
                "task_type": self.trainer_metadata.task_type if self.trainer_metadata else None,
                "framework": self.trainer_metadata.framework if self.trainer_metadata else None,
                "description": self.trainer_metadata.description if self.trainer_metadata else None,
            } if self.trainer_metadata else None,
            "config": self.config,
        }
        
        if self.environment_result:
            result["environment_check"] = self.environment_result.to_dict()
        
        return result
    
    def get_summary(self) -> str:
        """获取摘要信息"""
        if not self.environment_result:
            return "未执行检查"
        
        total = len(self.environment_result.passed) + len(self.environment_result.warnings) + len(self.environment_result.errors)
        
        if self.overall_status == "passed":
            status_emoji = "✅"
        elif self.overall_status == "warning":
            status_emoji = "⚠️"
        elif self.overall_status == "error":
            status_emoji = "❌"
        else:
            status_emoji = "⏳"
        
        summary = f"{status_emoji} 训练前体检报告\n"
        summary += f"训练器: {self.trainer_metadata.display_name if self.trainer_metadata else self.trainer_id}\n"
        summary += f"检查时间: {self.check_time}\n"
        summary += f"检查项: {total}个 (通过: {len(self.environment_result.passed)}, "
        summary += f"警告: {len(self.environment_result.warnings)}, 错误: {len(self.environment_result.errors)})\n"
        summary += f"训练状态: {'可启动训练' if self.can_start_training else '存在错误，无法训练'}\n"
        
        if self.suggestions:
            summary += f"建议: {self.suggestions[0] if len(self.suggestions) == 1 else f'共{len(self.suggestions)}条建议'}\n"
        
        return summary


class TrainingCenterManager:
    """训练中心管理器"""
    
    def __init__(self):
        self.health_reports = {}  # 缓存体检报告
        self.current_trainer_id = None
        self.current_config = None
        
    def get_available_trainers(self) -> List[Dict[str, Any]]:
        """获取可用训练器列表"""
        trainers = []
        for metadata in TrainerRegistry.list_trainers():
            # 判断是否为占位训练器
            is_placeholder = metadata.backend_class.__name__ == "PlaceholderTrainingBackend"
            
            trainers.append({
                "trainer_id": metadata.trainer_id,
                "display_name": metadata.display_name,
                "task_type": metadata.task_type,
                "framework": metadata.framework,
                "description": metadata.description,
                "required_config_keys": metadata.required_config_keys,
                "required_dependencies": metadata.required_dependencies,
                # 第二期新增信息
                "is_placeholder": is_placeholder,
                "can_train": not is_placeholder and metadata.trainer_id in ["yolo_v8", "classification"],  # YOLO和分类可真实训练
                "supported": metadata.trainer_id in ["yolo_v8", "classification"],  # 支持YOLO和分类
            })
        return trainers
    
    def get_trainer_info(self, trainer_id: str) -> Optional[Dict[str, Any]]:
        """获取训练器详细信息"""
        metadata = TrainerRegistry.get_trainer(trainer_id)
        if not metadata:
            return None
        
        return {
            "trainer_id": metadata.trainer_id,
            "display_name": metadata.display_name,
            "task_type": metadata.task_type,
            "framework": metadata.framework,
            "description": metadata.description,
            "required_config_keys": metadata.required_config_keys,
            "required_dependencies": metadata.required_dependencies,
            "required_files": metadata.required_files,
            "default_config": metadata.default_config,
            # 第二期新增字段
            "config_schema": getattr(metadata, 'config_schema', {}),
            "result_parsers": getattr(metadata, 'result_parsers', []),
            "metric_names": getattr(metadata, 'metric_names', []),
            "log_patterns": getattr(metadata, 'log_patterns', {}),
        }
    
    def run_health_check(self, trainer_id: str, config: Dict[str, Any]) -> TrainingHealthReport:
        """
        运行训练前体检
        
        Args:
            trainer_id: 训练器ID
            config: 训练配置
            
        Returns:
            体检报告对象
        """
        # 创建报告
        report = TrainingHealthReport(trainer_id, config)
        report.run_full_check()
        
        # 缓存报告（以配置哈希为键）
        config_hash = hash(json.dumps(config, sort_keys=True))
        self.health_reports[config_hash] = report
        
        # 更新当前状态
        self.current_trainer_id = trainer_id
        self.current_config = config
        
        return report
    
    def quick_check(self, trainer_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        快速检查（返回字典格式）
        
        Args:
            trainer_id: 训练器ID
            config: 训练配置
            
        Returns:
            检查结果字典
        """
        return check_training_environment(trainer_id, config)
    
    def create_backend(self, trainer_id: str, **kwargs):
        """
        创建训练后端实例
        
        Args:
            trainer_id: 训练器ID
            **kwargs: 传递给后端的参数
            
        Returns:
            后端实例
        """
        return TrainerRegistry.create_backend(trainer_id, **kwargs)
    
    def get_training_suggestion(self, trainer_id: str, config: Dict[str, Any]) -> List[str]:
        """
        获取训练建议
        
        Args:
            trainer_id: 训练器ID
            config: 训练配置
            
        Returns:
            建议列表
        """
        report = self.run_health_check(trainer_id, config)
        return report.suggestions
    
    def generate_config_template(self, trainer_id: str) -> Dict[str, Any]:
        """
        生成配置模板
        
        Args:
            trainer_id: 训练器ID
            
        Returns:
            配置模板
        """
        metadata = TrainerRegistry.get_trainer(trainer_id)
        if not metadata:
            return {}
        
        template = metadata.default_config.copy()
        template.update({
            "data": "path/to/data.yaml",
            "model": "path/to/model.pt",
            "epochs": 100,
            "batch_size": 16,
            "imgsz": 640,
            "device": "0",
            "project": "runs/train",
            "name": "exp",
        })
        
        return template
    
    def export_health_report(self, report: TrainingHealthReport, format: str = "json") -> str:
        """
        导出体检报告
        
        Args:
            report: 体检报告
            format: 导出格式 (json, text)
            
        Returns:
            导出内容
        """
        if format == "json":
            return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        elif format == "text":
            text = report.get_summary() + "\n\n"
            
            if report.environment_result:
                # 错误项
                if report.environment_result.errors:
                    text += "❌ 错误项:\n"
                    for error in report.environment_result.errors:
                        text += f"  - {error['name']}: {error['message']}\n"
                    text += "\n"
                
                # 警告项
                if report.environment_result.warnings:
                    text += "⚠️ 警告项:\n"
                    for warning in report.environment_result.warnings:
                        text += f"  - {warning['name']}: {warning['message']}\n"
                    text += "\n"
                
                # 通过项
                if report.environment_result.passed:
                    text += "✅ 通过项:\n"
                    for passed in report.environment_result.passed:
                        text += f"  - {passed['name']}: {passed['message']}\n"
            
            # 建议
            if report.suggestions:
                text += "\n💡 建议:\n"
                for i, suggestion in enumerate(report.suggestions, 1):
                    text += f"  {i}. {suggestion}\n"
            
            return text
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def find_latest_training_result(self, trainer_id: str):
        """
        查找最新的训练结果文件
        
        Args:
            trainer_id: 训练器ID
            
        Returns:
            最新结果文件路径，如果未找到则返回None
        """
        import glob
        import os
        
        if trainer_id == "classification":
            # 查找分类训练结果
            search_patterns = [
                "runs/classification/*/training_log.json",
                "runs/classification/**/training_log.json",
            ]
            
            result_files = []
            for pattern in search_patterns:
                files = glob.glob(pattern, recursive=True)
                result_files.extend(files)
            
            if result_files:
                # 按修改时间排序，获取最新的文件
                result_files.sort(key=os.path.getmtime, reverse=True)
                return result_files[0]
        
        elif trainer_id == "yolo_v8":
            # 查找YOLO训练结果
            search_patterns = [
                "runs/train/*/training_log.json",
                "runs/train/**/training_log.json",
            ]
            
            result_files = []
            for pattern in search_patterns:
                files = glob.glob(pattern, recursive=True)
                result_files.extend(files)
            
            if result_files:
                result_files.sort(key=os.path.getmtime, reverse=True)
                return result_files[0]
        
        return None
    
    def list_training_results(self, trainer_id: str, limit: int = 20) -> list:
        """
        列出训练结果文件（按时间倒序）
        
        Args:
            trainer_id: 训练器ID
            limit: 最多返回的结果数量
            
        Returns:
            训练结果信息列表，每个元素包含：
            - path: 结果文件路径
            - name: 实验名称
            - timestamp: 修改时间戳
            - config: 配置信息（如果可加载）
        """
        import glob
        import os
        import json
        from datetime import datetime
        
        result_files = []
        
        if trainer_id == "classification":
            # 查找分类训练结果
            search_patterns = [
                "runs/classification/*/training_log.json",
                "runs/classification/**/training_log.json",
            ]
            
            for pattern in search_patterns:
                files = glob.glob(pattern, recursive=True)
                result_files.extend(files)
        
        elif trainer_id == "yolo_v8":
            # 查找YOLO训练结果
            search_patterns = [
                "runs/train/*/training_log.json",
                "runs/train/**/training_log.json",
            ]
            
            for pattern in search_patterns:
                files = glob.glob(pattern, recursive=True)
                result_files.extend(files)
        
        else:
            return []
        
        # 去重
        result_files = list(set(result_files))
        
        # 按修改时间排序（最新的在前）
        result_files.sort(key=os.path.getmtime, reverse=True)
        
        # 限制数量
        result_files = result_files[:limit]
        
        # 提取基本信息
        results = []
        for file_path in result_files:
            try:
                # 实验名称是父目录名
                exp_name = os.path.basename(os.path.dirname(file_path))
                
                # 获取修改时间
                mod_time = os.path.getmtime(file_path)
                mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
                
                # 尝试加载配置获取更多信息
                config_info = {}
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                    
                    config = log_data.get("config", {})
                    config_info = {
                        "model_name": config.get("model_name", "未知"),
                        "epochs": config.get("epochs", 0),
                        "num_classes": config.get("num_classes", 0),
                        "batch_size": config.get("batch_size", 0),
                        "learning_rate": config.get("learning_rate", 0),
                    }
                    
                    # 提取最佳指标（如果存在）
                    epochs = log_data.get("epochs", [])
                    if epochs:
                        # 找到最佳验证准确率
                        val_acc_values = [e.get("val_accuracy", 0) for e in epochs if "val_accuracy" in e]
                        if val_acc_values:
                            best_val_acc = max(val_acc_values)
                            best_epoch = val_acc_values.index(best_val_acc) + 1
                            final_val_acc = val_acc_values[-1] if val_acc_values else 0
                            
                            config_info.update({
                                "best_epoch": best_epoch,
                                "best_val_acc": best_val_acc,
                                "final_val_acc": final_val_acc,
                            })
                
                except (json.JSONDecodeError, KeyError, Exception):
                    # 如果无法解析JSON，只提供基础信息
                    pass
                
                results.append({
                    "path": file_path,
                    "name": exp_name,
                    "timestamp": mod_time_str,
                    "timestamp_raw": mod_time,
                    "config": config_info,
                })
                
            except Exception:
                # 跳过无法处理的文件
                continue
        
        return results


# 全局训练中心管理器实例
training_center = TrainingCenterManager()


def get_training_center():
    """获取训练中心管理器实例（单例）"""
    return training_center


if __name__ == "__main__":
    # 测试代码
    from core.trainer_registry import initialize_registry
    initialize_registry()
    
    center = get_training_center()
    
    print("=== 可用训练器 ===")
    trainers = center.get_available_trainers()
    for trainer in trainers:
        print(f"- {trainer['display_name']} ({trainer['trainer_id']}): {trainer['description']}")
    
    print("\n=== 训练前体检 ===")
    test_config = {
        "data": "data.yaml",
        "model": "yolov8n.pt",
        "epochs": 100,
        "batch_size": 16,
        "device": "0",
    }
    
    report = center.run_health_check("yolo_v8", test_config)
    print(center.export_health_report(report, "text"))