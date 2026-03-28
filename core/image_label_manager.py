#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
image_label_manager.py - 图片与标签导航管理模块

职责：管理图片文件列表、当前图片索引、标签文件读写、自动保存等基础导航功能。
目标：减轻 MainWindow 负担，将"图片导航与标签存取"职责从主板层下放。

设计原则：
1. 专注于数据操作，不涉及 UI 绘制
2. 通过 WorkbenchContext 操作运行期状态
3. 提供清晰的接口供 MainWindow 调用
4. 为后续扩展预留空间
"""

import os
from typing import List, Optional, Tuple
from dataclasses import dataclass
import tkinter.messagebox as messagebox


@dataclass
class NavigationResult:
    """导航操作结果"""
    success: bool
    current_index: int
    current_image_name: str
    image_files_count: int
    message: str = ""


class ImageLabelManager:
    """图片与标签导航管理器"""
    
    def __init__(self, context):
        """
        初始化管理器
        
        Args:
            context: WorkbenchContext 实例
        """
        self.context = context
    
    # ==================== 图片文件管理 ====================
    
    def load_image_files(self) -> Tuple[List[str], str]:
        """
        加载图片目录中的所有图片文件
        
        Returns:
            Tuple[图片文件列表, 状态消息]
        """
        self.context.image_files = []
        
        if not self.context.image_dir or not os.path.isdir(self.context.image_dir):
            return [], "图片目录不存在或未设置"
        
        # 筛选图片文件
        image_files = []
        for f in os.listdir(self.context.image_dir):
            if f.lower().endswith(self.context.valid_ext):
                image_files.append(f)
        
        # 排序并保存
        self.context.image_files = sorted(image_files)
        
        msg = f"找到 {len(self.context.image_files)} 张图片"
        return self.context.image_files, msg
    
    def get_current_image_path(self) -> str:
        """获取当前图片的完整路径"""
        if not self.context.current_image_name:
            return ""
        return os.path.join(self.context.image_dir, self.context.current_image_name)
    
    def get_current_label_path(self) -> str:
        """获取当前标签文件的完整路径"""
        if not self.context.current_image_name or not self.context.label_dir:
            return ""
        
        base_name = os.path.splitext(self.context.current_image_name)[0]
        return os.path.join(self.context.label_dir, f"{base_name}.txt")
    
    def get_label_path(self, image_name: str) -> str:
        """根据图片名称获取标签文件路径"""
        if not image_name or not self.context.label_dir:
            return ""
        
        base_name = os.path.splitext(image_name)[0]
        return os.path.join(self.context.label_dir, f"{base_name}.txt")
    
    # ==================== 标签文件读写 ====================
    
    def load_current_labels(self) -> Tuple[List[List[float]], str]:
        """
        加载当前图片的标签
        
        Returns:
            Tuple[标注框列表, 状态消息]
        """
        self.context.boxes = []
        self.context.selected_idx = None
        
        if not self.context.current_image_name:
            return [], "当前没有选中图片"
        
        label_path = self.get_current_label_path()
        if not label_path or not os.path.exists(label_path):
            return [], f"标签文件不存在: {os.path.basename(label_path) if label_path else '路径为空'}"
        
        boxes = []
        try:
            with open(label_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    
                    try:
                        cls_id = int(float(parts[0]))
                        cx = float(parts[1])
                        cy = float(parts[2])
                        bw = float(parts[3])
                        bh = float(parts[4])
                        boxes.append([cls_id, cx, cy, bw, bh])
                    except ValueError as e:
                        # 跳过格式错误的行
                        continue
                        
            self.context.boxes = boxes
            msg = f"加载了 {len(boxes)} 个标注框"
            return boxes, msg
            
        except Exception as e:
            error_msg = f"标签读取失败: {str(e)}"
            return [], error_msg
    
    def save_current_labels(self, boxes: Optional[List[List[float]]] = None) -> Tuple[bool, str]:
        """
        保存当前图片的标签
        
        Args:
            boxes: 要保存的标注框列表，如果为None则使用context中的boxes
            
        Returns:
            Tuple[是否成功, 状态消息]
        """
        if not self.context.current_image_name:
            return False, "当前没有选中图片"
        
        if not self.context.label_dir:
            return False, "标签目录未设置"
        
        # 使用传入的boxes或context中的boxes
        boxes_to_save = boxes if boxes is not None else self.context.boxes
        
        # 确保标签目录存在
        os.makedirs(self.context.label_dir, exist_ok=True)
        
        label_path = self.get_current_label_path()
        
        try:
            with open(label_path, "w", encoding="utf-8") as f:
                for box in boxes_to_save:
                    if len(box) >= 5:
                        cls_id, cx, cy, bw, bh = box[:5]
                        f.write(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
            
            success_msg = f"已保存 {os.path.basename(label_path)}"
            return True, success_msg
            
        except Exception as e:
            error_msg = f"保存失败: {str(e)}"
            return False, error_msg
    
    def maybe_autosave(self) -> Tuple[bool, str]:
        """如果需要自动保存，则保存当前标签"""
        if self.context.auto_save:
            return self.save_current_labels()
        return False, "自动保存未启用"
    
    # ==================== 图片导航 ====================
    
    def can_navigate_prev(self) -> bool:
        """是否可以导航到上一张图片"""
        return bool(self.context.image_files and self.context.current_index > 0)
    
    def can_navigate_next(self) -> bool:
        """是否可以导航到下一张图片"""
        return bool(self.context.image_files and 
                   self.context.current_index < len(self.context.image_files) - 1)
    
    def navigate_prev(self) -> NavigationResult:
        """
        导航到上一张图片
        
        Returns:
            NavigationResult 包含导航结果
        """
        if not self.can_navigate_prev():
            return NavigationResult(
                success=False,
                current_index=self.context.current_index,
                current_image_name=self.context.current_image_name,
                image_files_count=len(self.context.image_files),
                message="无法导航到上一张图片"
            )
        
        # 先尝试自动保存
        autosave_success, autosave_msg = self.maybe_autosave()
        
        # 更新索引
        self.context.current_index -= 1
        self.context.current_image_name = self.context.image_files[self.context.current_index]
        
        # 重置选中状态
        self.context.selected_idx = None
        
        return NavigationResult(
            success=True,
            current_index=self.context.current_index,
            current_image_name=self.context.current_image_name,
            image_files_count=len(self.context.image_files),
            message=f"已切换到上一张图片{' (已自动保存)' if autosave_success else ''}"
        )
    
    def navigate_next(self) -> NavigationResult:
        """
        导航到下一张图片
        
        Returns:
            NavigationResult 包含导航结果
        """
        if not self.can_navigate_next():
            return NavigationResult(
                success=False,
                current_index=self.context.current_index,
                current_image_name=self.context.current_image_name,
                image_files_count=len(self.context.image_files),
                message="无法导航到下一张图片"
            )
        
        # 先尝试自动保存
        autosave_success, autosave_msg = self.maybe_autosave()
        
        # 更新索引
        self.context.current_index += 1
        self.context.current_image_name = self.context.image_files[self.context.current_index]
        
        # 重置选中状态
        self.context.selected_idx = None
        
        return NavigationResult(
            success=True,
            current_index=self.context.current_index,
            current_image_name=self.context.current_image_name,
            image_files_count=len(self.context.image_files),
            message=f"已切换到下一张图片{' (已自动保存)' if autosave_success else ''}"
        )
    
    def navigate_to_index(self, index: int) -> NavigationResult:
        """
        导航到指定索引的图片
        
        Args:
            index: 目标索引
            
        Returns:
            NavigationResult 包含导航结果
        """
        if not self.context.image_files:
            return NavigationResult(
                success=False,
                current_index=self.context.current_index,
                current_image_name=self.context.current_image_name,
                image_files_count=0,
                message="没有可用的图片文件"
            )
        
        if index < 0 or index >= len(self.context.image_files):
            return NavigationResult(
                success=False,
                current_index=self.context.current_index,
                current_image_name=self.context.current_image_name,
                image_files_count=len(self.context.image_files),
                message=f"索引 {index} 超出范围 (0-{len(self.context.image_files)-1})"
            )
        
        # 如果当前有图片且启用了自动保存，先保存
        if self.context.current_image_name and self.context.auto_save:
            self.save_current_labels()
        
        # 更新索引
        self.context.current_index = index
        self.context.current_image_name = self.context.image_files[index]
        
        # 重置选中状态
        self.context.selected_idx = None
        
        return NavigationResult(
            success=True,
            current_index=self.context.current_index,
            current_image_name=self.context.current_image_name,
            image_files_count=len(self.context.image_files),
            message=f"已切换到图片 {index+1}/{len(self.context.image_files)}"
        )
    
    def get_image_display_info(self) -> Tuple[Optional[str], str, str]:
        """
        获取图片显示相关信息（不包含UI绘制）
        
        Returns:
            Tuple[图片路径, 图片名称, 状态消息]
        """
        if not self.context.image_files:
            return None, "", "没有可用的图片文件"
        
        if not 0 <= self.context.current_index < len(self.context.image_files):
            return None, "", "当前索引无效"
        
        image_name = self.context.image_files[self.context.current_index]
        image_path = os.path.join(self.context.image_dir, image_name)
        
        if not os.path.exists(image_path):
            return None, image_name, f"图片文件不存在: {image_path}"
        
        return image_path, image_name, "图片加载就绪"
    
    def prepare_image_for_display(self, image_path: str, canvas_area_width: int, canvas_area_height: int) -> Tuple[Optional['Image.Image'], int, int, int, int, str]:
        """
        准备图片显示（加载图片、计算尺寸）
        
        Args:
            image_path: 图片路径
            canvas_area_width: 画布区域宽度
            canvas_area_height: 画布区域高度
            
        Returns:
            Tuple[PIL图片对象, 原始宽度, 原始高度, 显示宽度, 显示高度, 错误消息]
        """
        try:
            from PIL import Image
        except ImportError:
            return None, 0, 0, 0, 0, "PIL库未安装"
        
        try:
            # 加载图片
            img = Image.open(image_path).convert("RGB")
            orig_w, orig_h = img.size
            
            # 计算显示尺寸
            area_w = max(canvas_area_width - 20, 300)
            area_h = max(canvas_area_height - 20, 300)
            
            scale = min(area_w / orig_w, area_h / orig_h)
            if scale <= 0:
                scale = 1.0
            
            display_w = max(1, int(orig_w * scale))
            display_h = max(1, int(orig_h * scale))
            
            # 调整图片尺寸
            display_img = img.resize((display_w, display_h), Image.LANCZOS)
            
            return display_img, orig_w, orig_h, display_w, display_h, ""
            
        except Exception as e:
            return None, 0, 0, 0, 0, f"图片加载失败: {str(e)}"
    
    # ==================== 状态查询 ====================
    
    def get_status_summary(self) -> dict:
        """获取管理器状态摘要"""
        return {
            "has_image_dir": bool(self.context.image_dir and os.path.isdir(self.context.image_dir)),
            "has_label_dir": bool(self.context.label_dir),
            "image_files_count": len(self.context.image_files),
            "current_index": self.context.current_index,
            "current_image_name": self.context.current_image_name,
            "boxes_count": len(self.context.boxes),
            "auto_save_enabled": self.context.auto_save,
            "can_navigate_prev": self.can_navigate_prev(),
            "can_navigate_next": self.can_navigate_next(),
        }