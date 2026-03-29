"""
训练中心运行器 - 通用训练执行器
基于训练中心管理器，支持多种训练后端
"""

from typing import Optional, Dict, Any
from core.training_center_manager import get_training_center


class TrainingCenterRunner:
    """通用训练运行器"""
    
    def __init__(self, trainer_id: str = "yolo_v8"):
        """
        初始化训练运行器
        
        Args:
            trainer_id: 训练器ID，默认为YOLOv8
        """
        self.trainer_id = trainer_id
        self.backend = None
        self.training_center = get_training_center()
        
        # 创建后端实例
        self._create_backend()
    
    def _create_backend(self):
        """创建训练后端实例"""
        try:
            self.backend = self.training_center.create_backend(self.trainer_id)
            self.is_backend_ready = True
        except Exception as e:
            self.is_backend_ready = False
            self.backend_error = str(e)
            print(f"[训练中心运行器] 创建后端失败: {e}")
    
    def set_trainer(self, trainer_id: str):
        """设置训练器"""
        if trainer_id != self.trainer_id:
            self.trainer_id = trainer_id
            self._create_backend()
    
    def start(self, training_config: Dict[str, Any], monitor_window=None) -> bool:
        """
        启动训练
        
        Args:
            training_config: 训练配置
            monitor_window: 监控窗口实例
            
        Returns:
            是否成功启动
        """
        if not self.is_backend_ready:
            if monitor_window:
                monitor_window.append_log(f"[训练中心] 后端未就绪: {getattr(self, 'backend_error', '未知错误')}")
            return False
        
        # 运行训练前体检
        if monitor_window:
            monitor_window.append_log(f"[训练中心] 正在检查训练环境...")
        
        report = self.training_center.run_health_check(self.trainer_id, training_config)
        
        if not report.can_start_training:
            if monitor_window:
                monitor_window.append_log(f"[训练中心] 训练前检查失败:")
                for error in report.environment_result.errors:
                    monitor_window.append_log(f"  ❌ {error['name']}: {error['message']}")
                monitor_window.append_log(f"[训练中心] 无法启动训练，请先解决问题")
            return False
        
        # 显示警告（如果有）
        if report.environment_result.warnings and monitor_window:
            monitor_window.append_log(f"[训练中心] 训练前检查警告:")
            for warning in report.environment_result.warnings:
                monitor_window.append_log(f"  ⚠️ {warning['name']}: {warning['message']}")
        
        if monitor_window:
            monitor_window.append_log(f"[训练中心] 训练前检查通过，正在启动训练...")
        
        # 启动训练
        return self.backend.start(training_config, monitor_window)
    
    def stop(self, monitor_window=None) -> bool:
        """停止训练"""
        if not self.is_backend_ready:
            return False
        return self.backend.stop(monitor_window)
    
    def resume(self, training_config: Dict[str, Any], monitor_window=None) -> bool:
        """继续训练"""
        if not self.is_backend_ready:
            return False
        return self.backend.resume(training_config, monitor_window)
    
    def get_status(self) -> Dict[str, Any]:
        """获取训练状态"""
        if not self.is_backend_ready:
            return {"is_running": False, "backend_ready": False}
        
        status = self.backend.get_status()
        status.update({
            "backend_ready": True,
            "trainer_id": self.trainer_id,
        })
        return status
    
    def get_health_report(self, training_config: Dict[str, Any]) -> Dict[str, Any]:
        """获取训练前体检报告"""
        report = self.training_center.run_health_check(self.trainer_id, training_config)
        return report.to_dict()


# 向后兼容的包装器（保持原有接口）
class CompatibleTrainingRunner:
    """
    兼容性训练运行器
    保持与原有TrainingRunner相同的接口，内部使用训练中心
    """
    
    def __init__(self):
        self.runner = TrainingCenterRunner("yolo_v8")  # 默认YOLO
    
    def start(self, training_config, monitor_window=None):
        return self.runner.start(training_config, monitor_window)
    
    def stop(self, monitor_window=None):
        return self.runner.stop(monitor_window)
    
    def resume(self, training_config, monitor_window=None):
        return self.runner.resume(training_config, monitor_window)
    
    def get_status(self):
        return self.runner.get_status()


if __name__ == "__main__":
    # 测试代码
    from core.trainer_registry import initialize_registry
    initialize_registry()
    
    print("=== 测试训练中心运行器 ===")
    
    runner = TrainingCenterRunner("yolo_v8")
    
    test_config = {
        "data": "data.yaml",
        "model": "yolov8n.pt",
        "epochs": 100,
    }
    
    status = runner.get_status()
    print(f"状态: {status}")
    
    report = runner.get_health_report(test_config)
    print(f"体检报告: {report['overall_status']}")
    print(f"可训练: {report['can_start_training']}")