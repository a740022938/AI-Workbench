#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dataset_export_window.py - 数据集制作中心窗口

功能：
1. train/val/test 划分配置
2. 类别分布统计查看
3. 导出前预检查
4. 数据集导出
5. 导出结果报告
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from typing import Optional, Dict, Any

from core.dataset_exporter import (
    get_paired_files,
    validate_split_ratios,
    calculate_class_distribution,
    precheck_export,
    export_dataset_with_split
)
from core.data_health_manager import DataHealthManager, HealthCheckResult, IssueSeverity
from core.context.workbench_context import WorkbenchContext
from core.language_manager import t
from core.ui_style_manager import get_style_manager


class DatasetExportWindow:
    """数据集导出窗口"""
    
    def __init__(self, master, context: WorkbenchContext):
        """
        初始化数据集导出窗口
        
        Args:
            master: 父窗口
            context: WorkbenchContext 实例
        """
        self.master = master
        self.context = context
        
        # 窗口配置
        self.window = tk.Toplevel(master)
        self.window.title(t("TITLE_DATASET_EXPORT"))
        self.window.geometry("1000x800")
        self.window.transient(master)
        self.window.grab_set()
        
        # UI管理器
        self.style_manager = get_style_manager()
        self.language_manager = t._manager  # 通过t函数获取管理器
        
        # 样式
        self._update_colors_from_style()
        
        # 当前预检查结果
        self.current_precheck_result = None
        
        # 构建UI
        self._build_ui()
        
        # 注册回调
        if hasattr(self.language_manager, 'register_callback'):
            self.language_manager.register_callback(self._refresh_ui_on_language_change)
        self.style_manager.register_callback(self._refresh_ui_on_style_change)
        
        # 初始加载
        self._refresh_file_stats()
        self._refresh_class_distribution()
    
    def _update_colors_from_style(self):
        """从风格管理器更新颜色值"""
        theme = self.style_manager.get_current_theme_definition()
        
        # 更新基础颜色
        self.bg_main = theme.colors.get("background", "#16181d")
        self.bg_card = theme.colors.get("surface", "#20242c")
        self.bg_card_2 = theme.colors.get("surface_variant", "#252a33")
        self.text_main = theme.colors.get("text_primary", "#f5f7fa")
        self.text_sub = theme.colors.get("text_secondary", "#aeb6c2")
        self.accent = theme.colors.get("primary", "#6ea8fe")
        self.border = theme.colors.get("border", "#2d3440")
        self.btn_bg = theme.colors.get("button_background", "#2a303a")
        self.btn_hover = theme.colors.get("button_hover", "#343b47")
        self.error_color = theme.colors.get("error", "#f87171")
        self.warning_color = theme.colors.get("warning", "#fbbf24")
        self.success_color = theme.colors.get("success", "#10b981")
        
        # 更新窗口背景
        self.window.config(bg=self.bg_main)
    
    def _refresh_ui_on_style_change(self):
        """风格切换时刷新UI样式"""
        # 更新颜色值
        self._update_colors_from_style()
        
        # 刷新窗口背景
        self.window.config(bg=self.bg_main)
        
        # 刷新主容器背景
        if hasattr(self, 'main_frame'):
            self.main_frame.config(bg=self.bg_main)
        
        # 刷新标题区背景
        if hasattr(self, 'title_frame'):
            self.title_frame.config(bg=self.bg_main)
        
        # 刷新卡片背景
        card_widgets = [
            'split_card', 'stats_card', 'class_dist_card',
            'precheck_card', 'export_card'
        ]
        
        for card_name in card_widgets:
            if hasattr(self, card_name):
                card = getattr(self, card_name)
                try:
                    card.config(bg=self.bg_card, highlightbackground=self.border)
                except:
                    pass
        
        # 刷新主要按钮颜色
        button_widgets = [
            'run_precheck_btn', 'export_btn', 'browse_export_dir_btn'
        ]
        
        for btn_name in button_widgets:
            if hasattr(self, btn_name):
                btn = getattr(self, btn_name)
                try:
                    btn.config(bg=self.accent, fg=self.text_main)
                except:
                    pass
        
        # 刷新标签颜色
        label_widgets = [
            'title_label', 'file_stats_label', 'class_dist_label',
            'precheck_label', 'export_label'
        ]
        
        for label_name in label_widgets:
            if hasattr(self, label_name):
                label = getattr(self, label_name)
                try:
                    label.config(bg=self.bg_main, fg=self.text_main)
                except:
                    pass
        
        # 刷新输入框和下拉框
        if hasattr(self, 'train_ratio_entry'):
            try:
                self.train_ratio_entry.config(bg=self.bg_card_2, fg=self.text_main)
            except:
                pass
        
        if hasattr(self, 'val_ratio_entry'):
            try:
                self.val_ratio_entry.config(bg=self.bg_card_2, fg=self.text_main)
            except:
                pass
        
        if hasattr(self, 'test_ratio_entry'):
            try:
                self.test_ratio_entry.config(bg=self.bg_card_2, fg=self.text_main)
            except:
                pass
        
        if hasattr(self, 'export_dir_entry'):
            try:
                self.export_dir_entry.config(bg=self.bg_card_2, fg=self.text_main)
            except:
                pass
        
        # 刷新表格颜色（如果存在）
        if hasattr(self, 'class_dist_tree'):
            try:
                style = ttk.Style()
                style.configure("Custom.Treeview", 
                              background=self.bg_card,
                              foreground=self.text_main,
                              fieldbackground=self.bg_card)
                self.class_dist_tree.config(style="Custom.Treeview")
            except:
                pass
        
        # 刷新所有文本区域
        text_widgets = [
            'file_stats_text', 'precheck_text', 'result_text'
        ]
        
        for text_name in text_widgets:
            if hasattr(self, text_name):
                try:
                    getattr(self, text_name).config(bg=self.bg_card_2, fg=self.text_main)
                except:
                    pass
        
        print(f"数据集制作中心风格已刷新，当前风格: {self.style_manager.current_style.value}")
    
    def _refresh_ui_on_language_change(self):
        """语言切换时刷新UI文案"""
        # 更新窗口标题
        self.window.title(t("TITLE_DATASET_EXPORT"))
        
        # 更新按钮文本
        if hasattr(self, 'run_precheck_btn'):
            self.run_precheck_btn.config(text="运行预检查")
        if hasattr(self, 'export_btn'):
            self.export_btn.config(text="导出数据集")
        if hasattr(self, 'browse_export_dir_btn'):
            self.browse_export_dir_btn.config(text="浏览")
        
        # 更新标签文本
        if hasattr(self, 'file_stats_label'):
            self.file_stats_label.config(text="📊 文件统计")
        if hasattr(self, 'class_dist_label'):
            self.class_dist_label.config(text="📈 类别分布")
        if hasattr(self, 'precheck_label'):
            self.precheck_label.config(text="🔍 预检查")
        if hasattr(self, 'export_label'):
            self.export_label.config(text="🚀 导出设置")
        
        # 更新其他文本控件
        if hasattr(self, 'train_ratio_label'):
            self.train_ratio_label.config(text="训练集比例")
        if hasattr(self, 'val_ratio_label'):
            self.val_ratio_label.config(text="验证集比例")
        if hasattr(self, 'test_ratio_label'):
            self.test_ratio_label.config(text="测试集比例")
        if hasattr(self, 'export_dir_label'):
            self.export_dir_label.config(text="导出目录")
    
    def _build_ui(self):
        """构建UI界面"""
        # 主容器
        main_frame = tk.Frame(self.window, bg=self.bg_main)
        main_frame.pack(fill="both", expand=True, padx=14, pady=14)
        
        # 标题
        title_frame = tk.Frame(main_frame, bg=self.bg_main)
        title_frame.pack(fill="x", pady=(0, 14))
        
        tk.Label(
            title_frame,
            text="📊 数据集制作中心",
            bg=self.bg_main,
            fg=self.text_main,
            font=("Microsoft YaHei", 18, "bold")
        ).pack(side="left")
        
        # 关闭按钮
        tk.Button(
            title_frame,
            text="关闭",
            command=self.window.destroy,
            bg=self.border,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat"
        ).pack(side="right")
        
        # 左右分栏容器
        content_frame = tk.Frame(main_frame, bg=self.bg_main)
        content_frame.pack(fill="both", expand=True)
        
        # 左栏：配置和统计
        left_frame = tk.Frame(content_frame, bg=self.bg_main)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        # 右栏：预检查和导出
        right_frame = tk.Frame(content_frame, bg=self.bg_main)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # ==================== 左栏内容 ====================
        
        # 1. 文件统计卡片
        file_stats_card = self._create_card(left_frame, "📁 文件统计")
        file_stats_card.pack(fill="x", pady=(0, 12))
        
        self.file_stats_text = tk.Text(
            file_stats_card,
            bg=self.bg_card_2,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            height=6,
            wrap="word",
            relief="flat",
            padx=12,
            pady=12
        )
        self.file_stats_text.pack(fill="x", padx=12, pady=(0, 12))
        self.file_stats_text.config(state="disabled")
        
        # 2. 类别分布卡片
        class_dist_card = self._create_card(left_frame, "📊 类别分布统计")
        class_dist_card.pack(fill="both", expand=True, pady=(0, 12))
        
        # 类别分布表格容器
        table_container = tk.Frame(class_dist_card, bg=self.bg_card)
        table_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # 创建Treeview
        columns = ("class_id", "class_name", "box_count", "image_count")
        self.class_tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            height=12
        )
        
        # 设置列标题
        self.class_tree.heading("class_id", text="类别ID", anchor="center")
        self.class_tree.heading("class_name", text="类别名称", anchor="w")
        self.class_tree.heading("box_count", text="框数量", anchor="center")
        self.class_tree.heading("image_count", text="图片数量", anchor="center")
        
        # 设置列宽度
        self.class_tree.column("class_id", width=80, stretch=False, anchor="center")
        self.class_tree.column("class_name", width=120, stretch=True, anchor="w")
        self.class_tree.column("box_count", width=80, stretch=False, anchor="center")
        self.class_tree.column("image_count", width=80, stretch=False, anchor="center")
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.class_tree.yview)
        self.class_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.class_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # 3. 划分配置卡片
        split_config_card = self._create_card(left_frame, "⚙️ 数据集划分配置")
        split_config_card.pack(fill="x", pady=(0, 12))
        
        # 配置表单
        config_frame = tk.Frame(split_config_card, bg=self.bg_card)
        config_frame.pack(fill="x", padx=12, pady=12)
        
        # 训练集比例
        tk.Label(
            config_frame,
            text="训练集比例 (train_ratio):",
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 9)
        ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=8)
        
        self.train_ratio_var = tk.DoubleVar(value=0.7)
        train_scale = tk.Scale(
            config_frame,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient="horizontal",
            variable=self.train_ratio_var,
            bg=self.bg_card,
            fg=self.text_main,
            highlightthickness=0,
            length=200,
            command=self._on_ratio_changed
        )
        train_scale.grid(row=0, column=1, sticky="w", pady=8)
        
        self.train_ratio_label = tk.Label(
            config_frame,
            text="0.70",
            bg=self.bg_card,
            fg=self.accent,
            font=("Microsoft YaHei", 9, "bold")
        )
        self.train_ratio_label.grid(row=0, column=2, padx=8, pady=8)
        
        # 验证集比例
        tk.Label(
            config_frame,
            text="验证集比例 (val_ratio):",
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 9)
        ).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=8)
        
        self.val_ratio_var = tk.DoubleVar(value=0.2)
        val_scale = tk.Scale(
            config_frame,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient="horizontal",
            variable=self.val_ratio_var,
            bg=self.bg_card,
            fg=self.text_main,
            highlightthickness=0,
            length=200,
            command=self._on_ratio_changed
        )
        val_scale.grid(row=1, column=1, sticky="w", pady=8)
        
        self.val_ratio_label = tk.Label(
            config_frame,
            text="0.20",
            bg=self.bg_card,
            fg=self.accent,
            font=("Microsoft YaHei", 9, "bold")
        )
        self.val_ratio_label.grid(row=1, column=2, padx=8, pady=8)
        
        # 测试集比例
        tk.Label(
            config_frame,
            text="测试集比例 (test_ratio):",
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 9)
        ).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=8)
        
        self.test_ratio_var = tk.DoubleVar(value=0.1)
        test_scale = tk.Scale(
            config_frame,
            from_=0.0,
            to=1.0,
            resolution=0.05,
            orient="horizontal",
            variable=self.test_ratio_var,
            bg=self.bg_card,
            fg=self.text_main,
            highlightthickness=0,
            length=200,
            command=self._on_ratio_changed
        )
        test_scale.grid(row=2, column=1, sticky="w", pady=8)
        
        self.test_ratio_label = tk.Label(
            config_frame,
            text="0.10",
            bg=self.bg_card,
            fg=self.accent,
            font=("Microsoft YaHei", 9, "bold")
        )
        self.test_ratio_label.grid(row=2, column=2, padx=8, pady=8)
        
        # 比例验证状态
        self.ratio_status_label = tk.Label(
            config_frame,
            text="✅ 比例总和: 1.00",
            bg=self.bg_card,
            fg=self.success_color,
            font=("Microsoft YaHei", 9)
        )
        self.ratio_status_label.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        
        # ==================== 右栏内容 ====================
        
        # 4. 预检查卡片
        precheck_card = self._create_card(right_frame, "🔍 导出前预检查")
        precheck_card.pack(fill="both", expand=True, pady=(0, 12))
        
        # 预检查按钮
        precheck_btn_frame = tk.Frame(precheck_card, bg=self.bg_card)
        precheck_btn_frame.pack(fill="x", padx=12, pady=12)
        
        tk.Button(
            precheck_btn_frame,
            text="运行预检查",
            command=self._run_precheck,
            bg="#3b82f6",
            fg="white",
            font=("Microsoft YaHei", 10),
            padx=16,
            pady=8,
            relief="flat",
            cursor="hand2"
        ).pack(side="left")
        
        # 预检查结果区域
        precheck_result_frame = tk.Frame(precheck_card, bg=self.bg_card)
        precheck_result_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        self.precheck_text = tk.Text(
            precheck_result_frame,
            bg=self.bg_card_2,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            wrap="word",
            relief="flat",
            padx=12,
            pady=12
        )
        self.precheck_text.pack(fill="both", expand=True)
        self.precheck_text.insert("1.0", "点击【运行预检查】按钮开始检查...")
        self.precheck_text.config(state="disabled")
        
        # 5. 导出配置卡片
        export_card = self._create_card(right_frame, "🚀 数据集导出")
        export_card.pack(fill="x", pady=(0, 12))
        
        # 导出配置
        export_config_frame = tk.Frame(export_card, bg=self.bg_card)
        export_config_frame.pack(fill="x", padx=12, pady=12)
        
        # 导出目录选择
        tk.Label(
            export_config_frame,
            text="导出目录:",
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 9)
        ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=8)
        
        self.export_dir_var = tk.StringVar(value=self.context.config_data.get("paths", {}).get("output_dataset_dir", ""))
        export_dir_entry = tk.Entry(
            export_config_frame,
            textvariable=self.export_dir_var,
            bg="#1e2229",
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            relief="flat",
            insertbackground=self.text_main,
            width=30
        )
        export_dir_entry.grid(row=0, column=1, sticky="w", pady=8)
        
        tk.Button(
            export_config_frame,
            text="浏览",
            command=self._browse_export_dir,
            bg=self.btn_bg,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            padx=8,
            pady=2,
            relief="flat"
        ).grid(row=0, column=2, padx=(8, 0), pady=8)
        
        # 导出按钮
        export_btn_frame = tk.Frame(export_card, bg=self.bg_card)
        export_btn_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        self.export_btn = tk.Button(
            export_btn_frame,
            text="导出数据集",
            command=self._export_dataset,
            bg="#10b981",
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            padx=20,
            pady=10,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.export_btn.pack(side="left")
        
        tk.Button(
            export_btn_frame,
            text="查看导出报告",
            command=self._view_export_report,
            bg="#8b5cf6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            state="disabled"
        ).pack(side="left", padx=(8, 0))
        
        # 6. 导出结果卡片
        result_card = self._create_card(right_frame, "📋 导出结果")
        result_card.pack(fill="both", expand=True)
        
        self.result_text = tk.Text(
            result_card,
            bg=self.bg_card_2,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            wrap="word",
            relief="flat",
            padx=12,
            pady=12
        )
        self.result_text.pack(fill="both", expand=True, padx=12, pady=12)
        self.result_text.insert("1.0", "导出结果将显示在这里...")
        self.result_text.config(state="disabled")
        
        # 初始更新比例标签
        self._update_ratio_labels()
    
    def _create_card(self, parent, title):
        """创建卡片容器"""
        card = tk.Frame(parent, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        
        # 标题
        title_frame = tk.Frame(card, bg=self.bg_card)
        title_frame.pack(fill="x", padx=12, pady=12)
        
        tk.Label(
            title_frame,
            text=title,
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 12, "bold")
        ).pack(side="left")
        
        return card
    
    def _refresh_file_stats(self):
        """刷新文件统计信息"""
        if not self.context.image_dir or not self.context.label_dir:
            return
        
        # 获取配对文件
        image_files, label_files, missing_labels = get_paired_files(
            self.context.image_dir, 
            self.context.label_dir
        )
        
        # 更新统计文本
        self.file_stats_text.config(state="normal")
        self.file_stats_text.delete("1.0", "end")
        
        lines = []
        lines.append("【目录信息】")
        lines.append(f"  图片目录: {os.path.basename(self.context.image_dir)}")
        lines.append(f"  标签目录: {os.path.basename(self.context.label_dir)}")
        lines.append("")
        
        lines.append("【文件统计】")
        lines.append(f"  图片总数: {len(image_files) + len(missing_labels)}")
        lines.append(f"  有标签图片: {len(image_files)}")
        lines.append(f"  缺失标签: {len(missing_labels)}")
        lines.append(f"  可参与划分: {len(image_files)}")
        lines.append("")
        
        if missing_labels:
            lines.append(f"【缺失标签的图片 ({len(missing_labels)}张)】")
            for i, img in enumerate(missing_labels[:5], 1):
                lines.append(f"  {i}. {img}")
            if len(missing_labels) > 5:
                lines.append(f"  还有{len(missing_labels) - 5}张未显示...")
        
        self.file_stats_text.insert("1.0", "\n".join(lines))
        self.file_stats_text.config(state="disabled")
    
    def _refresh_class_distribution(self):
        """刷新类别分布统计"""
        if not self.context.image_dir or not self.context.label_dir:
            return
        
        # 获取配对文件
        image_files, label_files, _ = get_paired_files(
            self.context.image_dir, 
            self.context.label_dir
        )
        
        # 计算类别分布
        dist = calculate_class_distribution(self.context.label_dir, image_files)
        
        # 清空现有项
        for item in self.class_tree.get_children():
            self.class_tree.delete(item)
        
        # 添加类别统计
        class_counts = dist.get('class_counts', {})
        image_counts = dist.get('image_counts', {})
        
        for class_id in sorted(class_counts.keys()):
            box_count = class_counts[class_id]
            img_count = image_counts.get(class_id, 0)
            
            # 获取类别名称
            class_name = ""
            if self.context.class_names and 0 <= class_id < len(self.context.class_names):
                class_name = self.context.class_names[class_id]
            else:
                class_name = f"未知类别_{class_id}"
            
            self.class_tree.insert(
                "", "end",
                values=(class_id, class_name, box_count, img_count)
            )
        
        # 添加总计行
        total_boxes = dist.get('total_boxes', 0)
        total_images = dist.get('total_images_with_labels', 0)
        
        if total_boxes > 0:
            self.class_tree.insert(
                "", "end",
                values=("总计", "-", total_boxes, total_images),
                tags=("total",)
            )
            self.class_tree.tag_configure("total", foreground=self.accent, font=("Microsoft YaHei", 9, "bold"))
    
    def _on_ratio_changed(self, *args):
        """比例滑块变化事件"""
        self._update_ratio_labels()
    
    def _update_ratio_labels(self):
        """更新比例标签和验证状态"""
        # 获取当前值
        train_val = round(self.train_ratio_var.get(), 2)
        val_val = round(self.val_ratio_var.get(), 2)
        test_val = round(self.test_ratio_var.get(), 2)
        
        # 更新标签
        self.train_ratio_label.config(text=f"{train_val:.2f}")
        self.val_ratio_label.config(text=f"{val_val:.2f}")
        self.test_ratio_label.config(text=f"{test_val:.2f}")
        
        # 验证比例
        total = train_val + val_val + test_val
        diff = abs(total - 1.0)
        
        if diff <= 0.001:
            self.ratio_status_label.config(
                text=f"✅ 比例总和: {total:.2f}",
                fg=self.success_color
            )
        else:
            self.ratio_status_label.config(
                text=f"⚠️ 比例总和: {total:.2f} (应为1.00)",
                fg=self.warning_color
            )
    
    def _run_precheck(self):
        """运行预检查"""
        if not self.context.image_dir or not self.context.label_dir:
            messagebox.showwarning("目录未设置", "请先设置图片目录和标签目录")
            return
        
        # 获取比例
        train_ratio = round(self.train_ratio_var.get(), 2)
        val_ratio = round(self.val_ratio_var.get(), 2)
        test_ratio = round(self.test_ratio_var.get(), 2)
        
        # 运行预检查
        try:
            self.current_precheck_result = precheck_export(
                self.context.image_dir,
                self.context.label_dir,
                train_ratio,
                val_ratio,
                test_ratio
            )
            
            # 显示结果
            self.precheck_text.config(state="normal")
            self.precheck_text.delete("1.0", "end")
            
            result = self.current_precheck_result
            lines = []
            
            if result['status'] == 'error':
                lines.append(f"❌ {result['message']}")
                lines.append("")
                lines.append("请调整配置后重试。")
            else:
                lines.append(f"✅ {result['message']}")
                lines.append("")
                lines.append("【划分统计】")
                lines.append(f"  总图片数: {result['total_images']}")
                lines.append(f"  Train集: {result['train_count']} ({result['train_count']/max(result['total_images'],1)*100:.1f}%)")
                lines.append(f"  Val集: {result['val_count']} ({result['val_count']/max(result['total_images'],1)*100:.1f}%)")
                lines.append(f"  Test集: {result['test_count']} ({result['test_count']/max(result['total_images'],1)*100:.1f}%)")
                lines.append("")
                
                lines.append("【类别统计】")
                dist = result['class_distribution']
                lines.append(f"  总标注框: {dist['total_boxes']}")
                lines.append(f"  有标签图片: {dist['total_images_with_labels']}")
                lines.append(f"  类别数: {len(dist['class_counts'])}")
                lines.append("")
                
                # 显示类别分布前5个
                if dist['class_counts']:
                    lines.append("【类别分布 (前5)】")
                    sorted_classes = sorted(dist['class_counts'].items(), key=lambda x: x[1], reverse=True)
                    for class_id, count in sorted_classes[:5]:
                        class_name = ""
                        if self.context.class_names and 0 <= class_id < len(self.context.class_names):
                            class_name = self.context.class_names[class_id]
                        lines.append(f"  {class_id}: {class_name} - {count}个框 ({dist['image_counts'].get(class_id, 0)}张图片)")
                    if len(sorted_classes) > 5:
                        lines.append(f"  还有{len(sorted_classes)-5}个类别未显示...")
                    lines.append("")
                
                # 显示警告
                if result['has_warnings']:
                    lines.append("【⚠️ 警告】")
                    for warning in result['warnings']:
                        lines.append(f"  • {warning}")
                    lines.append("")
                
                lines.append("【建议】")
                if result['total_images'] < 100:
                    lines.append("  • 数据量较少，建议增加标注数据")
                if result['missing_labels'] > 0:
                    lines.append(f"  • 有{result['missing_labels']}张图片缺失标签，建议补充")
                if len(dist['class_counts']) == 0:
                    lines.append("  • 没有有效的标注框，无法用于训练")
                
                # 启用导出按钮
                if result['total_images'] > 0 and len(dist['class_counts']) > 0:
                    self.export_btn.config(state="normal")
                else:
                    self.export_btn.config(state="disabled")
            
            self.precheck_text.insert("1.0", "\n".join(lines))
            self.precheck_text.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("预检查失败", f"预检查时发生错误:\n{str(e)}")
    
    def _browse_export_dir(self):
        """浏览导出目录"""
        dir_path = filedialog.askdirectory(
            title="选择数据集导出目录",
            initialdir=os.path.expanduser("~")
        )
        if dir_path:
            self.export_dir_var.set(dir_path)
    
    def _check_health_before_export(self):
        """导出前检查健康状态"""
        try:
            manager = DataHealthManager(self.context)
            result = manager.run_full_health_check()
            
            if result.issues_found == 0:
                return {
                    'has_issues': False,
                    'message': '✅ 数据集健康检查通过，未发现问题'
                }
            
            # 统计问题
            error_count = result.issues_by_severity.get(IssueSeverity.ERROR, 0)
            warning_count = result.issues_by_severity.get(IssueSeverity.WARNING, 0)
            info_count = result.issues_by_severity.get(IssueSeverity.INFO, 0)
            
            # 判断是否建议处理
            suggestion = ""
            if error_count > 0:
                suggestion = f"发现 {error_count} 个错误问题，强烈建议先到质检中心处理"
            elif warning_count > 0:
                suggestion = f"发现 {warning_count} 个警告问题，建议先到质检中心查看"
            else:
                suggestion = f"发现 {info_count} 个信息提示，可继续导出"
            
            return {
                'has_issues': result.issues_found > 0,
                'total_issues': result.issues_found,
                'error_count': error_count,
                'warning_count': warning_count,
                'info_count': info_count,
                'suggestion': suggestion,
                'result': result
            }
        except Exception as e:
            # 如果检查失败，只记录日志，不阻止导出
            return {
                'has_issues': False,
                'message': f'健康检查失败（不影响导出）: {str(e)}'
            }
    
    def _export_dataset(self):
        """导出数据集"""
        if not self.current_precheck_result or self.current_precheck_result['status'] == 'error':
            messagebox.showwarning("请先运行预检查", "请先运行预检查并确保通过后再导出")
            return
        
        export_dir = self.export_dir_var.get().strip()
        if not export_dir:
            messagebox.showwarning("导出目录未设置", "请先设置导出目录")
            return
        
        # 确认导出
        confirm = messagebox.askyesno(
            "确认导出",
            f"确认要将数据集导出到以下目录吗？\n\n{export_dir}\n\n"
            f"这将创建以下子目录:\n"
            f"  • images/train, images/val, images/test\n"
            f"  • labels/train, labels/val, labels/test\n"
            f"  • data.yaml, export_report.json"
        )
        if not confirm:
            return
        
        # 获取比例
        train_ratio = round(self.train_ratio_var.get(), 2)
        val_ratio = round(self.val_ratio_var.get(), 2)
        test_ratio = round(self.test_ratio_var.get(), 2)
        
        # 导出数据集
        try:
            result = export_dataset_with_split(
                self.context.image_dir,
                self.context.label_dir,
                export_dir,
                self.context.class_names,
                train_ratio,
                val_ratio,
                test_ratio
            )
            
            # 显示结果
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", "end")
            
            lines = []
            if result['status'] == 'error':
                lines.append(f"❌ 导出失败: {result['message']}")
            else:
                lines.append(f"✅ {result['message']}")
                lines.append("")
                lines.append("【导出摘要】")
                lines.append(f"  导出目录: {result['output_dir']}")
                lines.append(f"  导出时间: {result['start_time']} → {result['end_time']} ({result['duration_seconds']:.1f}秒)")
                lines.append("")
                lines.append("【数据集统计】")
                lines.append(f"  总导出数量: {result['exported_count']}")
                lines.append(f"  Train集: {result['train_count']}")
                lines.append(f"  Val集: {result['val_count']}")
                lines.append(f"  Test集: {result['test_count']}")
                lines.append(f"  类别数: {result['class_count']}")
                lines.append("")
                lines.append("【文件结构】")
                lines.append(f"  {export_dir}/")
                lines.append(f"  ├── images/")
                lines.append(f"  │   ├── train/")
                lines.append(f"  │   ├── val/")
                lines.append(f"  │   └── test/")
                lines.append(f"  ├── labels/")
                lines.append(f"  │   ├── train/")
                lines.append(f"  │   ├── val/")
                lines.append(f"  │   └── test/")
                lines.append(f"  ├── data.yaml")
                lines.append(f"  └── export_report.json")
                lines.append("")
                
                if result['skipped_count'] > 0:
                    lines.append(f"【跳过文件 ({result['skipped_count']}个)】")
                    for i, skipped in enumerate(result['skipped_files'][:3], 1):
                        lines.append(f"  {i}. {skipped['image']}: {skipped['error']}")
                    if result['skipped_count'] > 3:
                        lines.append(f"  还有{result['skipped_count'] - 3}个文件未显示...")
                    lines.append("")
                
                lines.append("【下一步建议】")
                lines.append("  1. 检查导出目录中的data.yaml文件")
                lines.append("  2. 使用训练中心开始训练")
                lines.append("  3. 如有问题，可查看export_report.json获取详情")
                
                # 更新结果文本
                self.result_text.insert("1.0", "\n".join(lines))
                
                # 保存配置
                if 'paths' not in self.context.config_data:
                    self.context.config_data['paths'] = {}
                self.context.config_data['paths']['output_dataset_dir'] = export_dir
                
                # 显示成功消息
                messagebox.showinfo(
                    "导出成功",
                    f"数据集导出成功！\n\n"
                    f"共导出{result['exported_count']}个图片-标签对。\n"
                    f"导出目录: {export_dir}\n\n"
                    f"请检查data.yaml文件配置是否正确。"
                )
            
            self.result_text.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("导出失败", f"导出数据集时发生错误:\n{str(e)}")
    
    def _view_export_report(self):
        """查看导出报告（预留功能）"""
        export_dir = self.export_dir_var.get().strip()
        if not export_dir or not os.path.exists(export_dir):
            messagebox.showwarning("目录不存在", "导出目录不存在，请先导出数据集")
            return
        
        report_path = os.path.join(export_dir, "export_report.json")
        if not os.path.exists(report_path):
            messagebox.showwarning("报告不存在", "导出报告不存在")
            return
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # 创建报告查看窗口
            report_window = tk.Toplevel(self.window)
            report_window.title("导出报告查看")
            report_window.geometry("800x600")
            report_window.configure(bg=self.bg_main)
            report_window.transient(self.window)
            
            # 标题
            title_frame = tk.Frame(report_window, bg=self.bg_main)
            title_frame.pack(fill="x", padx=14, pady=14)
            
            tk.Label(
                title_frame,
                text="📋 导出报告详情",
                bg=self.bg_main,
                fg=self.text_main,
                font=("Microsoft YaHei", 16, "bold")
            ).pack(side="left")
            
            # 关闭按钮
            tk.Button(
                title_frame,
                text="关闭",
                command=report_window.destroy,
                bg=self.border,
                fg=self.text_main,
                font=("Microsoft YaHei", 9),
                padx=12,
                pady=4,
                relief="flat"
            ).pack(side="right")
            
            # 内容
            content_frame = tk.Frame(report_window, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
            content_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
            
            report_text = tk.Text(
                content_frame,
                bg="#1e2229",
                fg=self.text_main,
                font=("Microsoft YaHei", 9),
                wrap="word",
                relief="flat",
                padx=12,
                pady=12
            )
            report_text.pack(fill="both", expand=True, padx=2, pady=2)
            
            # 格式化JSON显示
            report_text.insert("1.0", json.dumps(report_data, ensure_ascii=False, indent=2))
            report_text.config(state="disabled")
            
            # 滚动条
            scrollbar = tk.Scrollbar(content_frame, command=report_text.yview)
            report_text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            
        except Exception as e:
            messagebox.showerror("读取报告失败", f"读取导出报告时发生错误:\n{str(e)}")


    def destroy(self):
        """销毁窗口，清理回调"""
        if hasattr(self, 'language_manager') and hasattr(self.language_manager, 'unregister_callback'):
            self.language_manager.unregister_callback(self._refresh_ui_on_language_change)
        if hasattr(self, 'style_manager'):
            self.style_manager.unregister_callback(self._refresh_ui_on_style_change)
        self.window.destroy()

def open_dataset_export_window(master, context):
    """
    打开数据集导出窗口（方便函数）
    
    Args:
        master: 父窗口
        context: WorkbenchContext 实例
    """
    window = DatasetExportWindow(master, context)
    return window