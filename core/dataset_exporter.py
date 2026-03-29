import os
import shutil
import random
import json
from typing import List, Dict, Tuple, Optional
import datetime


# ====================== 基础函数 ======================

def get_paired_files(image_dir: str, label_dir: str) -> Tuple[List[str], List[str], List[str]]:
    """
    获取图片和标签配对的文件列表
    
    Returns:
        (image_files, label_files, missing_labels): 图片文件列表、标签文件列表、缺失标签的图片列表
    """
    if not os.path.isdir(image_dir) or not os.path.isdir(label_dir):
        return [], [], []
    
    valid_ext = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    image_files = []
    label_files = []
    missing_labels = []
    
    for file in os.listdir(image_dir):
        if not file.lower().endswith(valid_ext):
            continue
        
        img_path = os.path.join(image_dir, file)
        label_name = os.path.splitext(file)[0] + ".txt"
        label_path = os.path.join(label_dir, label_name)
        
        if os.path.exists(label_path):
            image_files.append(file)
            label_files.append(label_name)
        else:
            missing_labels.append(file)
    
    return image_files, label_files, missing_labels


def validate_split_ratios(train_ratio: float, val_ratio: float, test_ratio: float) -> Tuple[bool, str]:
    """验证划分比例是否合法"""
    if train_ratio < 0 or val_ratio < 0 or test_ratio < 0:
        return False, "比例不能为负数"
    
    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 0.001:  # 允许微小误差
        return False, f"比例总和应为1.0，当前为{total:.3f}"
    
    return True, "比例验证通过"


def split_dataset_files(image_files: List[str], label_files: List[str], 
                       train_ratio: float, val_ratio: float, test_ratio: float,
                       shuffle: bool = True, seed: int = 42) -> Dict[str, List[str]]:
    """
    划分数据集文件
    
    Returns:
        {
            'train': [image1, image2, ...],
            'val': [image3, image4, ...],
            'test': [image5, image6, ...]
        }
    """
    # 验证比例
    is_valid, msg = validate_split_ratios(train_ratio, val_ratio, test_ratio)
    if not is_valid:
        raise ValueError(msg)
    
    # 确保图片和标签文件一一对应
    if len(image_files) != len(label_files):
        raise ValueError(f"图片文件数({len(image_files)})和标签文件数({len(label_files)})不匹配")
    
    # 创建文件对列表
    pairs = list(zip(image_files, label_files))
    
    # 随机打乱
    if shuffle:
        random.seed(seed)
        random.shuffle(pairs)
    
    total = len(pairs)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    # 划分
    train_pairs = pairs[:train_end]
    val_pairs = pairs[train_end:val_end]
    test_pairs = pairs[val_end:]
    
    # 转换为字典格式
    result = {
        'train': [pair[0] for pair in train_pairs],  # 只返回图片文件名
        'val': [pair[0] for pair in val_pairs],
        'test': [pair[0] for pair in test_pairs],
        'train_labels': [pair[1] for pair in train_pairs],
        'val_labels': [pair[1] for pair in val_pairs],
        'test_labels': [pair[1] for pair in test_pairs]
    }
    
    return result


