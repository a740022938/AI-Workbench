"""
配置对比器 - 对比两个训练配置的差异
"""

import json
import os
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime


class ConfigComparator:
    """配置对比器"""
    
    def __init__(self):
        pass
    
    def compare_configs(self, config_a: Dict[str, Any], config_b: Dict[str, Any], 
                       exclude_fields: List[str] = None) -> List[Dict[str, Any]]:
        """
        对比两个配置，返回差异列表
        
        Args:
            config_a: 配置A
            config_b: 配置B  
            exclude_fields: 要排除的字段列表（如name, project等）
            
        Returns:
            差异列表，每个元素包含字段名、值A、值B、是否不同
        """
        if exclude_fields is None:
            exclude_fields = []
        
        # 获取所有字段
        all_keys = set(config_a.keys()) | set(config_b.keys())
        
        # 排除不需要对比的字段
        keys_to_compare = [k for k in all_keys if k not in exclude_fields]
        
        differences = []
        
        for key in sorted(keys_to_compare):
            value_a = config_a.get(key)
            value_b = config_b.get(key)
            
            # 判断是否相同
            is_different = self._are_values_different(value_a, value_b)
            
            # 格式化显示值
            display_a = self._format_value(value_a)
            display_b = self._format_value(value_b)
            
            differences.append({
                "field": key,
                "value_a": display_a,
                "value_b": display_b,
                "is_different": is_different,
                "raw_value_a": value_a,
                "raw_value_b": value_b
            })
        
        return differences
    
    def _are_values_different(self, value_a, value_b) -> bool:
        """判断两个值是否不同"""
        # 处理None值
        if value_a is None and value_b is None:
            return False
        if value_a is None or value_b is None:
            return True
        
        # 处理数值类型（整数和浮点数）
        if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
            # 浮点数比较考虑精度
            if isinstance(value_a, float) or isinstance(value_b, float):
                return abs(float(value_a) - float(value_b)) > 1e-10
            else:
                return value_a != value_b
        
        # 处理字符串
        if isinstance(value_a, str) and isinstance(value_b, str):
            return value_a.strip() != value_b.strip()
        
        # 处理列表/元组
        if isinstance(value_a, (list, tuple)) and isinstance(value_b, (list, tuple)):
            if len(value_a) != len(value_b):
                return True
            for item_a, item_b in zip(value_a, value_b):
                if self._are_values_different(item_a, item_b):
                    return True
            return False
        
        # 处理字典
        if isinstance(value_a, dict) and isinstance(value_b, dict):
            all_keys = set(value_a.keys()) | set(value_b.keys())
            for key in all_keys:
                if self._are_values_different(value_a.get(key), value_b.get(key)):
                    return True
            return False
        
        # 其他类型
        try:
            return value_a != value_b
        except:
            # 如果无法比较，假设不同
            return True
    
    def _format_value(self, value) -> str:
        """格式化值用于显示"""
        if value is None:
            return "null"
        
        if isinstance(value, (int, float)):
            # 浮点数格式化
            if isinstance(value, float):
                return f"{value:.6f}".rstrip('0').rstrip('.') if value != 0 else "0"
            else:
                return str(value)
        
        if isinstance(value, bool):
            return str(value)
        
        if isinstance(value, str):
            # 字符串截断，避免过长
            if len(value) > 50:
                return value[:47] + "..."
            return value
        
        if isinstance(value, (list, tuple)):
            if len(value) > 3:
                return f"[{len(value)}项]"
            return str(value)
        
        if isinstance(value, dict):
            return "{...}"
        
        return str(value)
    
    def get_summary(self, config_a: Dict[str, Any], config_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取配置对比摘要
        
        Args:
            config_a: 配置A
            config_b: 配置B
            
        Returns:
            对比摘要
        """
        differences = self.compare_configs(config_a, config_b)
        
        total_fields = len(differences)
        different_fields = sum(1 for d in differences if d["is_different"])
        
        # 找出关键字段的差异
        key_fields = ["model_name", "epochs", "batch_size", "learning_rate", 
                     "use_augmentation", "use_pretrained_weights", "scheduler_type"]
        
        key_differences = []
        for diff in differences:
            if diff["field"] in key_fields and diff["is_different"]:
                key_differences.append(diff["field"])
        
        return {
            "total_fields": total_fields,
            "different_fields": different_fields,
            "different_percentage": (different_fields / total_fields * 100) if total_fields > 0 else 0,
            "key_differences": key_differences,
            "all_differences": differences
        }
    
    def prepare_config_for_reuse(self, config: Dict[str, Any], 
                               original_name: str = None,
                               suffix: str = None) -> Dict[str, Any]:
        """
        准备配置用于复用（创建新实验）
        
        Args:
            config: 原始配置
            original_name: 原始实验名（可选）
            suffix: 后缀（可选，默认使用时间戳）
            
        Returns:
            修改后的配置（用于新实验）
        """
        # 深拷贝配置
        import copy
        new_config = copy.deepcopy(config)
        
        # 处理实验名
        if "name" in new_config:
            if suffix is None:
                suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            original_name = new_config.get("name", "experiment")
            # 移除可能已存在的后缀
            base_name = original_name
            for s in ["_复件", "_复用", "_copy"]:
                if base_name.endswith(s):
                    base_name = base_name[:-len(s)]
            
            new_name = f"{base_name}_复件_{suffix}"
            new_config["name"] = new_name
        
        # 处理项目路径（如果需要）
        if "project" in new_config:
            project = new_config["project"]
            # 确保不是具体的实验路径
            if "/" in project or "\\" in project:
                # 如果是完整路径，提取项目根目录
                parts = project.replace("\\", "/").split("/")
                if len(parts) > 1:
                    # 保留项目根目录，去掉实验名
                    new_config["project"] = "/".join(parts[:-1]) if len(parts) > 1 else parts[0]
        
        # 重置一些状态字段
        reset_fields = [
            "best_epoch", "best_val_acc", "best_val_loss",
            "final_val_acc", "final_val_loss", "start_time", "end_time"
        ]
        
        for field in reset_fields:
            if field in new_config:
                del new_config[field]
        
        return new_config
    
    def export_comparison_report(self, config_a: Dict[str, Any], config_b: Dict[str, Any],
                               exp_name_a: str = "实验A", exp_name_b: str = "实验B",
                               format: str = "text") -> str:
        """
        导出对比报告
        
        Args:
            config_a: 配置A
            config_b: 配置B
            exp_name_a: 实验A的名称
            exp_name_b: 实验B的名称
            format: 报告格式 (text, json, markdown)
            
        Returns:
            报告内容
        """
        differences = self.compare_configs(config_a, config_b)
        summary = self.get_summary(config_a, config_b)
        
        if format == "json":
            report = {
                "summary": {
                    "total_fields": summary["total_fields"],
                    "different_fields": summary["different_fields"],
                    "different_percentage": summary["different_percentage"],
                    "key_differences": summary["key_differences"]
                },
                "differences": differences,
                "config_a": config_a,
                "config_b": config_b
            }
            return json.dumps(report, indent=2, ensure_ascii=False)
        
        elif format == "markdown":
            lines = []
            lines.append(f"# 训练配置对比报告")
            lines.append(f"**对比时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"**实验A**: {exp_name_a}")
            lines.append(f"**实验B**: {exp_name_b}")
            lines.append("")
            
            lines.append(f"## 对比摘要")
            lines.append(f"- 总字段数: {summary['total_fields']}")
            lines.append(f"- 差异字段: {summary['different_fields']}")
            lines.append(f"- 差异比例: {summary['different_percentage']:.1f}%")
            
            if summary['key_differences']:
                lines.append(f"- 关键差异: {', '.join(summary['key_differences'])}")
            
            lines.append("")
            lines.append(f"## 详细差异")
            lines.append("")
            lines.append("| 字段名 | 实验A的值 | 实验B的值 | 是否不同 |")
            lines.append("|--------|-----------|-----------|----------|")
            
            for diff in differences:
                field = diff["field"]
                value_a = diff["value_a"].replace("|", "\\|")
                value_b = diff["value_b"].replace("|", "\\|")
                is_diff = "✅" if diff["is_different"] else " "
                
                lines.append(f"| {field} | {value_a} | {value_b} | {is_diff} |")
            
            return "\n".join(lines)
        
        else:  # text格式
            lines = []
            lines.append("=" * 80)
            lines.append(f"训练配置对比报告")
            lines.append(f"对比时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"实验A: {exp_name_a}")
            lines.append(f"实验B: {exp_name_b}")
            lines.append("=" * 80)
            lines.append("")
            
            lines.append(f"对比摘要:")
            lines.append(f"  总字段数: {summary['total_fields']}")
            lines.append(f"  差异字段: {summary['different_fields']}")
            lines.append(f"  差异比例: {summary['different_percentage']:.1f}%")
            
            if summary['key_differences']:
                lines.append(f"  关键差异: {', '.join(summary['key_differences'])}")
            
            lines.append("")
            lines.append("详细差异:")
            lines.append("-" * 100)
            lines.append(f"{'字段名':<20} {'实验A的值':<25} {'实验B的值':<25} {'是否不同':<10}")
            lines.append("-" * 100)
            
            for diff in differences:
                field = diff["field"]
                value_a = diff["value_a"]
                value_b = diff["value_b"]
                is_diff = "不同" if diff["is_different"] else "相同"
                
                # 截断过长的值
                if len(value_a) > 23:
                    value_a = value_a[:20] + "..."
                if len(value_b) > 23:
                    value_b = value_b[:20] + "..."
                
                lines.append(f"{field:<20} {value_a:<25} {value_b:<25} {is_diff:<10}")
            
            lines.append("-" * 100)
            
            return "\n".join(lines)


# 全局实例
_config_comparator = None


def get_config_comparator():
    """获取配置对比器实例（单例）"""
    global _config_comparator
    if _config_comparator is None:
        _config_comparator = ConfigComparator()
    return _config_comparator


if __name__ == "__main__":
    # 测试代码
    config1 = {
        "name": "experiment1",
        "model_name": "resnet18",
        "epochs": 50,
        "batch_size": 32,
        "learning_rate": 0.001,
        "use_augmentation": True,
        "use_pretrained_weights": False,
        "scheduler_type": "step"
    }
    
    config2 = {
        "name": "experiment2",
        "model_name": "resnet34",
        "epochs": 100,
        "batch_size": 64,
        "learning_rate": 0.0005,
        "use_augmentation": False,
        "use_pretrained_weights": True,
        "scheduler_type": "cosine"
    }
    
    comparator = ConfigComparator()
    
    # 测试对比
    differences = comparator.compare_configs(config1, config2, exclude_fields=["name"])
    print("配置差异:")
    for diff in differences:
        print(f"  {diff['field']}: {diff['value_a']} vs {diff['value_b']} ({'不同' if diff['is_different'] else '相同'})")
    
    # 测试摘要
    summary = comparator.get_summary(config1, config2)
    print(f"\n对比摘要:")
    print(f"  总字段: {summary['total_fields']}")
    print(f"  差异字段: {summary['different_fields']}")
    print(f"  差异比例: {summary['different_percentage']:.1f}%")
    
    # 测试复用配置
    reused_config = comparator.prepare_config_for_reuse(config1, suffix="test")
    print(f"\n复用配置:")
    print(f"  原始name: {config1['name']}")
    print(f"  新name: {reused_config['name']}")
    
    # 测试报告
    report = comparator.export_comparison_report(config1, config2, "实验1", "实验2", "text")
    print(f"\n文本报告:")
    print(report[:500] + "..." if len(report) > 500 else report)