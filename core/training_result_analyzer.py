"""
训练结果分析器 - 解析和展示训练结果
支持分类训练器的结果分析
"""

import json
import os
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TrainingResult:
    """训练结果数据类"""
    trainer_id: str
    log_path: str
    config: Dict[str, Any]
    start_time: str
    end_time: str
    epochs: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    summary: Dict[str, Any]
    capabilities: Dict[str, Any]  # 使用的增强能力
    notes: Dict[str, str]  # 实验批注（实验备注、改动说明、重新训练原因等）
    tags: List[str]  # 实验标签
    is_favorite: bool  # 是否收藏
    is_important: bool  # 是否重要
    is_archived: bool  # 是否归档（安全清理方案）


@dataclass
class ClassificationTrainingResult(TrainingResult):
    """分类训练结果数据类"""
    train_loss_values: List[float]
    train_acc_values: List[float]
    val_loss_values: List[float]
    val_acc_values: List[float]
    learning_rate_values: List[float]
    best_epoch: int
    best_val_acc: float
    best_val_loss: float
    final_train_acc: float
    final_train_loss: float
    final_val_acc: float
    final_val_loss: float


class TrainingResultAnalyzer:
    """训练结果分析器基类"""
    
    def __init__(self):
        pass
    
    def load_result(self, log_path: str) -> Optional[TrainingResult]:
        """
        加载训练结果
        
        Args:
            log_path: 训练日志文件路径
            
        Returns:
            训练结果对象，如果加载失败则返回None
        """
        if not os.path.exists(log_path):
            return None
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # 确定训练器类型
            trainer_id = self._detect_trainer_type(log_data)
            
            # 根据不同训练器类型解析
            if trainer_id == "classification":
                return self._parse_classification_result(log_path, log_data)
            else:
                # 通用解析
                return self._parse_generic_result(log_path, log_data, trainer_id)
                
        except Exception as e:
            print(f"加载训练结果失败: {e}")
            return None
    
    def _detect_trainer_type(self, log_data: Dict[str, Any]) -> str:
        """检测训练器类型"""
        config = log_data.get("config", {})
        
        # 根据配置特征判断
        if "data_dir" in config and "num_classes" in config:
            return "classification"
        elif "data" in config and "model" in config:
            return "yolo_v8"
        else:
            return "unknown"
    
    def _parse_generic_result(self, log_path: str, log_data: Dict[str, Any], trainer_id: str) -> TrainingResult:
        """解析通用训练结果"""
        epochs = log_data.get("epochs", [])
        
        # 计算基础指标
        metrics = {}
        if epochs:
            # 提取关键指标
            train_losses = [e.get("train_loss", 0) for e in epochs if "train_loss" in e]
            val_losses = [e.get("val_loss", 0) for e in epochs if "val_loss" in e]
            train_accs = [e.get("train_accuracy", 0) for e in epochs if "train_accuracy" in e]
            val_accs = [e.get("val_accuracy", 0) for e in epochs if "val_accuracy" in e]
            
            if train_losses:
                metrics["final_train_loss"] = train_losses[-1]
                metrics["min_train_loss"] = min(train_losses)
            if val_losses:
                metrics["final_val_loss"] = val_losses[-1]
                metrics["min_val_loss"] = min(val_losses)
            if train_accs:
                metrics["final_train_accuracy"] = train_accs[-1]
                metrics["max_train_accuracy"] = max(train_accs)
            if val_accs:
                metrics["final_val_accuracy"] = val_accs[-1]
                metrics["max_val_accuracy"] = max(val_accs)
        
        # 构建结果摘要
        summary = {
            "epochs_completed": len(epochs),
            "has_validation": any("val_loss" in e for e in epochs),
            "training_time": self._calculate_training_time(log_data),
            "model_saved": log_data.get("model_saved", ""),
        }
        
        # 能力使用情况
        capabilities = {
            "augmentation_used": log_data.get("augmentation_used", False),
            "pretrained_used": log_data.get("pretrained_used", False),
            "scheduler_used": log_data.get("scheduler_used", "none"),
        }
        
        # 实验批注
        notes = log_data.get("notes", {
            "experiment_notes": "",
            "change_description": "",
            "reason_for_retraining": "",
            "source_experiment": ""  # 来源实验信息，用于再训练跟踪
        })
        
        # 实验标签/收藏/重要标记/归档状态
        tags = log_data.get("tags", [])
        is_favorite = log_data.get("is_favorite", False)
        is_important = log_data.get("is_important", False)
        is_archived = log_data.get("is_archived", False)
        
        return TrainingResult(
            trainer_id=trainer_id,
            log_path=log_path,
            config=log_data.get("config", {}),
            start_time=log_data.get("start_time", ""),
            end_time=log_data.get("end_time", ""),
            epochs=epochs,
            metrics=metrics,
            summary=summary,
            capabilities=capabilities,
            notes=notes,
            tags=tags,
            is_favorite=is_favorite,
            is_important=is_important,
            is_archived=is_archived
        )
    
    def _parse_classification_result(self, log_path: str, log_data: Dict[str, Any]) -> ClassificationTrainingResult:
        """解析分类训练结果"""
        epochs = log_data.get("epochs", [])
        
        # 提取各个指标序列
        train_loss_values = []
        train_acc_values = []
        val_loss_values = []
        val_acc_values = []
        learning_rate_values = []
        
        for epoch_data in epochs:
            train_loss_values.append(epoch_data.get("train_loss", 0))
            train_acc_values.append(epoch_data.get("train_accuracy", 0))
            val_loss_values.append(epoch_data.get("val_loss", 0))
            val_acc_values.append(epoch_data.get("val_accuracy", 0))
            learning_rate_values.append(epoch_data.get("learning_rate", 0))
        
        # 找到最佳验证准确率
        best_epoch = 0
        best_val_acc = 0.0
        best_val_loss = float('inf')
        
        if val_acc_values:
            best_val_acc = max(val_acc_values)
            best_epoch = val_acc_values.index(best_val_acc) + 1
        
        if val_loss_values:
            best_val_loss = min(val_loss_values)
        
        # 最终指标
        final_train_acc = train_acc_values[-1] if train_acc_values else 0.0
        final_train_loss = train_loss_values[-1] if train_loss_values else 0.0
        final_val_acc = val_acc_values[-1] if val_acc_values else 0.0
        final_val_loss = val_loss_values[-1] if val_loss_values else 0.0
        
        # 构建通用结果
        generic_result = self._parse_generic_result(log_path, log_data, "classification")
        
        return ClassificationTrainingResult(
            trainer_id="classification",
            log_path=log_path,
            config=log_data.get("config", {}),
            start_time=log_data.get("start_time", ""),
            end_time=log_data.get("end_time", ""),
            epochs=epochs,
            metrics=generic_result.metrics,
            summary=generic_result.summary,
            capabilities=generic_result.capabilities,
            train_loss_values=train_loss_values,
            train_acc_values=train_acc_values,
            val_loss_values=val_loss_values,
            val_acc_values=val_acc_values,
            learning_rate_values=learning_rate_values,
            best_epoch=best_epoch,
            best_val_acc=best_val_acc,
            best_val_loss=best_val_loss,
            final_train_acc=final_train_acc,
            final_train_loss=final_train_loss,
            final_val_acc=final_val_acc,
            final_val_loss=final_val_loss
        )
    
    def _calculate_training_time(self, log_data: Dict[str, Any]) -> str:
        """计算训练时间"""
        start_time = log_data.get("start_time", "")
        end_time = log_data.get("end_time", "")
        
        if not start_time or not end_time:
            return "未知"
        
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration = end_dt - start_dt
            
            # 格式化为可读字符串
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if hours > 0:
                return f"{hours}小时{minutes}分{seconds}秒"
            elif minutes > 0:
                return f"{minutes}分{seconds}秒"
            else:
                return f"{seconds}秒"
                
        except Exception:
            return "未知"
    
    def get_result_summary_text(self, result: TrainingResult) -> str:
        """获取结果摘要文本"""
        if isinstance(result, ClassificationTrainingResult):
            return self._get_classification_summary_text(result)
        else:
            return self._get_generic_summary_text(result)
    
    def _get_generic_summary_text(self, result: TrainingResult) -> str:
        """获取通用训练结果摘要"""
        summary = []
        summary.append(f"训练器: {result.trainer_id}")
        summary.append(f"训练时间: {result.summary.get('training_time', '未知')}")
        summary.append(f"完成轮数: {result.summary.get('epochs_completed', 0)}")
        
        if result.metrics:
            if "final_train_accuracy" in result.metrics:
                summary.append(f"最终训练准确率: {result.metrics['final_train_accuracy']:.2f}%")
            if "final_val_accuracy" in result.metrics:
                summary.append(f"最终验证准确率: {result.metrics['final_val_accuracy']:.2f}%")
            if "final_train_loss" in result.metrics:
                summary.append(f"最终训练损失: {result.metrics['final_train_loss']:.4f}")
            if "final_val_loss" in result.metrics:
                summary.append(f"最终验证损失: {result.metrics['final_val_loss']:.4f}")
        
        if result.capabilities.get("pretrained_used"):
            summary.append("使用能力: 预训练权重")
        if result.capabilities.get("augmentation_used"):
            summary.append("使用能力: 数据增强")
        if result.capabilities.get("scheduler_used") != "none":
            summary.append(f"使用能力: 学习率调度器 ({result.capabilities['scheduler_used']})")
        
        return "\n".join(summary)
    
    def _get_classification_summary_text(self, result: ClassificationTrainingResult) -> str:
        """获取分类训练结果摘要"""
        summary = []
        summary.append("=== 分类训练结果 ===")
        summary.append(f"模型: {result.config.get('model_name', '未知')}")
        summary.append(f"类别数: {result.config.get('num_classes', '未知')}")
        summary.append(f"训练轮数: {len(result.epochs)}/{result.config.get('epochs', '未知')}")
        summary.append(f"训练时间: {result.summary.get('training_time', '未知')}")
        summary.append("")
        summary.append("--- 最佳表现 ---")
        summary.append(f"最佳验证准确率: {result.best_val_acc:.2f}% (第 {result.best_epoch} 轮)")
        summary.append(f"最佳验证损失: {result.best_val_loss:.4f}")
        summary.append("")
        summary.append("--- 最终表现 ---")
        summary.append(f"最终训练准确率: {result.final_train_acc:.2f}%")
        summary.append(f"最终训练损失: {result.final_train_loss:.4f}")
        if result.final_val_acc > 0:
            summary.append(f"最终验证准确率: {result.final_val_acc:.2f}%")
            summary.append(f"最终验证损失: {result.final_val_loss:.4f}")
        summary.append("")
        summary.append("--- 使用能力 ---")
        if result.capabilities.get("pretrained_used"):
            summary.append("✓ 预训练权重: 启用")
        else:
            summary.append("✗ 预训练权重: 禁用")
        
        if result.capabilities.get("augmentation_used"):
            summary.append("✓ 数据增强: 启用")
            # 显示具体增强配置
            config = result.config
            if config.get("augmentation_random_horizontal_flip"):
                summary.append("  - 随机水平翻转: 启用")
            if config.get("augmentation_random_rotation", 0) > 0:
                summary.append(f"  - 随机旋转: ±{config['augmentation_random_rotation']}度")
        else:
            summary.append("✗ 数据增强: 禁用")
        
        scheduler_type = result.capabilities.get("scheduler_used", "none")
        if scheduler_type != "none":
            summary.append(f"✓ 学习率调度器: {scheduler_type}")
            if scheduler_type == "step":
                summary.append(f"  - 步长: {result.config.get('scheduler_step_size', 30)}")
                summary.append(f"  - 衰减率: {result.config.get('scheduler_gamma', 0.1)}")
            elif scheduler_type == "cosine":
                summary.append(f"  - 周期: {result.config.get('scheduler_t_max', 10)}")
        else:
            summary.append("✗ 学习率调度器: 无")
        
        summary.append("")
        summary.append(f"结果文件: {result.log_path}")
        if result.summary.get("model_saved"):
            summary.append(f"模型文件: {result.summary['model_saved']}")
        
        return "\n".join(summary)
    
    def save_notes(self, log_path: str, notes: Dict[str, str]) -> bool:
        """
        保存批注到训练日志文件
        
        Args:
            log_path: 训练日志文件路径
            notes: 批注字典
            
        Returns:
            成功返回True，失败返回False
        """
        if not os.path.exists(log_path):
            print(f"错误: 文件不存在 {log_path}")
            return False
        
        try:
            # 读取训练日志
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # 更新批注
            if 'notes' not in log_data:
                log_data['notes'] = {}
            
            # 只更新提供的字段，保留其他字段
            for key, value in notes.items():
                if value is not None:  # 只更新非空值
                    log_data['notes'][key] = value
            
            # 写回文件
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            print(f"批注已保存到: {log_path}")
            return True
            
        except Exception as e:
            print(f"保存批注失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_tags_favorite_important(self, log_path: str, tags: List[str] = None, 
                                   is_favorite: bool = None, is_important: bool = None) -> bool:
        """
        保存标签/收藏/重要标记到训练日志文件
        
        Args:
            log_path: 训练日志文件路径
            tags: 标签列表（可选）
            is_favorite: 是否收藏（可选）
            is_important: 是否重要（可选）
            
        Returns:
            成功返回True，失败返回False
        """
        if not os.path.exists(log_path):
            print(f"错误: 文件不存在 {log_path}")
            return False
        
        try:
            # 读取训练日志
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # 更新标签
            if tags is not None:
                log_data['tags'] = tags
            
            # 更新收藏状态
            if is_favorite is not None:
                log_data['is_favorite'] = is_favorite
            
            # 更新重要标记
            if is_important is not None:
                log_data['is_important'] = is_important
            
            # 写回文件
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            print(f"标签/收藏/重要标记已保存到: {log_path}")
            return True
            
        except Exception as e:
            print(f"保存标签/收藏/重要标记失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def batch_add_tags(self, log_paths: List[str], tags_to_add: List[str]) -> Tuple[int, int]:
        """
        批量添加标签到多个训练结果
        
        Args:
            log_paths: 训练日志文件路径列表
            tags_to_add: 要添加的标签列表
            
        Returns:
            (成功数, 失败数)
        """
        success_count = 0
        failure_count = 0
        
        for log_path in log_paths:
            try:
                # 读取当前标签
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                current_tags = log_data.get('tags', [])
                
                # 添加新标签（去重）
                for tag in tags_to_add:
                    if tag not in current_tags:
                        current_tags.append(tag)
                
                # 保存更新
                log_data['tags'] = current_tags
                
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=2, ensure_ascii=False)
                
                success_count += 1
                print(f"成功添加标签到: {log_path}")
                
            except Exception as e:
                print(f"添加标签失败 {log_path}: {e}")
                failure_count += 1
        
        return success_count, failure_count
    
    def batch_set_favorite(self, log_paths: List[str], is_favorite: bool) -> Tuple[int, int]:
        """
        批量设置收藏状态
        
        Args:
            log_paths: 训练日志文件路径列表
            is_favorite: 收藏状态
            
        Returns:
            (成功数, 失败数)
        """
        success_count = 0
        failure_count = 0
        
        for log_path in log_paths:
            try:
                # 读取当前数据
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                # 设置收藏状态
                log_data['is_favorite'] = is_favorite
                
                # 保存更新
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=2, ensure_ascii=False)
                
                success_count += 1
                print(f"成功设置收藏状态到: {log_path}")
                
            except Exception as e:
                print(f"设置收藏状态失败 {log_path}: {e}")
                failure_count += 1
        
        return success_count, failure_count
    
    def batch_set_important(self, log_paths: List[str], is_important: bool) -> Tuple[int, int]:
        """
        批量设置重要标记
        
        Args:
            log_paths: 训练日志文件路径列表
            is_important: 重要标记状态
            
        Returns:
            (成功数, 失败数)
        """
        success_count = 0
        failure_count = 0
        
        for log_path in log_paths:
            try:
                # 读取当前数据
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                # 设置重要标记
                log_data['is_important'] = is_important
                
                # 保存更新
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=2, ensure_ascii=False)
                
                success_count += 1
                print(f"成功设置重要标记到: {log_path}")
                
            except Exception as e:
                print(f"设置重要标记失败 {log_path}: {e}")
                failure_count += 1
        
        return success_count, failure_count
    
    def batch_set_archived(self, log_paths: List[str], is_archived: bool) -> Tuple[int, int]:
        """
        批量设置归档状态（安全清理方案）
        
        Args:
            log_paths: 训练日志文件路径列表
            is_archived: 归档状态（True=归档，False=未归档）
            
        Returns:
            (成功数, 失败数)
        """
        success_count = 0
        failure_count = 0
        
        for log_path in log_paths:
            try:
                # 读取当前数据
                with open(log_path, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                # 设置归档状态
                log_data['is_archived'] = is_archived
                
                # 保存更新
                with open(log_path, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=2, ensure_ascii=False)
                
                success_count += 1
                print(f"成功设置归档状态到: {log_path}")
                
            except Exception as e:
                print(f"设置归档状态失败 {log_path}: {e}")
                failure_count += 1
        
        return success_count, failure_count
    
    def export_results_summary(self, log_paths: List[str], output_path: str, format: str = "txt") -> bool:
        """
        批量导出实验摘要
        
        Args:
            log_paths: 训练日志文件路径列表
            output_path: 输出文件路径
            format: 导出格式（txt, json, csv）
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            # 加载所有结果
            results = []
            for log_path in log_paths:
                result = self.load_result(log_path)
                if result:
                    results.append(result)
            
            if not results:
                print("没有可导出的结果")
                return False
            
            if format == "txt":
                return self._export_to_txt(results, output_path)
            elif format == "json":
                return self._export_to_json(results, output_path)
            elif format == "csv":
                return self._export_to_csv(results, output_path)
            else:
                print(f"不支持的导出格式: {format}")
                return False
                
        except Exception as e:
            print(f"导出失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _export_to_txt(self, results: List[TrainingResult], output_path: str) -> bool:
        """导出为文本文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=== 训练实验结果批量导出 ===\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"导出数量: {len(results)} 个实验\n")
                f.write("=" * 50 + "\n\n")
                
                for i, result in enumerate(results, 1):
                    f.write(f"实验 {i}: {result.config.get('name', '未知')}\n")
                    f.write(f"文件路径: {result.log_path}\n")
                    f.write(f"训练时间: {result.start_time} 到 {result.end_time}\n")
                    f.write(f"训练器: {result.trainer_id}\n")
                    
                    # 标签信息
                    tags = getattr(result, 'tags', [])
                    if tags:
                        f.write(f"标签: {', '.join(tags)}\n")
                    
                    # 收藏/重要状态
                    if getattr(result, 'is_favorite', False):
                        f.write("状态: ★ 收藏\n")
                    if getattr(result, 'is_important', False):
                        f.write("状态: ❗ 重要\n")
                    
                    # 关键指标
                    if isinstance(result, ClassificationTrainingResult):
                        f.write(f"最佳验证准确率: {result.best_val_acc:.2f}%\n")
                        f.write(f"最终验证准确率: {result.final_val_acc:.2f}%\n")
                        f.write(f"最佳轮数: {result.best_epoch}\n")
                    else:
                        # 通用指标
                        if "final_val_accuracy" in result.metrics:
                            f.write(f"最终验证准确率: {result.metrics['final_val_accuracy']:.2f}%\n")
                        if "max_val_accuracy" in result.metrics:
                            f.write(f"最高验证准确率: {result.metrics['max_val_accuracy']:.2f}%\n")
                    
                    f.write("-" * 40 + "\n\n")
            
            print(f"文本导出成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"文本导出失败: {e}")
            return False
    
    def _export_to_json(self, results: List[TrainingResult], output_path: str) -> bool:
        """导出为JSON文件"""
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "count": len(results),
                "results": []
            }
            
            for result in results:
                result_data = {
                    "name": result.config.get("name", ""),
                    "log_path": result.log_path,
                    "trainer_id": result.trainer_id,
                    "start_time": result.start_time,
                    "end_time": result.end_time,
                    "tags": getattr(result, 'tags', []),
                    "is_favorite": getattr(result, 'is_favorite', False),
                    "is_important": getattr(result, 'is_important', False),
                    "config_summary": {
                        "model_name": result.config.get("model_name", ""),
                        "num_classes": result.config.get("num_classes", 0),
                        "epochs": result.config.get("epochs", 0),
                        "batch_size": result.config.get("batch_size", 0),
                        "learning_rate": result.config.get("learning_rate", 0.0),
                    },
                    "metrics": {}
                }
                
                # 添加指标
                if isinstance(result, ClassificationTrainingResult):
                    result_data["metrics"]["best_val_acc"] = result.best_val_acc
                    result_data["metrics"]["final_val_acc"] = result.final_val_acc
                    result_data["metrics"]["best_epoch"] = result.best_epoch
                    result_data["metrics"]["final_train_acc"] = result.final_train_acc
                else:
                    result_data["metrics"] = result.metrics
                
                export_data["results"].append(result_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"JSON导出成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"JSON导出失败: {e}")
            return False
    
    def _export_to_csv(self, results: List[TrainingResult], output_path: str) -> bool:
        """导出为CSV文件"""
        try:
            import csv
            
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # 表头
                headers = [
                    "实验名称", "训练器", "训练开始时间", "训练结束时间",
                    "标签", "是否收藏", "是否重要",
                    "模型名称", "类别数", "训练轮数", "批次大小", "学习率",
                    "最佳验证准确率", "最终验证准确率", "最佳轮数", "文件路径"
                ]
                writer.writerow(headers)
                
                # 数据行
                for result in results:
                    # 基础信息
                    row = [
                        result.config.get("name", ""),
                        result.trainer_id,
                        result.start_time,
                        result.end_time,
                        ",".join(getattr(result, 'tags', [])),
                        "是" if getattr(result, 'is_favorite', False) else "否",
                        "是" if getattr(result, 'is_important', False) else "否",
                        result.config.get("model_name", ""),
                        result.config.get("num_classes", ""),
                        result.config.get("epochs", ""),
                        result.config.get("batch_size", ""),
                        result.config.get("learning_rate", ""),
                    ]
                    
                    # 指标
                    if isinstance(result, ClassificationTrainingResult):
                        row.extend([
                            f"{result.best_val_acc:.2f}%",
                            f"{result.final_val_acc:.2f}%",
                            result.best_epoch,
                            result.log_path
                        ])
                    else:
                        # 通用指标
                        best_val_acc = result.metrics.get("max_val_accuracy", 0)
                        final_val_acc = result.metrics.get("final_val_accuracy", 0)
                        row.extend([
                            f"{best_val_acc:.2f}%" if best_val_acc else "",
                            f"{final_val_acc:.2f}%" if final_val_acc else "",
                            "",
                            result.log_path
                        ])
                    
                    writer.writerow(row)
            
            print(f"CSV导出成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"CSV导出失败: {e}")
            return False


# 全局分析器实例
_analyzer = None

def get_result_analyzer() -> TrainingResultAnalyzer:
    """获取结果分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = TrainingResultAnalyzer()
    return _analyzer