def calculate_class_distribution(label_dir: str, image_files: List[str]) -> Dict[str, Dict[str, int]]:
    """
    计算类别分布统计
    
    Returns:
        {
            'class_counts': {class_id: count},
            'image_counts': {class_id: image_count},
            'total_boxes': int,
            'total_images_with_labels': int
        }
    """
    class_counts = {}
    image_counts = {}
    total_boxes = 0
    total_images_with_labels = 0
    
    for image_file in image_files:
        label_name = os.path.splitext(image_file)[0] + ".txt"
        label_path = os.path.join(label_dir, label_name)
        
        if not os.path.exists(label_path):
            continue
        
        total_images_with_labels += 1
        
        try:
            with open(label_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            image_classes = set()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split()
                if len(parts) >= 1:
                    try:
                        class_id = int(parts[0])
                        # 统计框数量
                        if class_id not in class_counts:
                            class_counts[class_id] = 0
                        class_counts[class_id] += 1
                        total_boxes += 1
                        
                        # 统计图片数（每个类别在该图片中出现就算一次）
                        image_classes.add(class_id)
                    except ValueError:
                        continue
            
            # 更新图片计数
            for class_id in image_classes:
                if class_id not in image_counts:
                    image_counts[class_id] = 0
                image_counts[class_id] += 1
                
        except Exception:
            continue
    
    return {
        'class_counts': class_counts,
        'image_counts': image_counts,
        'total_boxes': total_boxes,
        'total_images_with_labels': total_images_with_labels
    }


def precheck_export(image_dir: str, label_dir: str, 
                   train_ratio: float, val_ratio: float, test_ratio: float) -> Dict[str, any]:
    """
    导出前预检查
    
    Returns:
        预检查结果字典
    """
    # 获取配对文件
    image_files, label_files, missing_labels = get_paired_files(image_dir, label_dir)
    total_images = len(image_files)
    
    # 验证比例
    is_valid, ratio_msg = validate_split_ratios(train_ratio, val_ratio, test_ratio)
    
    if not is_valid:
        return {
            'status': 'error',
            'message': ratio_msg,
            'total_images': total_images,
            'missing_labels': len(missing_labels)
        }
    
    # 计算划分数量
    train_count = int(total_images * train_ratio)
    val_count = int(total_images * val_ratio)
    test_count = total_images - train_count - val_count
    
    # 计算类别分布
    class_dist = calculate_class_distribution(label_dir, image_files)
    
    # 检查是否存在异常
    warnings = []
    if total_images == 0:
        warnings.append("没有找到可用的图片-标签对")
    if len(missing_labels) > 0:
        warnings.append(f"有{len(missing_labels)}张图片缺失标签文件")
    if class_dist['total_boxes'] == 0:
        warnings.append("所有标签文件都没有有效的标注框")
    
    # 检查类别ID连续性
    if class_dist['class_counts']:
        max_class_id = max(class_dist['class_counts'].keys())
        missing_classes = []
        for i in range(max_class_id + 1):
            if i not in class_dist['class_counts']:
                missing_classes.append(i)
        if missing_classes:
            warnings.append(f"类别ID不连续，缺失的ID: {missing_classes}")
    
    return {
        'status': 'success',
        'message': '预检查通过',
        'total_images': total_images,
        'train_count': train_count,
        'val_count': val_count,
        'test_count': test_count,
        'missing_labels': len(missing_labels),
        'class_distribution': class_dist,
        'warnings': warnings,
        'has_warnings': len(warnings) > 0
    }


def export_dataset_with_split(image_dir: str, label_dir: str, output_dir: str, 
                             class_names: List[str], 
                             train_ratio: float = 0.7, val_ratio: float = 0.2, test_ratio: float = 0.1,
                             shuffle: bool = True, seed: int = 42) -> Dict[str, any]:
    """
    导出数据集（支持train/val/test划分）
    
    Returns:
        导出结果字典
    """
    start_time = datetime.datetime.now()
    
    # 预检查
    precheck = precheck_export(image_dir, label_dir, train_ratio, val_ratio, test_ratio)
    if precheck['status'] == 'error':
        return {
            'status': 'error',
            'message': precheck['message'],
            'exported_count': 0
        }
    
    # 获取配对文件
    image_files, label_files, missing_labels = get_paired_files(image_dir, label_dir)
    
    # 划分数据集
    try:
        split_result = split_dataset_files(image_files, label_files, train_ratio, val_ratio, test_ratio, shuffle, seed)
    except Exception as e:
        return {
            'status': 'error',
            'message': f"数据集划分失败: {str(e)}",
            'exported_count': 0
        }
    
    # 创建输出目录结构
    dirs_to_create = [
        os.path.join(output_dir, "images", "train"),
        os.path.join(output_dir, "images", "val"),
        os.path.join(output_dir, "images", "test"),
        os.path.join(output_dir, "labels", "train"),
        os.path.join(output_dir, "labels", "val"),
        os.path.join(output_dir, "labels", "test")
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
    
    # 复制文件
    exported_count = 0
    skipped_files = []
    
    # 辅助函数：复制单个集合的文件
    def copy_split_files(split_name: str, image_list: List[str], label_list: List[str]):
        nonlocal exported_count
        for img_file, label_file in zip(image_list, label_list):
            src_img = os.path.join(image_dir, img_file)
            src_label = os.path.join(label_dir, label_file)
            
            dst_img = os.path.join(output_dir, "images", split_name, img_file)
            dst_label = os.path.join(output_dir, "labels", split_name, label_file)
            
            try:
                shutil.copy2(src_img, dst_img)
                shutil.copy2(src_label, dst_label)
                exported_count += 1
            except Exception as e:
                skipped_files.append({
                    'image': img_file,
                    'label': label_file,
                    'error': str(e)
                })
    
    # 复制各个划分集
    copy_split_files('train', split_result['train'], split_result['train_labels'])
    copy_split_files('val', split_result['val'], split_result['val_labels'])
    copy_split_files('test', split_result['test'], split_result['test_labels'])
    
    # 生成data.yaml
    yaml_path = os.path.join(output_dir, "data.yaml")
    try:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(f"path: {output_dir}\n")
            f.write("train: images/train\n")
            f.write("val: images/val\n")
            if test_ratio > 0:
                f.write("test: images/test\n")
            f.write("\n")
            f.write("names:\n")
            for i, name in enumerate(class_names):
                f.write(f"  {i}: {name}\n")
    except Exception as e:
        return {
            'status': 'error',
            'message': f"生成data.yaml失败: {str(e)}",
            'exported_count': exported_count
        }
    
    # 生成导出报告
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    report = {
        'status': 'success',
        'message': f"数据集导出成功，共导出{exported_count}个图片-标签对",
        'exported_count': exported_count,
        'output_dir': output_dir,
        'train_count': len(split_result['train']),
        'val_count': len(split_result['val']),
        'test_count': len(split_result['test']),
        'class_names': class_names,
        'class_count': len(class_names),
        'train_ratio': train_ratio,
        'val_ratio': val_ratio,
        'test_ratio': test_ratio,
        'skipped_files': skipped_files,
        'skipped_count': len(skipped_files),
        'missing_labels': len(missing_labels),
        'start_time': start_time.strftime("%Y-%m-%d %H:%M:%S"),
        'end_time': end_time.strftime("%Y-%m-%d %H:%M:%S"),
        'duration_seconds': duration,
        # 预留字段
        'dataset_version': '1.0',
        'export_format': 'yolo',
        'can_reimport': False  # 为闭环修正预留
    }
    
    # 保存报告文件
    report_path = os.path.join(output_dir, "export_report.json")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # 报告文件保存失败不影响导出
    
    return report


# ====================== 旧函数（保持兼容） ======================

def export_dataset(image_dir, label_dir, output_dir, class_names):
    """
    旧版导出函数（不支持划分，保持向后兼容）
    """
    if not image_dir or not os.path.isdir(image_dir):
        return False, f"image_dir not found: {image_dir}"

    if not label_dir or not os.path.isdir(label_dir):
        return False, f"label_dir not found: {label_dir}"

    if not output_dir:
        return False, "output_dir is empty"

    images_out = os.path.join(output_dir, "images")
    labels_out = os.path.join(output_dir, "labels")

    os.makedirs(images_out, exist_ok=True)
    os.makedirs(labels_out, exist_ok=True)

    count = 0
    valid_ext = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

    for file in os.listdir(image_dir):
        if not file.lower().endswith(valid_ext):
            continue

        img_path = os.path.join(image_dir, file)
        label_name = os.path.splitext(file)[0] + ".txt"
        label_path = os.path.join(label_dir, label_name)

        if os.path.exists(label_path):
            shutil.copy2(img_path, os.path.join(images_out, file))
            shutil.copy2(label_path, os.path.join(labels_out, label_name))
            count += 1

    yaml_path = os.path.join(output_dir, "data.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(f"path: {output_dir}\n")
        f.write("train: images\n")
        f.write("val: images\n\n")
        f.write("names:\n")
        for i, name in enumerate(class_names):
            f.write(f"  {i}: {name}\n")

    return True, f"export done, total {count}"