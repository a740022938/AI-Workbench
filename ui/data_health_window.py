#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
data_health_window.py - 数据集健康检查窗口

职责：展示数据集健康检查结果，提供交互操作。
目标：为用户提供直观的数据质量检查和问题定位界面。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from typing import Optional, Callable, List

from core.data_health_manager import (
    DataHealthManager, 
    HealthCheckResult, 
    HealthIssue,
    IssueSeverity,
    IssueType
)
from core.data_health_fixer import DataHealthFixer, FixResult
from core.closed_loop_manager import ClosedLoopManager, BadCaseSource
from core.language_manager import t
from core.ui_style_manager import get_style_manager


class DataHealthWindow(tk.Toplevel):
    """数据集健康检查窗口"""
    
    def __init__(self, master, context, on_jump_to_image: Optional[Callable] = None):
        """
        初始化窗口
        
        Args:
            master: 父窗口
            context: WorkbenchContext 实例
            on_jump_to_image: 跳转到指定图片的回调函数
        """
        super().__init__(master)
        
        self.context = context
        self.on_jump_to_image = on_jump_to_image
        self.health_manager = DataHealthManager(context)
        self.health_fixer = DataHealthFixer(self.health_manager)
        self.current_result: Optional[HealthCheckResult] = None
        self.current_selected_issue: Optional[HealthIssue] = None
        self.filtered_issues: List[HealthIssue] = []
        
        # 排序和视图状态
        self.sort_by = "severity"  # 默认按严重程度排序
        self.sort_order = "desc"   # 默认降序（错误优先）
        self.view_mode = "all"     # 视图模式：all, error, warning, info, auto_fixable, manual_fix
        
        # 窗口设置
        self.title(t("TITLE_DATA_HEALTH"))
        self.geometry("1200x800")
        self.minsize(1000, 600)
        self.configure(bg="#16181d")
        
        # UI管理器
        self.style_manager = get_style_manager()
        self.language_manager = t._manager  # 通过t函数获取管理器
        
        # 样式颜色
        self._update_colors_from_style()
        self.bg_main = "#16181d"
        self.bg_card = "#252a33"
        self.text_main = "#f5f7fa"
        self.text_sub = "#aeb6c2"
        self.border = "#2d3440"
        self.success_color = "#10b981"  # 绿色
        self.warning_color = "#f59e0b"  # 黄色
        self.error_color = "#ef4444"    # 红色
        self.info_color = "#3b82f6"     # 蓝色
        
        # 构建UI
        self._build_ui()
        
        # 注册回调
        if hasattr(self.language_manager, 'register_callback'):
            self.language_manager.register_callback(self._refresh_ui_on_language_change)
        self.style_manager.register_callback(self._refresh_ui_on_style_change)
        
        # 默认运行一次检查
        self.run_health_check()
    
    def _update_colors_from_style(self):
        """从风格管理器更新颜色值"""
        theme = self.style_manager.get_current_theme_definition()
        
        # 更新基础颜色
        self.bg_main = theme.colors.get("background", "#16181d")
        self.bg_card = theme.colors.get("surface", "#252a33")
        self.text_main = theme.colors.get("text_primary", "#f5f7fa")
        self.text_sub = theme.colors.get("text_secondary", "#aeb6c2")
        self.border = theme.colors.get("border", "#2d3440")
        self.success_color = theme.colors.get("success", "#10b981")
        self.warning_color = theme.colors.get("warning", "#f59e0b")
        self.error_color = theme.colors.get("error", "#ef4444")
        self.info_color = theme.colors.get("primary", "#3b82f6")
        
        # 更新窗口背景
        self.configure(bg=self.bg_main)
    
    def _refresh_ui_on_style_change(self):
        """风格切换时刷新UI样式"""
        # 更新颜色值
        self._update_colors_from_style()
        
        # 刷新窗口背景
        self.configure(bg=self.bg_main)
        
        # 刷新主容器背景
        if hasattr(self, 'container'):
            self.container.config(bg=self.bg_main)
        
        # 刷新标题栏背景
        if hasattr(self, 'title_frame'):
            self.title_frame.config(bg=self.bg_main)
        
        # 刷新工具栏背景
        if hasattr(self, 'toolbar_frame'):
            self.toolbar_frame.config(bg=self.bg_main)
        
        # 刷新内容区域背景
        if hasattr(self, 'content_frame'):
            self.content_frame.config(bg=self.bg_main)
        
        # 刷新卡片背景
        card_widgets = [
            'stats_card', 'issues_card', 'summary_card', 'image_summary_card'
        ]
        
        for card_name in card_widgets:
            if hasattr(self, card_name):
                card = getattr(self, card_name)
                try:
                    card.config(bg=self.bg_card, highlightbackground=self.border)
                except:
                    pass
        
        # 刷新按钮颜色
        button_widgets = [
            'run_check_btn', 'fix_all_btn', 'export_report_btn',
            'jump_to_image_btn', 'refresh_btn', 'add_to_closed_loop_btn'
        ]
        
        for btn_name in button_widgets:
            if hasattr(self, btn_name):
                btn = getattr(self, btn_name)
                try:
                    btn.config(bg=self.info_color, fg=self.text_main)
                except:
                    pass
        
        # 刷新表格颜色
        if hasattr(self, 'issues_tree'):
            try:
                style = ttk.Style()
                style.configure("Custom.Treeview", 
                              background=self.bg_card,
                              foreground=self.text_main,
                              fieldbackground=self.bg_card)
                self.issues_tree.config(style="Custom.Treeview")
            except:
                pass
        
        print(f"质检中心风格已刷新，当前风格: {self.style_manager.current_style.value}")
    
    def _refresh_ui_on_language_change(self):
        """语言切换时刷新UI文案"""
        # 更新窗口标题
        self.title(t("TITLE_DATA_HEALTH"))
        
        # 更新按钮文本
        if hasattr(self, 'run_check_btn'):
            self.run_check_btn.config(text="运行健康检查")
        if hasattr(self, 'fix_all_btn'):
            self.fix_all_btn.config(text="一键修复全部")
        if hasattr(self, 'export_report_btn'):
            self.export_report_btn.config(text="导出报告")
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.config(text="刷新")
        if hasattr(self, 'add_to_closed_loop_btn'):
            self.add_to_closed_loop_btn.config(text="添加到闭环修正")
    
    def _build_ui(self):
        """构建用户界面"""
        # 主容器
        container = tk.Frame(self, bg=self.bg_main)
        container.pack(fill="both", expand=True, padx=14, pady=14)
        
        # 标题栏
        self._build_title_bar(container)
        
        # 分隔线
        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=10)
        
        # 主要内容区域（左右分割）
        main_content = tk.Frame(container, bg=self.bg_main)
        main_content.pack(fill="both", expand=True)
        
        # 左栏：统计信息
        left_frame = tk.Frame(main_content, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        # 右栏：详细问题列表与图片汇总（选项卡）
        self.right_notebook = ttk.Notebook(main_content)
        self.right_notebook.pack(side="right", fill="both", expand=True)
        
        # 创建两个标签页
        issues_frame = tk.Frame(self.right_notebook, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        images_frame = tk.Frame(self.right_notebook, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        
        self.right_notebook.add(issues_frame, text="🔍 详细问题列表")
        self.right_notebook.add(images_frame, text="🖼️ 按图片汇总")
        
        self._build_statistics_panel(left_frame)
        self._build_issues_panel(issues_frame)
        self._build_image_summary_panel(images_frame)
        
        # 初始化排序状态
        self.after(100, self._init_sort_state)
    
    def _build_title_bar(self, parent):
        """构建标题栏和操作按钮"""
        title_bar = tk.Frame(parent, bg=self.bg_main)
        title_bar.pack(fill="x", pady=(0, 10))
        
        # 标题
        tk.Label(
            title_bar,
            text="📊 数据集健康检查",
            bg=self.bg_main,
            fg=self.text_main,
            font=("Microsoft YaHei", 16, "bold")
        ).pack(side="left")
        
        # 操作按钮区域
        button_frame = tk.Frame(title_bar, bg=self.bg_main)
        button_frame.pack(side="right")
        
        # 刷新按钮
        refresh_btn = tk.Button(
            button_frame,
            text="🔄 重新检查",
            command=self.run_health_check,
            bg="#3b82f6",
            fg="white",
            font=("Microsoft YaHei", 10),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2"
        )
        refresh_btn.pack(side="left", padx=4)
        
        # 导出报告按钮
        export_btn = tk.Button(
            button_frame,
            text="📄 导出报告",
            command=self.export_report,
            bg="#10b981",
            fg="white",
            font=("Microsoft YaHei", 10),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2"
        )
        export_btn.pack(side="left", padx=4)
        
        # 快速修复按钮
        fix_btn = tk.Button(
            button_frame,
            text="🔧 快速修复",
            command=self.show_fix_dialog,
            bg="#f59e0b",
            fg="white",
            font=("Microsoft YaHei", 10),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            state="normal"
        )
        fix_btn.pack(side="left", padx=4)
        
        # 修复历史按钮
        history_btn = tk.Button(
            button_frame,
            text="📜 修复历史",
            command=self.show_fix_history,
            bg="#8b5cf6",
            fg="white",
            font=("Microsoft YaHei", 10),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            state="normal"
        )
        history_btn.pack(side="left", padx=4)
        
        # 关闭按钮
        close_btn = tk.Button(
            button_frame,
            text="✕ 关闭",
            command=self.destroy,
            bg=self.border,
            fg=self.text_main,
            font=("Microsoft YaHei", 10),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2"
        )
        close_btn.pack(side="left", padx=4)
    
    def _build_statistics_panel(self, parent):
        """构建统计信息面板"""
        # 面板标题
        title_frame = tk.Frame(parent, bg=self.bg_card, height=48)
        title_frame.pack(fill="x", padx=12, pady=12)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="📈 检查结果统计",
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 13, "bold")
        ).pack(side="left")
        
        # 统计内容容器
        stats_container = tk.Frame(parent, bg=self.bg_card)
        stats_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # 使用网格布局
        for i in range(6):
            stats_container.grid_rowconfigure(i, weight=1)
        stats_container.grid_columnconfigure(0, weight=1)
        stats_container.grid_columnconfigure(1, weight=1)
        
        # 统计数据标签（初始化时为空）
        self.stats_labels = {}
        
        # 基本统计
        stats = [
            ("图片目录", "image_dir", ""),
            ("标签目录", "label_dir", ""),
            ("图片数量", "image_count", "0"),
            ("标签数量", "label_count", "0"),
            ("类别数量", "class_count", "0"),
            ("类别来源", "class_source", "未设置"),
        ]
        
        for i, (label_text, key, default) in enumerate(stats):
            # 标签
            label = tk.Label(
                stats_container,
                text=f"{label_text}:",
                bg=self.bg_card,
                fg=self.text_sub,
                font=("Microsoft YaHei", 10),
                anchor="w"
            )
            label.grid(row=i, column=0, sticky="w", padx=(0, 10), pady=6)
            
            # 值
            value_label = tk.Label(
                stats_container,
                text=default,
                bg=self.bg_card,
                fg=self.text_main,
                font=("Microsoft YaHei", 10, "bold"),
                anchor="w"
            )
            value_label.grid(row=i, column=1, sticky="w", pady=6)
            self.stats_labels[key] = value_label
        
        # 分隔线
        ttk.Separator(stats_container, orient="horizontal").grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=10
        )
        
        # 问题统计
        issue_stats = [
            ("检查时间", "check_time", "未检查"),
            ("检查项数", "total_checks", "0"),
            ("发现问题", "issues_found", "0"),
            ("错误数量", "error_count", "0", self.error_color),
            ("警告数量", "warning_count", "0", self.warning_color),
            ("信息提示", "info_count", "0", self.info_color),
        ]
        
        for i, (label_text, key, default, *color) in enumerate(issue_stats, start=7):
            # 标签
            label = tk.Label(
                stats_container,
                text=f"{label_text}:",
                bg=self.bg_card,
                fg=self.text_sub,
                font=("Microsoft YaHei", 10),
                anchor="w"
            )
            label.grid(row=i, column=0, sticky="w", padx=(0, 10), pady=6)
            
            # 值
            fg_color = color[0] if color else self.text_main
            value_label = tk.Label(
                stats_container,
                text=default,
                bg=self.bg_card,
                fg=fg_color,
                font=("Microsoft YaHei", 10, "bold"),
                anchor="w"
            )
            value_label.grid(row=i, column=1, sticky="w", pady=6)
            self.stats_labels[key] = value_label
        
        # 总体状态
        self.overall_status_label = tk.Label(
            stats_container,
            text="请点击'重新检查'开始检查",
            bg=self.bg_card,
            fg=self.text_sub,
            font=("Microsoft YaHei", 11),
            anchor="w",
            wraplength=300
        )
        self.overall_status_label.grid(row=13, column=0, columnspan=2, sticky="w", pady=20)
    
    def _build_issues_panel(self, parent):
        """构建问题列表面板"""
        # 面板标题
        title_frame = tk.Frame(parent, bg=self.bg_card, height=48)
        title_frame.pack(fill="x", padx=12, pady=12)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="🔍 详细问题列表",
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 13, "bold")
        ).pack(side="left")
        
        # 筛选和排序工具栏
        toolbar_frame = tk.Frame(title_frame, bg=self.bg_card)
        toolbar_frame.pack(side="right")
        
        # 视图筛选按钮
        filter_frame = tk.Frame(toolbar_frame, bg=self.bg_card)
        filter_frame.pack(side="left", padx=(0, 10))
        
        self.filter_var = tk.StringVar(value="all")
        
        view_buttons = [
            ("全部", "all", self.text_sub),
            ("错误", "error", self.error_color),
            ("警告", "warning", self.warning_color),
            ("信息", "info", self.info_color),
            ("可自动修复", "auto_fixable", "#10b981"),  # 绿色
            ("需人工处理", "manual_fix", "#f59e0b")     # 黄色
        ]
        
        for text, value, color in view_buttons:
            tk.Radiobutton(
                filter_frame,
                text=text,
                variable=self.filter_var,
                value=value,
                command=self._refresh_issues_list,
                bg=self.bg_card,
                fg=color,
                selectcolor=self.bg_card,
                font=("Microsoft YaHei", 9),
                cursor="hand2"
            ).pack(side="left", padx=2)
        
        # 排序控件
        sort_frame = tk.Frame(toolbar_frame, bg=self.bg_card)
        sort_frame.pack(side="left")
        
        tk.Label(
            sort_frame,
            text="排序:",
            bg=self.bg_card,
            fg=self.text_sub,
            font=("Microsoft YaHei", 9)
        ).pack(side="left", padx=(0, 4))
        
        # 排序字段选择
        self.sort_var = tk.StringVar(value="severity")
        sort_options = [
            ("严重程度", "severity"),
            ("问题类型", "type"),
            ("文件名", "file"),
            ("可自动修复", "auto_fixable")
        ]
        
        sort_menu = tk.OptionMenu(
            sort_frame,
            self.sort_var,
            *[opt[0] for opt in sort_options],
            command=self._on_sort_changed
        )
        sort_menu.config(
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            relief="flat",
            cursor="hand2"
        )
        sort_menu["menu"].config(
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 9)
        )
        sort_menu.pack(side="left", padx=2)
        
        # 排序顺序按钮
        self.sort_order_var = tk.StringVar(value="desc")
        
        def toggle_sort_order():
            current = self.sort_order_var.get()
            new = "asc" if current == "desc" else "desc"
            self.sort_order_var.set(new)
            self._refresh_issues_list()
        
        self.sort_order_btn = tk.Button(
            sort_frame,
            text="↓",
            command=toggle_sort_order,
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 9, "bold"),
            relief="flat",
            cursor="hand2",
            width=2
        )
        self.sort_order_btn.pack(side="left", padx=2)
        
        # 问题列表容器
        issues_container = tk.Frame(parent, bg=self.bg_card)
        issues_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # 创建Treeview
        columns = ("severity", "type", "file", "message", "suggestion")
        self.tree = ttk.Treeview(
            issues_container,
            columns=columns,
            show="tree headings",
            height=15,
            selectmode="browse"
        )
        
        # 设置列
        self.tree.heading("#0", text="", anchor="w")
        self.tree.column("#0", width=0, stretch=False)
        
        self.tree.heading("severity", text="严重程度", anchor="w")
        self.tree.column("severity", width=80, stretch=False)
        
        self.tree.heading("type", text="问题类型", anchor="w")
        self.tree.column("type", width=150, stretch=False)
        
        self.tree.heading("file", text="相关文件", anchor="w")
        self.tree.column("file", width=200, stretch=True)
        
        self.tree.heading("message", text="问题描述", anchor="w")
        self.tree.column("message", width=300, stretch=True)
        
        self.tree.heading("suggestion", text="修复建议", anchor="w")
        self.tree.column("suggestion", width=250, stretch=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(issues_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        issues_container.grid_rowconfigure(0, weight=1)
        issues_container.grid_columnconfigure(0, weight=1)
        
        # 详情面板
        detail_frame = tk.Frame(issues_container, bg=self.bg_card, height=120)
        detail_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        detail_frame.grid_propagate(False)
        
        tk.Label(
            detail_frame,
            text="问题详情:",
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 10, "bold")
        ).pack(anchor="w", padx=4, pady=4)
        
        self.detail_text = tk.Text(
            detail_frame,
            bg="#1e2229",
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            height=6,
            wrap="word",
            relief="flat",
            padx=8,
            pady=8
        )
        self.detail_text.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.detail_text.config(state="disabled")
        
        # 操作按钮
        button_frame = tk.Frame(detail_frame, bg=self.bg_card)
        button_frame.pack(fill="x", padx=4, pady=(0, 4))
        
        self.jump_btn = tk.Button(
            button_frame,
            text="跳转到文件",
            command=self._jump_to_selected_file,
            bg="#3b82f6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.jump_btn.pack(side="left", padx=2)
        
        # 修复当前问题按钮
        self.fix_current_btn = tk.Button(
            button_frame,
            text="修复当前问题",
            command=self.fix_current_issue,
            bg="#10b981",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.fix_current_btn.pack(side="left", padx=2)
        
        # 修复当前图片同类问题按钮
        self.fix_similar_btn = tk.Button(
            button_frame,
            text="修复当前图片同类问题",
            command=self.fix_similar_issues,
            bg="#f59e0b",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.fix_similar_btn.pack(side="left", padx=2)
        
        # 手动处理按钮（针对不可自动修复的问题）
        self.manual_fix_btn = tk.Button(
            button_frame,
            text="手动处理",
            command=self.show_manual_fix_guidance,
            bg="#8b5cf6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.manual_fix_btn.pack(side="left", padx=2)
        
        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self._on_issue_selected)
    
    def run_health_check(self):
        """运行健康检查"""
        try:
            # 显示加载状态
            self.overall_status_label.config(
                text="正在检查数据集...",
                fg=self.info_color
            )
            self.update()
            
            # 执行检查
            self.current_result = self.health_manager.run_full_health_check()
            
            # 更新统计信息
            self._update_statistics()
            
            # 更新问题列表
            self._refresh_issues_list()
            
            # 更新图片汇总
            self._refresh_image_summary()
            
            # 更新总体状态
            if self.current_result.issues_found == 0:
                self.overall_status_label.config(
                    text="✅ 数据集健康检查通过！未发现任何问题。",
                    fg=self.success_color
                )
            else:
                error_count = self.current_result.issues_by_severity[IssueSeverity.ERROR]
                warning_count = self.current_result.issues_by_severity[IssueSeverity.WARNING]
                info_count = self.current_result.issues_by_severity[IssueSeverity.INFO]
                
                status_parts = []
                if error_count > 0:
                    status_parts.append(f"{error_count}个错误")
                if warning_count > 0:
                    status_parts.append(f"{warning_count}个警告")
                if info_count > 0:
                    status_parts.append(f"{info_count}个信息提示")
                
                status_text = f"⚠️ 发现{len(status_parts)}类问题: {', '.join(status_parts)}"
                self.overall_status_label.config(
                    text=status_text,
                    fg=self.warning_color if error_count == 0 else self.error_color
                )
            
        except Exception as e:
            messagebox.showerror("检查失败", f"执行健康检查时发生错误:\n{e}")
            self.overall_status_label.config(
                text=f"❌ 检查失败: {str(e)}",
                fg=self.error_color
            )
    
    def _on_tree_right_click(self, event):
        """树形控件右键点击事件"""
        # 获取点击位置的行
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        
        # 选中该行
        self.tree.selection_set(row_id)
        
        # 获取选中的问题
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # 创建右键菜单
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="添加到闭环修正", command=self._add_to_closed_loop_for_selected_issue)
        menu.add_separator()
        menu.add_command(label="跳转到文件", command=self._jump_to_selected_file)
        
        # 显示菜单
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _add_to_closed_loop_for_selected_issue(self):
        """将选中的问题添加到闭环修正"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择一个健康检查问题")
            return
        
        # 获取选中的问题
        item = selected_items[0]
        values = self.tree.item(item, "values")
        if not values or len(values) < 5:
            messagebox.showerror("错误", "无法获取问题详情")
            return
        
        # 从过滤的问题列表中查找对应的问题对象
        # 注意：这里的索引提取逻辑可能需要根据实际item ID格式调整
        try:
            # item ID格式通常是'I001'之类的
            issue_index = int(item[1:])  # 去掉开头的'I'
        except:
            # 如果解析失败，尝试从当前显示的问题中查找匹配项
            issue_index = -1
            for i, issue in enumerate(self.filtered_issues):
                if (issue.file_name == values[2] and 
                    issue.issue_type == values[1] and 
                    issue.message == values[3]):
                    issue_index = i
                    break
        
        if issue_index < 0 or issue_index >= len(self.filtered_issues):
            messagebox.showerror("错误", "无法找到对应的问题对象")
            return
        
        issue = self.filtered_issues[issue_index]
        
        # 创建闭环管理器实例
        manager = ClosedLoopManager()
        
        # 生成问题摘要
        severity_text = values[0]
        issue_type = values[1]
        file_name = values[2]
        message = values[3]
        suggestion = values[4]
        
        problem_summary = f"质检问题 - {issue_type}: {message}"
        
        # 添加bad case
        success, msg = manager.add_bad_case(
            image_name=file_name,
            source_type=BadCaseSource.QUALITY_CHECK,
            problem_summary=problem_summary,
            issue_type=issue_type,
            class_name=issue.class_name if hasattr(issue, 'class_name') else "",
            confidence=0.0,
            file_path=issue.file_path if hasattr(issue, 'file_path') else "",
            label_path=issue.label_path if hasattr(issue, 'label_path') else "",
            resolution_note=f"来自质检中心: {suggestion}"
        )
        
        if success:
            messagebox.showinfo("成功", f"已添加到闭环修正中心\n{msg}")
        else:
            messagebox.showerror("错误", f"添加失败: {msg}")
    
    def _update_statistics(self):
        """更新统计信息"""
        if not self.current_result:
            return
        
        # 基本统计
        self.stats_labels["image_dir"].config(
            text=self.current_result.summary.get("image_directory", "未设置")
        )
        self.stats_labels["label_dir"].config(
            text=self.current_result.summary.get("label_directory", "未设置")
        )
        self.stats_labels["image_count"].config(
            text=str(self.current_result.summary.get("image_files_count", 0))
        )
        self.stats_labels["label_count"].config(
            text=str(self.current_result.summary.get("label_files_count", 0))
        )
        self.stats_labels["class_count"].config(
            text=str(self.current_result.summary.get("current_class_names_count", 0))
        )
        self.stats_labels["class_source"].config(
            text=self.current_result.summary.get("current_class_names_source", "未知")
        )
        
        # 检查统计
        self.stats_labels["check_time"].config(
            text=self.current_result.timestamp
        )
        self.stats_labels["total_checks"].config(
            text=str(self.current_result.total_checks)
        )
        self.stats_labels["issues_found"].config(
            text=str(self.current_result.issues_found)
        )
        self.stats_labels["error_count"].config(
            text=str(self.current_result.issues_by_severity[IssueSeverity.ERROR]),
            fg=self.error_color
        )
        self.stats_labels["warning_count"].config(
            text=str(self.current_result.issues_by_severity[IssueSeverity.WARNING]),
            fg=self.warning_color
        )
        self.stats_labels["info_count"].config(
            text=str(self.current_result.issues_by_severity[IssueSeverity.INFO]),
            fg=self.info_color
        )
    
    def _on_sort_changed(self, *args):
        """排序选项改变事件"""
        # 更新排序按钮文本
        order = self.sort_order_var.get()
        self.sort_order_btn.config(text="↑" if order == "asc" else "↓")
        self._refresh_issues_list()
    
    def _init_sort_state(self):
        """初始化排序状态"""
        # 设置排序按钮初始文本
        order = self.sort_order_var.get()
        self.sort_order_btn.config(text="↑" if order == "asc" else "↓")
    
    def _refresh_issues_list(self):
        """刷新问题列表（支持筛选、排序）"""
        if not self.current_result:
            return
        
        # 清空现有项
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 获取筛选条件
        filter_value = self.filter_var.get()
        
        # 筛选问题
        issues_to_show = []
        for issue in self.current_result.issues:
            if filter_value == "all":
                issues_to_show.append(issue)
            elif filter_value == "error":
                if issue.severity == IssueSeverity.ERROR:
                    issues_to_show.append(issue)
            elif filter_value == "warning":
                if issue.severity == IssueSeverity.WARNING:
                    issues_to_show.append(issue)
            elif filter_value == "info":
                if issue.severity == IssueSeverity.INFO:
                    issues_to_show.append(issue)
            elif filter_value == "auto_fixable":
                can_fix, _ = self.health_fixer.can_fix_issue(issue)
                if can_fix:
                    issues_to_show.append(issue)
            elif filter_value == "manual_fix":
                can_fix, _ = self.health_fixer.can_fix_issue(issue)
                if not can_fix:
                    issues_to_show.append(issue)
        
        # 获取排序设置
        sort_display = self.sort_var.get()
        sort_order = self.sort_order_var.get()
        
        # 将显示文本映射到排序键和函数
        sort_mapping = {
            "严重程度": ("severity", lambda issue: issue.severity.value),
            "问题类型": ("type", lambda issue: issue.issue_type.value),
            "文件名": ("file", lambda issue: (issue.file_name or "").lower()),
            "可自动修复": ("auto_fixable", lambda issue: not self.health_fixer.can_fix_issue(issue)[0])
        }
        
        sort_key, sort_func = sort_mapping.get(sort_display, ("severity", lambda issue: issue.severity.value))
        
        # 排序问题
        if sort_order == "desc":
            # 降序：对于可自动修复，True（可修复）在前，False（不可修复）在后
            # 对于严重程度，ERROR > WARNING > INFO
            reverse = True
            if sort_key == "auto_fixable":
                # 可自动修复的应该排在前面（True > False）
                reverse = True
        else:
            reverse = False
            if sort_key == "auto_fixable":
                # 升序时不可修复的在前
                reverse = False
        
        # 处理严重程度特殊排序（自定义顺序）
        if sort_key == "severity":
            severity_order = {IssueSeverity.ERROR: 0, IssueSeverity.WARNING: 1, IssueSeverity.INFO: 2}
            issues_to_show.sort(key=lambda issue: severity_order[issue.severity], reverse=reverse)
        else:
            issues_to_show.sort(key=sort_func, reverse=reverse)
        
        # 添加项到Treeview
        for issue in issues_to_show:
            # 严重程度文本和颜色
            severity_text = issue.severity.value.upper()
            if issue.severity == IssueSeverity.ERROR:
                severity_tag = "error"
            elif issue.severity == IssueSeverity.WARNING:
                severity_tag = "warning"
            else:
                severity_tag = "info"
            
            # 文件显示文本
            file_display = issue.file_name if issue.file_name else "-"
            
            # 检查是否可自动修复
            can_fix, fix_reason = self.health_fixer.can_fix_issue(issue)
            fix_status = "可自动修复" if can_fix else "需人工处理"
            
            self.tree.insert(
                "", "end",
                values=(
                    severity_text,
                    f"{issue.issue_type.value} ({fix_status})",
                    file_display,
                    issue.message[:100] + "..." if len(issue.message) > 100 else issue.message,
                    issue.suggestion[:80] + "..." if len(issue.suggestion) > 80 else issue.suggestion
                ),
                tags=(severity_tag,)
            )
        
        # 配置标签样式
        self.tree.tag_configure("error", foreground=self.error_color)
        self.tree.tag_configure("warning", foreground=self.warning_color)
        self.tree.tag_configure("info", foreground=self.info_color)
        
        # 存储筛选后的问题列表供选择事件使用
        self.filtered_issues = issues_to_show
        
        # 更新详情面板
        self._clear_detail_panel()
    
    def _on_issue_selected(self, event):
        """处理问题选择事件（使用筛选后的列表）"""
        selection = self.tree.selection()
        if not selection or not self.filtered_issues:
            self._clear_detail_panel()
            return
        
        # 获取选中的行索引
        selected_item = selection[0]
        item_index = self.tree.index(selected_item)
        
        # 使用筛选后的问题列表
        if item_index < len(self.filtered_issues):
            issue = self.filtered_issues[item_index]
            self._update_detail_panel(issue)
    
    def _update_detail_panel(self, issue: HealthIssue):
        """更新详情面板"""
        # 清空现有内容
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        
        # 构建详情文本
        detail_lines = []
        
        # 基本信息
        detail_lines.append(f"【问题类型】{issue.issue_type.value}")
        detail_lines.append(f"【严重程度】{issue.severity.value.upper()}")
        detail_lines.append("")
        
        if issue.file_name:
            detail_lines.append(f"【相关文件】{issue.file_name}")
        
        if issue.file_path:
            detail_lines.append(f"【文件路径】{issue.file_path}")
        
        if issue.line_number > 0:
            detail_lines.append(f"【行号】{issue.line_number}")
        
        detail_lines.append("")
        detail_lines.append("【问题描述】")
        detail_lines.append(issue.message)
        detail_lines.append("")
        
        detail_lines.append("【修复建议】")
        detail_lines.append(issue.suggestion)
        detail_lines.append("")
        
        if issue.details:
            detail_lines.append("【详细信息】")
            for key, value in issue.details.items():
                detail_lines.append(f"  {key}: {value}")
        
        # 插入文本
        for line in detail_lines:
            self.detail_text.insert("end", line + "\n")
        
        # 设置只读
        self.detail_text.config(state="disabled")
        
        # 保存当前选中问题
        self.current_selected_issue = issue
        
        # 更新跳转按钮状态
        if issue.file_name and issue.file_path and self.on_jump_to_image:
            # 检查是否是图片文件
            is_image = any(issue.file_name.lower().endswith(ext) 
                          for ext in self.health_manager._valid_ext)
            if is_image:
                self.jump_btn.config(state="normal")
            else:
                self.jump_btn.config(state="disabled")
        else:
            self.jump_btn.config(state="disabled")
        
        # 更新修复按钮状态
        can_fix, reason = self.health_fixer.can_fix_issue(issue)
        if can_fix:
            self.fix_current_btn.config(state="normal", text=f"修复当前问题 ({reason})")
            self.fix_similar_btn.config(state="normal")
            self.manual_fix_btn.config(state="disabled", text="手动处理")
        else:
            self.fix_current_btn.config(state="disabled", text=f"无法自动修复: {reason}")
            self.fix_similar_btn.config(state="disabled")
            self.manual_fix_btn.config(state="normal", text="手动处理")
    
    def _clear_detail_panel(self):
        """清空详情面板"""
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", "请选择一个问题查看详情...")
        self.detail_text.config(state="disabled")
        self.jump_btn.config(state="disabled")
        self.current_selected_issue = None
        self.fix_current_btn.config(state="disabled", text="修复当前问题")
        self.fix_similar_btn.config(state="disabled")
        self.manual_fix_btn.config(state="disabled", text="手动处理")
    
    def _jump_to_selected_file(self):
        """跳转到选中的文件"""
        selection = self.tree.selection()
        if not selection or not self.current_result or not self.on_jump_to_image:
            return
        
        # 获取选中的行索引
        selected_item = selection[0]
        item_index = self.tree.index(selected_item)
        
        # 根据筛选条件找到对应的问题
        filter_value = self.filter_var.get()
        if filter_value == "all":
            issues = self.current_result.issues
        elif filter_value == "error":
            issues = [i for i in self.current_result.issues 
                     if i.severity == IssueSeverity.ERROR]
        elif filter_value == "warning":
            issues = [i for i in self.current_result.issues 
                     if i.severity == IssueSeverity.WARNING]
        elif filter_value == "info":
            issues = [i for i in self.current_result.issues 
                     if i.severity == IssueSeverity.INFO]
        else:
            issues = []
        
        if item_index < len(issues):
            issue = issues[item_index]
            if issue.file_name and issue.file_path:
                # 调用回调函数
                try:
                    self.on_jump_to_image(issue.file_name)
                except Exception as e:
                    messagebox.showerror("跳转失败", f"无法跳转到文件:\n{e}")
    
    def export_report(self):
        """导出检查报告"""
        if not self.current_result:
            messagebox.showwarning("无数据", "请先运行健康检查")
            return
        
        # 选择保存路径
        file_path = filedialog.asksaveasfilename(
            title="导出健康检查报告",
            defaultextension=".txt",
            filetypes=[
                ("文本文件", "*.txt"),
                ("JSON文件", "*.json"),
                ("所有文件", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            if file_path.lower().endswith('.json'):
                success = self.health_manager.export_report_json(self.current_result, file_path)
                format_name = "JSON"
            else:
                success = self.health_manager.export_report_txt(self.current_result, file_path)
                format_name = "文本"
            
            if success:
                messagebox.showinfo(
                    "导出成功",
                    f"检查报告已导出为{format_name}格式:\n{file_path}"
                )
            else:
                messagebox.showerror("导出失败", "无法写入文件，请检查权限和磁盘空间")
                
        except Exception as e:
            messagebox.showerror("导出失败", f"导出报告时发生错误:\n{e}")
    
    def fix_current_issue(self):
        """修复当前选中的问题"""
        if not self.current_selected_issue:
            messagebox.showwarning("无选中问题", "请先选择一个要修复的问题")
            return
        
        # 确认修复
        issue = self.current_selected_issue
        confirm_msg = f"确定要修复此问题吗？\n\n问题类型: {issue.issue_type.value}\n文件: {issue.file_name}\n描述: {issue.message}"
        
        if not messagebox.askyesno("确认修复", confirm_msg):
            return
        
        try:
            # 启动修复会话
            session_id = self.health_fixer.start_fix_session()
            
            # 执行修复
            result = self.health_fixer.fix_single_issue(issue)
            
            # 结束会话并获取回执
            receipt = self.health_fixer.end_fix_session()
            
            if result.result.value == "success":
                # 显示修复结果
                message = f"修复成功: {result.message}\n\n"
                message += f"会话ID: {receipt.session_id}\n"
                message += f"修复统计: 尝试1个, 成功1个, 失败{receipt.summary['failed']}个"
                
                messagebox.showinfo("修复成功", message)
                # 刷新检查结果
                self.run_health_check()
            elif result.result.value == "not_supported":
                messagebox.showwarning("不支持修复", f"无法自动修复: {result.message}")
            elif result.result.value == "failed":
                messagebox.showerror("修复失败", f"修复失败: {result.message}")
            elif result.result.value == "cancelled":
                # 用户取消，无需提示
                pass
        
        except Exception as e:
            messagebox.showerror("修复异常", f"修复过程中发生错误:\n{e}")
    
    def fix_similar_issues(self):
        """修复当前图片中的同类问题（带预览）"""
        if not self.current_selected_issue:
            messagebox.showwarning("无选中问题", "请先选择一个要修复的问题")
            return
        
        issue = self.current_selected_issue
        if not issue.file_path:
            messagebox.showwarning("无文件路径", "无法确定文件路径")
            return
        
        # 生成修复预览
        try:
            preview_data = self.health_fixer.preview_fix_issues_in_file(
                file_path=issue.file_path,
                issue_types=[issue.issue_type]
            )
        except Exception as e:
            messagebox.showerror("预览失败", f"无法生成修复预览:\n{e}")
            return
        
        # 检查是否有可修复的问题
        if preview_data["fixable_issues"] == 0:
            messagebox.showinfo("无需修复", "该文件中没有可自动修复的同类问题")
            return
        
        # 构建预览消息
        lines = []
        lines.append("=" * 60)
        lines.append("批量修复预览")
        lines.append("=" * 60)
        lines.append(f"文件: {preview_data['file_name']}")
        lines.append(f"问题类型: {issue.issue_type.value}")
        lines.append("")
        lines.append(f"本次准备修复 {preview_data['fixable_issues']} 个问题")
        lines.append(f"涉及 {preview_data['file_count']} 个文件")
        lines.append("")
        
        if preview_data['fixable_by_type']:
            lines.append("可修复的问题类型:")
            for issue_type, count in preview_data['fixable_by_type'].items():
                lines.append(f"  • {issue_type}: {count}个")
            lines.append("")
        
        if preview_data['unfixable_by_type']:
            lines.append("将被跳过的问题类型（不支持自动修复）:")
            for issue_type, count in preview_data['unfixable_by_type'].items():
                lines.append(f"  • {issue_type}: {count}个")
            lines.append("")
        
        if preview_data['sample_issues']:
            lines.append("示例问题（前{}个）:".format(len(preview_data['sample_issues'])))
            for i, sample in enumerate(preview_data['sample_issues'], 1):
                status = "可修复" if sample['can_fix'] else "需跳过"
                lines.append(f"  {i}. {sample['type']} - {sample['file']} ({status})")
                lines.append(f"     描述: {sample['message']}")
            lines.append("")
        
        lines.append("确认执行修复吗？系统会自动备份原始文件。")
        lines.append("=" * 60)
        
        preview_msg = "\n".join(lines)
        
        # 显示预览并确认
        if not messagebox.askyesno("批量修复预览", preview_msg):
            return
        
        # 执行实际修复
        try:
            # 启动修复会话
            session_id = self.health_fixer.start_fix_session()
            
            # 修复该文件中的所有同类问题
            results = self.health_fixer.fix_issues_in_file(
                issue.file_path, 
                issue_types=[issue.issue_type]
            )
            
            # 结束会话并获取回执
            receipt = self.health_fixer.end_fix_session()
            
            # 统计结果
            success_count = sum(1 for r in results if r.result.value == "success")
            total_count = len(results)
            
            if total_count == 0:
                messagebox.showinfo("无需修复", "该文件中没有发现同类问题")
            else:
                # 显示修复结果（包含回执信息）
                result_msg = f"批量修复完成:\n\n"
                result_msg += f"会话ID: {receipt.session_id}\n"
                result_msg += f"处理结果: 尝试{total_count}个, 成功{success_count}个, 失败{total_count - success_count}个\n"
                result_msg += f"涉及文件: {preview_data['file_count']}个\n"
                
                messagebox.showinfo("批量修复完成", result_msg)
                # 刷新检查结果
                self.run_health_check()
        
        except Exception as e:
            messagebox.showerror("批量修复异常", f"批量修复过程中发生错误:\n{e}")
    
    def show_manual_fix_guidance(self):
        """显示人工修复指导"""
        if not self.current_selected_issue:
            messagebox.showwarning("无选中问题", "请先选择一个要手动处理的问题")
            return
        
        issue = self.current_selected_issue
        
        # 获取人工修复指导
        try:
            guidance = self.health_fixer.get_manual_fix_guidance(issue)
        except Exception as e:
            messagebox.showerror("获取指导失败", f"无法获取人工修复指导:\n{e}")
            return
        
        # 构建指导消息
        lines = []
        lines.append("=" * 60)
        lines.append("人工修复指导")
        lines.append("=" * 60)
        lines.append(f"问题类型: {guidance['issue_type']}")
        lines.append(f"相关文件: {guidance['file_name'] or '无'}")
        lines.append(f"问题描述: {guidance['message']}")
        lines.append(f"修复建议: {guidance['suggestion']}")
        lines.append("")
        lines.append("为什么不能自动修复:")
        lines.append(f"  {guidance.get('reason', '需要人工确认')}")
        lines.append("")
        lines.append("手动修复步骤:")
        for step in guidance.get('manual_steps', []):
            lines.append(f"  {step}")
        lines.append("")
        
        # 添加操作选项
        lines.append("操作选项:")
        lines.append("  1. 跳转到图片（如果可用）")
        lines.append("  2. 打开标签文件")
        lines.append("  3. 忽略此问题")
        
        message = "\n".join(lines)
        
        # 显示对话框
        import tkinter.simpledialog as sd
        class GuidanceDialog(sd.Dialog):
            def __init__(self, parent, title, message, guidance, on_jump_callback=None):
                self.message = message
                self.guidance = guidance
                self.on_jump_callback = on_jump_callback
                super().__init__(parent, title)
            
            def body(self, master):
                text = tk.Text(master, wrap="word", width=80, height=20)
                text.insert("1.0", self.message)
                text.config(state="disabled")
                text.pack(fill="both", expand=True, padx=10, pady=10)
                return text
            
            def buttonbox(self):
                box = tk.Frame(self)
                
                # 跳转到图片按钮
                if self.guidance.get('jump_target') and self.on_jump_callback:
                    jump_btn = tk.Button(
                        box,
                        text="跳转到图片",
                        command=self.jump_to_image,
                        bg="#3b82f6",
                        fg="white",
                        padx=12,
                        pady=6
                    )
                    jump_btn.pack(side="left", padx=5)
                
                # 打开标签文件按钮
                if self.guidance.get('file_path'):
                    open_btn = tk.Button(
                        box,
                        text="打开标签文件",
                        command=self.open_label_file,
                        bg="#10b981",
                        fg="white",
                        padx=12,
                        pady=6
                    )
                    open_btn.pack(side="left", padx=5)
                
                # 忽略按钮
                ignore_btn = tk.Button(
                    box,
                    text="忽略",
                    command=self.cancel,
                    bg="#6b7280",
                    fg="white",
                    padx=12,
                    pady=6
                )
                ignore_btn.pack(side="left", padx=5)
                
                # 关闭按钮
                close_btn = tk.Button(
                    box,
                    text="关闭",
                    command=self.ok,
                    bg="#ef4444",
                    fg="white",
                    padx=12,
                    pady=6
                )
                close_btn.pack(side="left", padx=5)
                
                box.pack()
            
            def jump_to_image(self):
                if self.on_jump_callback and self.guidance.get('file_name'):
                    try:
                        self.on_jump_callback(self.guidance['file_name'])
                    except Exception as e:
                        messagebox.showerror("跳转失败", f"无法跳转到图片:\n{e}")
            
            def open_label_file(self):
                file_path = self.guidance.get('file_path')
                if file_path and os.path.exists(file_path):
                    try:
                        import subprocess
                        if os.name == 'nt':  # Windows
                            os.startfile(file_path)
                        elif os.name == 'posix':  # macOS/Linux
                            subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', file_path))
                        else:
                            messagebox.showinfo("打开文件", f"文件路径:\n{file_path}")
                    except Exception as e:
                        messagebox.showinfo("打开文件", f"文件路径:\n{file_path}\n\n错误: {e}")
                else:
                    messagebox.showwarning("文件不存在", f"无法找到文件:\n{file_path}")
        
        # 显示对话框
        import sys
        dialog = GuidanceDialog(
            self,
            "人工修复指导",
            message,
            guidance,
            on_jump_callback=self.on_jump_to_image if guidance.get('file_name') else None
        )
    
    def show_fix_dialog(self):
        """显示快速修复选项对话框（带预览）"""
        if not self.current_result:
            messagebox.showwarning("无检查结果", "请先运行健康检查")
            return
        
        # 生成修复预览
        try:
            preview_data = self.health_fixer.preview_fix_all_fixable_issues(
                issue_types=None  # 所有可自动修复的类型
            )
        except Exception as e:
            messagebox.showerror("预览失败", f"无法生成修复预览:\n{e}")
            return
        
        # 检查是否有可修复的问题
        if preview_data["fixable_issues"] == 0:
            messagebox.showinfo("无需修复", "当前没有可自动修复的问题")
            return
        
        # 构建预览消息
        lines = []
        lines.append("=" * 60)
        lines.append("批量快速修复预览")
        lines.append("=" * 60)
        lines.append(f"本次准备修复 {preview_data['fixable_issues']} 个问题")
        lines.append(f"涉及 {preview_data['file_count']} 个文件")
        lines.append(f"将被跳过 {preview_data['unfixable_issues']} 个问题（不支持自动修复）")
        lines.append("")
        
        if preview_data['fixable_by_type']:
            lines.append("可修复的问题类型:")
            for issue_type, count in preview_data['fixable_by_type'].items():
                lines.append(f"  • {issue_type}: {count}个")
            lines.append("")
        
        if preview_data['unfixable_by_type']:
            lines.append("将被跳过的问题类型:")
            for issue_type, count in preview_data['unfixable_by_type'].items():
                lines.append(f"  • {issue_type}: {count}个")
            lines.append("")
        
        if preview_data['file_names']:
            lines.append(f"涉及的主要文件（前{len(preview_data['file_names'])}个）:")
            for i, file_name in enumerate(preview_data['file_names'], 1):
                lines.append(f"  {i}. {file_name}")
            if preview_data['file_count'] > len(preview_data['file_names']):
                lines.append(f"  还有 {preview_data['file_count'] - len(preview_data['file_names'])} 个文件...")
            lines.append("")
        
        if preview_data['sample_issues']:
            lines.append("示例问题（前{}个）:".format(len(preview_data['sample_issues'])))
            for i, sample in enumerate(preview_data['sample_issues'], 1):
                status = "可修复" if sample['can_fix'] else "需跳过"
                lines.append(f"  {i}. {sample['type']} - {sample['file']} ({status})")
                lines.append(f"     描述: {sample['message']}")
            lines.append("")
        
        lines.append("确认执行批量修复吗？系统会自动备份原始文件。")
        lines.append("=" * 60)
        
        preview_msg = "\n".join(lines)
        
        # 显示预览并确认
        if not messagebox.askyesno("批量快速修复预览", preview_msg):
            return
        
        # 执行实际修复
        try:
            # 启动修复会话
            session_id = self.health_fixer.start_fix_session()
            
            # 执行批量修复（复用原有逻辑）
            success_count = 0
            total_count = preview_data["fixable_issues"]
            
            # 获取所有可自动修复的问题
            auto_fixable_types = [
                IssueType.EMPTY_LABEL,
                IssueType.DUPLICATE_BOUNDING_BOX,
                IssueType.INVALID_BOUNDING_BOX,
                IssueType.BOUNDING_BOX_OUT_OF_BOUNDS
            ]
            
            fixable_issues = []
            for issue in self.current_result.issues:
                can_fix, _ = self.health_fixer.can_fix_issue(issue)
                if can_fix:
                    fixable_issues.append(issue)
            
            for issue in fixable_issues:
                result = self.health_fixer.fix_single_issue(issue)
                if result.result.value == "success":
                    success_count += 1
            
            # 结束会话并获取回执
            receipt = self.health_fixer.end_fix_session()
            
            # 显示修复结果
            result_msg = f"批量快速修复完成:\n\n"
            result_msg += f"会话ID: {receipt.session_id}\n"
            result_msg += f"处理结果: 尝试{total_count}个, 成功{success_count}个, 失败{total_count - success_count}个\n"
            result_msg += f"涉及文件: {preview_data['file_count']}个\n"
            
            messagebox.showinfo("批量修复完成", result_msg)
            
            # 刷新检查结果
            self.run_health_check()
        
        except Exception as e:
            messagebox.showerror("批量修复失败", f"批量修复过程中发生错误:\n{e}")
    
    def show_fix_history(self):
        """显示修复历史窗口"""
        # 获取最近修复回执
        recent_receipts = self.health_fixer.get_recent_receipts(limit=20)
        
        if not recent_receipts:
            messagebox.showinfo("无修复历史", "暂无修复历史记录")
            return
        
        # 创建历史窗口
        history_window = tk.Toplevel(self)
        history_window.title("修复历史记录")
        history_window.geometry("1000x600")
        history_window.configure(bg=self.bg_main)
        history_window.transient(self)
        history_window.grab_set()
        
        # 标题栏
        title_frame = tk.Frame(history_window, bg=self.bg_main)
        title_frame.pack(fill="x", padx=14, pady=14)
        
        tk.Label(
            title_frame,
            text="📜 修复历史记录",
            bg=self.bg_main,
            fg=self.text_main,
            font=("Microsoft YaHei", 16, "bold")
        ).pack(side="left")
        
        # 操作按钮区域
        button_frame = tk.Frame(title_frame, bg=self.bg_main)
        button_frame.pack(side="right")
        
        tk.Button(
            button_frame,
            text="刷新",
            command=lambda: self._refresh_history_window(history_window),
            bg="#3b82f6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=4,
            relief="flat"
        ).pack(side="left", padx=2)
        
        tk.Button(
            button_frame,
            text="关闭",
            command=history_window.destroy,
            bg=self.border,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=4,
            relief="flat"
        ).pack(side="left", padx=2)
        
        # 主内容区域
        main_frame = tk.Frame(history_window, bg=self.bg_main)
        main_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        
        # 创建表格框架
        table_frame = tk.Frame(main_frame, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        table_frame.pack(fill="both", expand=True)
        
        # 创建表格
        columns = ("时间", "修复类型", "尝试数", "成功数", "失败数", "修改文件数", "会话ID")
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        # 设置列标题
        tree.heading("时间", text="时间")
        tree.heading("修复类型", text="修复类型")
        tree.heading("尝试数", text="尝试数")
        tree.heading("成功数", text="成功数")
        tree.heading("失败数", text="失败数")
        tree.heading("修改文件数", text="修改文件数")
        tree.heading("会话ID", text="会话ID")
        
        # 设置列宽度
        tree.column("时间", width=150, anchor="center")
        tree.column("修复类型", width=200, anchor="w")
        tree.column("尝试数", width=80, anchor="center")
        tree.column("成功数", width=80, anchor="center")
        tree.column("失败数", width=80, anchor="center")
        tree.column("修改文件数", width=100, anchor="center")
        tree.column("会话ID", width=120, anchor="center")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        
        # 填充数据
        for receipt in recent_receipts:
            # 生成修复类型描述
            issue_types = receipt.summary.get('issue_types_handled', [])
            if issue_types:
                fix_type_desc = ", ".join(issue_types[:3])  # 最多显示3种类型
                if len(issue_types) > 3:
                    fix_type_desc += f"等{len(issue_types)}种"
            else:
                fix_type_desc = "无"
            
            # 添加行
            tree.insert("", "end", values=(
                receipt.start_time,
                fix_type_desc,
                receipt.summary['total_attempted'],
                receipt.summary['success'],
                receipt.summary['failed'],
                receipt.summary['modified_files_count'],
                receipt.session_id
            ))
        
        # 详情区域
        detail_frame = tk.Frame(main_frame, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        detail_frame.pack(fill="both", expand=True, pady=(8, 0))
        
        detail_label = tk.Label(
            detail_frame,
            text="修复记录详情",
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 11, "bold")
        )
        detail_label.pack(anchor="w", padx=10, pady=8)
        
        detail_text = tk.Text(
            detail_frame,
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            height=8,
            wrap="word",
            relief="flat",
            padx=8,
            pady=8
        )
        detail_text.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        detail_text.config(state="disabled")
        
        # 操作按钮区域
        detail_button_frame = tk.Frame(detail_frame, bg=self.bg_card)
        detail_button_frame.pack(fill="x", padx=4, pady=(0, 4))
        
        tk.Button(
            detail_button_frame,
            text="查看详细报告",
            command=lambda: self._show_receipt_detail(tree, detail_text),
            bg="#10b981",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat"
        ).pack(side="left", padx=2)
        
        tk.Button(
            detail_button_frame,
            text="查看修复差异",
            command=lambda: self._show_fix_diff(tree),
            bg="#8b5cf6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat"
        ).pack(side="left", padx=2)
        
        tk.Button(
            detail_button_frame,
            text="导出报告",
            command=lambda: self._export_receipt_report(tree),
            bg="#3b82f6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat"
        ).pack(side="left", padx=2)
        
        # 绑定选择事件
        tree.bind("<<TreeviewSelect>>", lambda e: self._on_history_selected(tree, detail_text))
        
        # 默认显示第一条记录的详情
        if recent_receipts:
            tree.selection_set(tree.get_children()[0])
            self._on_history_selected(tree, detail_text)
    
    def _refresh_history_window(self, history_window):
        """刷新历史窗口"""
        history_window.destroy()
        self.show_fix_history()
    
    def _on_history_selected(self, tree, detail_text):
        """处理历史记录选择事件"""
        selection = tree.selection()
        if not selection:
            return
        
        # 获取选中的会话ID
        item = selection[0]
        values = tree.item(item, "values")
        session_id = values[6]  # 会话ID在第七列
        
        # 获取回执详情
        receipt = self.health_fixer.get_receipt_by_id(session_id)
        if not receipt:
            detail_text.config(state="normal")
            detail_text.delete("1.0", "end")
            detail_text.insert("1.0", "无法找到该修复记录")
            detail_text.config(state="disabled")
            return
        
        # 显示回执文本
        detail_text.config(state="normal")
        detail_text.delete("1.0", "end")
        detail_text.insert("1.0", receipt.get_receipt_text())
        detail_text.config(state="disabled")
    
    def _show_receipt_detail(self, tree, detail_text):
        """显示选中回执的详细报告"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("无选中记录", "请先选择一条修复记录")
            return
        
        item = selection[0]
        values = tree.item(item, "values")
        session_id = values[6]
        
        receipt = self.health_fixer.get_receipt_by_id(session_id)
        if not receipt:
            messagebox.showerror("错误", "无法找到该修复记录")
            return
        
        # 创建详细报告窗口
        detail_window = tk.Toplevel(self)
        detail_window.title(f"详细修复报告 - {session_id}")
        detail_window.geometry("900x700")
        detail_window.configure(bg=self.bg_main)
        detail_window.transient(self)
        
        # 标题
        title_frame = tk.Frame(detail_window, bg=self.bg_main)
        title_frame.pack(fill="x", padx=14, pady=14)
        
        tk.Label(
            title_frame,
            text="📋 详细修复报告",
            bg=self.bg_main,
            fg=self.text_main,
            font=("Microsoft YaHei", 16, "bold")
        ).pack(side="left")
        
        # 关闭按钮
        tk.Button(
            title_frame,
            text="关闭",
            command=detail_window.destroy,
            bg=self.border,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat"
        ).pack(side="right")
        
        # 报告内容
        report_frame = tk.Frame(detail_window, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        report_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        
        # 使用ScrolledText以便滚动
        try:
            from tkinter.scrolledtext import ScrolledText
            report_text = ScrolledText(
                report_frame,
                bg=self.bg_card,
                fg=self.text_main,
                font=("Courier New", 9),
                wrap="word",
                relief="flat"
            )
        except ImportError:
            # 回退方案
            report_text = tk.Text(
                report_frame,
                bg=self.bg_card,
                fg=self.text_main,
                font=("Courier New", 9),
                wrap="word",
                relief="flat"
            )
            scrollbar = tk.Scrollbar(report_frame, command=report_text.yview)
            report_text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
        
        report_text.pack(fill="both", expand=True, padx=4, pady=4)
        report_text.insert("1.0", receipt.get_detailed_report())
        report_text.config(state="disabled")
        
        # 操作按钮
        button_frame = tk.Frame(report_frame, bg=self.bg_card)
        button_frame.pack(fill="x", padx=4, pady=(0, 4))
        
        tk.Button(
            button_frame,
            text="复制报告",
            command=lambda: self._copy_report_to_clipboard(report_text),
            bg="#f59e0b",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat"
        ).pack(side="left", padx=2)
        
        tk.Button(
            button_frame,
            text="导出为文本文件",
            command=lambda: self._export_report_to_file(receipt),
            bg="#10b981",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat"
        ).pack(side="left", padx=2)
    
    def _export_receipt_report(self, tree):
        """导出选中回执的报告"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("无选中记录", "请先选择一条修复记录")
            return
        
        item = selection[0]
        values = tree.item(item, "values")
        session_id = values[6]
        
        receipt = self.health_fixer.get_receipt_by_id(session_id)
        if not receipt:
            messagebox.showerror("错误", "无法找到该修复记录")
            return
        
        self._export_report_to_file(receipt)
    
    def _export_report_to_file(self, receipt):
        """导出报告到文件"""
        file_path = filedialog.asksaveasfilename(
            title="导出修复报告",
            defaultextension=".txt",
            filetypes=[
                ("文本文件", "*.txt"),
                ("JSON文件", "*.json"),
                ("所有文件", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            if file_path.lower().endswith('.json'):
                import json
                # 构建JSON结构
                report_data = {
                    "session_id": receipt.session_id,
                    "start_time": receipt.start_time,
                    "end_time": receipt.end_time,
                    "summary": receipt.summary,
                    "operations_count": len(receipt.operations)
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
                format_name = "JSON"
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(receipt.get_detailed_report())
                format_name = "文本"
            
            messagebox.showinfo("导出成功", f"修复报告已导出为{format_name}格式:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("导出失败", f"导出报告时发生错误:\n{e}")
    
    def _copy_report_to_clipboard(self, report_text):
        """复制报告到剪贴板"""
        try:
            self.clipboard_clear()
            self.clipboard_append(report_text.get("1.0", "end-1c"))
            messagebox.showinfo("复制成功", "报告已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("复制失败", f"复制到剪贴板失败:\n{e}")

    def _build_image_summary_panel(self, parent):
        """构建按图片汇总面板"""
        # 面板标题
        title_frame = tk.Frame(parent, bg=self.bg_card, height=48)
        title_frame.pack(fill="x", padx=12, pady=12)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="🖼️ 按图片汇总问题统计",
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 13, "bold")
        ).pack(side="left")
        
        # 工具栏（排序和筛选）
        toolbar_frame = tk.Frame(title_frame, bg=self.bg_card)
        toolbar_frame.pack(side="right")
        
        tk.Label(
            toolbar_frame,
            text="排序:",
            bg=self.bg_card,
            fg=self.text_sub,
            font=("Microsoft YaHei", 9)
        ).pack(side="left", padx=(0, 4))
        
        # 排序字段选择
        self.image_sort_var = tk.StringVar(value="total_desc")
        sort_options = [
            ("问题总数 ↓", "total_desc"),
            ("问题总数 ↑", "total_asc"),
            ("错误数 ↓", "errors_desc"),
            ("错误数 ↑", "errors_asc"),
            ("可自动修复数 ↓", "auto_fixable_desc"),
            ("可自动修复数 ↑", "auto_fixable_asc"),
            ("图片名 A-Z", "name_asc"),
            ("图片名 Z-A", "name_desc")
        ]
        
        sort_menu = tk.OptionMenu(
            toolbar_frame,
            self.image_sort_var,
            *[opt[0] for opt in sort_options],
            command=self._refresh_image_summary
        )
        sort_menu.config(
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            relief="flat",
            cursor="hand2"
        )
        sort_menu["menu"].config(
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 9)
        )
        sort_menu.pack(side="left", padx=2)
        
        # 刷新按钮
        refresh_btn = tk.Button(
            toolbar_frame,
            text="刷新",
            command=self._refresh_image_summary,
            bg="#3b82f6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=8,
            pady=2,
            relief="flat",
            cursor="hand2"
        )
        refresh_btn.pack(side="left", padx=2)
        
        # 图片汇总表格容器
        table_container = tk.Frame(parent, bg=self.bg_card)
        table_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # 创建Treeview
        columns = ("image_name", "total", "errors", "warnings", "infos", "auto_fixable", "manual_fix")
        self.image_tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            height=15,
            selectmode="browse"
        )
        
        # 设置列标题
        self.image_tree.heading("image_name", text="图片名", anchor="w")
        self.image_tree.heading("total", text="问题总数", anchor="center")
        self.image_tree.heading("errors", text="错误", anchor="center")
        self.image_tree.heading("warnings", text="警告", anchor="center")
        self.image_tree.heading("infos", text="信息", anchor="center")
        self.image_tree.heading("auto_fixable", text="可自动修复", anchor="center")
        self.image_tree.heading("manual_fix", text="需人工处理", anchor="center")
        
        # 设置列宽度
        self.image_tree.column("image_name", width=200, stretch=True)
        self.image_tree.column("total", width=80, stretch=False, anchor="center")
        self.image_tree.column("errors", width=60, stretch=False, anchor="center")
        self.image_tree.column("warnings", width=60, stretch=False, anchor="center")
        self.image_tree.column("infos", width=60, stretch=False, anchor="center")
        self.image_tree.column("auto_fixable", width=100, stretch=False, anchor="center")
        self.image_tree.column("manual_fix", width=100, stretch=False, anchor="center")
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.image_tree.yview)
        self.image_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.image_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # 详情面板
        detail_frame = tk.Frame(parent, bg=self.bg_card, height=120)
        detail_frame.pack(fill="both", expand=False, pady=(10, 0))
        
        tk.Label(
            detail_frame,
            text="图片详情:",
            bg=self.bg_card,
            fg=self.text_main,
            font=("Microsoft YaHei", 10, "bold")
        ).pack(anchor="w", padx=4, pady=4)
        
        self.image_detail_text = tk.Text(
            detail_frame,
            bg="#1e2229",
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            height=6,
            wrap="word",
            relief="flat",
            padx=8,
            pady=8
        )
        self.image_detail_text.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.image_detail_text.config(state="disabled")
        
        # 操作按钮
        button_frame = tk.Frame(detail_frame, bg=self.bg_card)
        button_frame.pack(fill="x", padx=4, pady=(0, 4))
        
        self.jump_to_image_btn = tk.Button(
            button_frame,
            text="跳转到图片",
            command=self._jump_to_selected_image,
            bg="#3b82f6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.jump_to_image_btn.pack(side="left", padx=2)
        
        self.view_image_issues_btn = tk.Button(
            button_frame,
            text="查看该图片所有问题",
            command=self._view_image_issues,
            bg="#10b981",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.view_image_issues_btn.pack(side="left", padx=2)
        
        self.fix_image_issues_btn = tk.Button(
            button_frame,
            text="修复该图片",
            command=self._fix_image_issues,
            bg="#ef4444",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.fix_image_issues_btn.pack(side="left", padx=2)
        
        self.view_fix_diff_btn = tk.Button(
            button_frame,
            text="查看修复差异",
            command=self._view_image_fix_diff,
            bg="#8b5cf6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.view_fix_diff_btn.pack(side="left", padx=2)
        
        self.manual_fix_issues_btn = tk.Button(
            button_frame,
            text="人工处理问题",
            command=self._view_manual_issues,
            bg="#f59e0b",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.manual_fix_issues_btn.pack(side="left", padx=2)
        
        self.fix_report_btn = tk.Button(
            button_frame,
            text="修复报告",
            command=self._view_fix_report,
            bg="#06b6d4",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.fix_report_btn.pack(side="left", padx=2)
        
        self.fix_history_btn = tk.Button(
            button_frame,
            text="修复历史",
            command=self._view_fix_history,
            bg="#8b5cf6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=4,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.fix_history_btn.pack(side="left", padx=2)
        
        # 绑定选择事件
        self.image_tree.bind("<<TreeviewSelect>>", self._on_image_selected)
        
        # 存储图片汇总数据
        self.image_summary_data = []
    
    def _refresh_image_summary(self, *args):
        """刷新图片汇总表格"""
        if not self.current_result:
            return
        
        # 清空现有项
        for item in self.image_tree.get_children():
            self.image_tree.delete(item)
        
        # 获取图片汇总数据
        self.image_summary_data = self.health_manager.get_image_summary_report(self.current_result)
        
        if not self.image_summary_data:
            # 没有数据，显示提示
            self.image_tree.insert("", "end", values=("未发现任何问题", "0", "0", "0", "0", "0", "0"))
            return
        
        # 获取排序设置
        sort_value = self.image_sort_var.get()
        
        # 排序
        if sort_value == "total_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=True)
        elif sort_value == "total_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=False)
        elif sort_value == "errors_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=True)
        elif sort_value == "errors_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=False)
        elif sort_value == "auto_fixable_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=True)
        elif sort_value == "auto_fixable_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=False)
        elif sort_value == "name_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=False)
        elif sort_value == "name_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=True)
        else:
            sorted_data = self.image_summary_data
        
        # 添加项到Treeview
        for item in sorted_data:
            # 设置颜色标签（根据错误数）
            tags = ()
            if item['errors'] > 0:
                tags = ("error",)
            elif item['warnings'] > 0:
                tags = ("warning",)
            elif item['total'] > 0:
                tags = ("info",)
            
            self.image_tree.insert(
                "", "end",
                values=(
                    item['image_name'],
                    item['total'],
                    item['errors'],
                    item['warnings'],
                    item['infos'],
                    item['auto_fixable'],
                    item['manual_fix']
                ),
                tags=tags
            )
        
        # 配置标签样式
        self.image_tree.tag_configure("error", foreground=self.error_color)
        self.image_tree.tag_configure("warning", foreground=self.warning_color)
        self.image_tree.tag_configure("info", foreground=self.info_color)
        
        # 清空详情面板
        self._clear_image_detail_panel()
    
    def _on_image_selected(self, event):
        """处理图片选择事件"""
        selection = self.image_tree.selection()
        if not selection or not self.image_summary_data:
            self._clear_image_detail_panel()
            return
        
        # 获取选中的行索引
        selected_item = selection[0]
        item_index = self.image_tree.index(selected_item)
        
        # 获取排序后的数据（需要重新排序以匹配显示顺序）
        sort_value = self.image_sort_var.get()
        if sort_value == "total_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=True)
        elif sort_value == "total_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=False)
        elif sort_value == "errors_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=True)
        elif sort_value == "errors_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=False)
        elif sort_value == "auto_fixable_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=True)
        elif sort_value == "auto_fixable_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=False)
        elif sort_value == "name_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=False)
        elif sort_value == "name_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=True)
        else:
            sorted_data = self.image_summary_data
        
        if item_index < len(sorted_data):
            item_data = sorted_data[item_index]
            self._update_image_detail_panel(item_data)
    
    def _update_image_detail_panel(self, item_data):
        """更新图片详情面板"""
        # 清空现有内容
        self.image_detail_text.config(state="normal")
        self.image_detail_text.delete("1.0", "end")
        
        # 构建详情文本
        detail_lines = []
        detail_lines.append(f"【图片名】{item_data['image_name']}")
        detail_lines.append("")
        detail_lines.append("【问题统计】")
        detail_lines.append(f"  问题总数: {item_data['total']}")
        detail_lines.append(f"  错误数: {item_data['errors']}")
        detail_lines.append(f"  警告数: {item_data['warnings']}")
        detail_lines.append(f"  信息数: {item_data['infos']}")
        detail_lines.append(f"  可自动修复: {item_data['auto_fixable']}")
        detail_lines.append(f"  需人工处理: {item_data['manual_fix']}")
        detail_lines.append("")
        
        # 获取该图片下的所有问题
        image_stats = self.health_manager.get_issues_by_image(self.current_result)
        if item_data['image_name'] in image_stats:
            issues = image_stats[item_data['image_name']]['issues']
            if issues:
                detail_lines.append(f"【问题列表（共{len(issues)}个）】")
                for i, issue in enumerate(issues[:10], 1):  # 最多显示10个
                    severity_symbol = "❌" if issue.severity == IssueSeverity.ERROR else \
                                     "⚠️" if issue.severity == IssueSeverity.WARNING else "ℹ️"
                    detail_lines.append(f"  {i}. {severity_symbol} {issue.message[:80]}{'...' if len(issue.message) > 80 else ''}")
                if len(issues) > 10:
                    detail_lines.append(f"  还有{len(issues) - 10}个问题未显示...")
                
                # 添加人工处理问题专门列表
                if item_data['manual_fix'] > 0:
                    detail_lines.append("")
                    detail_lines.append(f"【需人工处理的问题（{item_data['manual_fix']}个）】")
                    
                    # 筛选人工处理问题
                    manual_issues = []
                    issue_types = {}
                    
                    for issue in issues:
                        can_fix, _ = self.health_fixer.can_fix_issue(issue)
                        if not can_fix:
                            manual_issues.append(issue)
                            issue_type = issue.issue_type.value
                            if issue_type not in issue_types:
                                issue_types[issue_type] = 0
                            issue_types[issue_type] += 1
                    
                    # 显示问题类型概览
                    if issue_types:
                        type_lines = []
                        for issue_type, count in issue_types.items():
                            type_lines.append(f"  • {issue_type}: {count}个")
                        detail_lines.append("  " + "，".join(type_lines))
                    
                    # 显示前5个人工处理问题详情
                    for i, issue in enumerate(manual_issues[:5], 1):
                        severity_symbol = "❌" if issue.severity == IssueSeverity.ERROR else \
                                         "⚠️" if issue.severity == IssueSeverity.WARNING else "ℹ️"
                        detail_lines.append(f"  {i}. {severity_symbol} {issue.message[:70]}{'...' if len(issue.message) > 70 else ''}")
                    if len(manual_issues) > 5:
                        detail_lines.append(f"  还有{len(manual_issues) - 5}个人工处理问题未显示...")
        
        # 插入文本
        for line in detail_lines:
            self.image_detail_text.insert("end", line + "\n")
        
        # 设置只读
        self.image_detail_text.config(state="disabled")
        
        # 更新按钮状态
        if self.on_jump_to_image:
            # 尝试查找对应的图片文件
            image_name = item_data['image_name']
            # 检查是否有对应的图片文件
            if self.context.image_dir:
                for ext in self.health_manager._valid_ext:
                    possible_file = os.path.join(self.context.image_dir, image_name + ext)
                    if os.path.exists(possible_file):
                        self.jump_to_image_btn.config(state="normal")
                        break
                else:
                    self.jump_to_image_btn.config(state="disabled")
            else:
                self.jump_to_image_btn.config(state="disabled")
        else:
            self.jump_to_image_btn.config(state="disabled")
        
        # 查看问题按钮始终可用（如果有问题）
        if item_data['total'] > 0:
            self.view_image_issues_btn.config(state="normal")
        else:
            self.view_image_issues_btn.config(state="disabled")
        
        # 修复按钮只在有可自动修复问题时可用
        if item_data['auto_fixable'] > 0:
            self.fix_image_issues_btn.config(state="normal")
        else:
            self.fix_image_issues_btn.config(state="disabled")
        
        # 查看修复差异按钮只在有修复记录时可用
        image_name = item_data['image_name']
        has_fix_operations = False
        try:
            # 检查是否有修复记录
            operations = self.health_fixer.get_image_fix_operations(image_name)
            has_fix_operations = len(operations) > 0
        except Exception:
            has_fix_operations = False
        
        if has_fix_operations:
            self.view_fix_diff_btn.config(state="normal")
            self.fix_report_btn.config(state="normal")
            self.fix_history_btn.config(state="normal")
        else:
            self.view_fix_diff_btn.config(state="disabled")
            self.fix_report_btn.config(state="disabled")
            self.fix_history_btn.config(state="disabled")
        
        # 人工处理按钮只在有需人工处理问题时可用
        if item_data['manual_fix'] > 0:
            self.manual_fix_issues_btn.config(state="normal")
        else:
            self.manual_fix_issues_btn.config(state="disabled")
    
    def _clear_image_detail_panel(self):
        """清空图片详情面板"""
        self.image_detail_text.config(state="normal")
        self.image_detail_text.delete("1.0", "end")
        self.image_detail_text.insert("1.0", "请选择一个图片查看详情...")
        self.image_detail_text.config(state="disabled")
        self.jump_to_image_btn.config(state="disabled")
        self.view_image_issues_btn.config(state="disabled")
        self.fix_image_issues_btn.config(state="disabled")
        self.view_fix_diff_btn.config(state="disabled")
        self.manual_fix_issues_btn.config(state="disabled")
        self.fix_report_btn.config(state="disabled")
        self.fix_history_btn.config(state="disabled")
    
    def _jump_to_selected_image(self):
        """跳转到选中的图片"""
        selection = self.image_tree.selection()
        if not selection or not self.image_summary_data or not self.on_jump_to_image:
            return
        
        # 获取选中的行索引
        selected_item = selection[0]
        item_index = self.image_tree.index(selected_item)
        
        # 获取排序后的数据
        sort_value = self.image_sort_var.get()
        if sort_value == "total_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=True)
        elif sort_value == "total_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=False)
        elif sort_value == "errors_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=True)
        elif sort_value == "errors_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=False)
        elif sort_value == "auto_fixable_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=True)
        elif sort_value == "auto_fixable_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=False)
        elif sort_value == "name_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=False)
        elif sort_value == "name_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=True)
        else:
            sorted_data = self.image_summary_data
        
        if item_index < len(sorted_data):
            image_name = sorted_data[item_index]['image_name']
            # 尝试查找对应的图片文件
            if self.context.image_dir:
                for ext in self.health_manager._valid_ext:
                    possible_file = image_name + ext
                    if os.path.exists(os.path.join(self.context.image_dir, possible_file)):
                        # 调用回调函数
                        try:
                            self.on_jump_to_image(possible_file)
                            return
                        except Exception as e:
                            messagebox.showerror("跳转失败", f"无法跳转到图片:\n{e}")
                            return
                # 如果没找到，尝试直接使用图片名
                try:
                    self.on_jump_to_image(image_name)
                except Exception as e:
                    messagebox.showerror("跳转失败", f"无法跳转到图片:\n{e}")
    
    def _view_image_issues(self):
        """查看选中图片的所有问题（切换到问题列表并筛选）"""
        selection = self.image_tree.selection()
        if not selection or not self.image_summary_data:
            return
        
        # 获取选中的行索引
        selected_item = selection[0]
        item_index = self.image_tree.index(selected_item)
        
        # 获取排序后的数据
        sort_value = self.image_sort_var.get()
        if sort_value == "total_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=True)
        elif sort_value == "total_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=False)
        elif sort_value == "errors_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=True)
        elif sort_value == "errors_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=False)
        elif sort_value == "auto_fixable_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=True)
        elif sort_value == "auto_fixable_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=False)
        elif sort_value == "name_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=False)
        elif sort_value == "name_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=True)
        else:
            sorted_data = self.image_summary_data
        
        if item_index < len(sorted_data):
            image_name = sorted_data[item_index]['image_name']
            # 切换到问题列表标签页
            if hasattr(self, 'right_notebook'):
                self.right_notebook.select(0)  # 切换到第一个标签页（问题列表）
            
            # 可选：在问题列表中筛选该图片的问题
            # 由于筛选功能需要额外实现，暂时只显示提示
            messagebox.showinfo(
                "查看图片问题",
                f"已切换到问题列表，请手动筛选图片 '{image_name}' 的问题。\n\n"
                f"提示：在问题列表中按文件名排序可快速定位。"
            )
    
    def _view_manual_issues(self):
        """查看选中图片的需人工处理问题"""
        selection = self.image_tree.selection()
        if not selection or not self.image_summary_data:
            messagebox.showwarning("无选中图片", "请先选择一个图片")
            return
        
        # 获取选中的行索引
        selected_item = selection[0]
        item_index = self.image_tree.index(selected_item)
        
        # 获取排序后的数据
        sort_value = self.image_sort_var.get()
        if sort_value == "total_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=True)
        elif sort_value == "total_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=False)
        elif sort_value == "errors_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=True)
        elif sort_value == "errors_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=False)
        elif sort_value == "auto_fixable_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=True)
        elif sort_value == "auto_fixable_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=False)
        elif sort_value == "name_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=False)
        elif sort_value == "name_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=True)
        else:
            sorted_data = self.image_summary_data
        
        if item_index >= len(sorted_data):
            messagebox.showerror("错误", "无法获取图片信息")
            return
        
        image_name = sorted_data[item_index]['image_name']
        
        # 获取该图片的所有问题
        image_stats = self.health_manager.get_issues_by_image(self.current_result)
        if image_name not in image_stats:
            messagebox.showinfo("无问题", f"图片 '{image_name}' 没有任何问题")
            return
        
        issues = image_stats[image_name]['issues']
        
        # 筛选需要人工处理的问题（不可自动修复的问题）
        manual_issues = []
        
        for issue in issues:
            can_fix, _ = self.health_fixer.can_fix_issue(issue)
            if not can_fix:
                manual_issues.append(issue)
        
        if not manual_issues:
            messagebox.showinfo(
                "无需人工处理",
                f"图片 '{image_name}' 没有需要人工处理的问题。\n\n"
                f"所有问题都可以自动修复或已修复。"
            )
            return
        
        # 切换到问题列表标签页
        if hasattr(self, 'right_notebook'):
            self.right_notebook.select(0)  # 切换到第一个标签页（问题列表）
        
        # 设置视图模式为"manual_fix"，只显示需人工处理的问题
        self.view_mode = "manual_fix"
        
        # 设置聚焦图片，便于在问题列表中筛选
        self.focused_image_for_manual_fix = image_name
        
        # 刷新问题列表，应用筛选
        self._refresh_issues_list()
        
        # 统计问题类型
        issue_types = {}
        for issue in manual_issues:
            issue_type = issue.issue_type.value
            if issue_type not in issue_types:
                issue_types[issue_type] = 0
            issue_types[issue_type] += 1
        
        # 尝试在问题列表中定位第一个需人工处理的问题
        if hasattr(self, 'issues_tree'):
            # 查找第一个属于该图片且需要人工处理的问题
            found_item = None
            for child in self.issues_tree.get_children():
                item_values = self.issues_tree.item(child)
                # 问题项的值可能包含文件名，这里简化处理
                # 实际应该通过issue对象判断，但这里先尝试匹配文件名
                if 'values' in item_values and len(item_values['values']) > 1:
                    file_name = item_values['values'][1]  # 假设第二列是文件名
                    if image_name in file_name:
                        found_item = child
                        break
            
            if found_item:
                # 选中并滚动到该项
                self.issues_tree.selection_set(found_item)
                self.issues_tree.see(found_item)
                # 更新详情面板
                self._on_issue_selected(None)
        
        # 构建提示信息
        type_summary = "\n".join([f"  • {issue_type}: {count}个" for issue_type, count in issue_types.items()])
        
        messagebox.showinfo(
            "人工处理问题",
            f"图片 '{image_name}' 共有 {len(manual_issues)} 个需要人工处理的问题。\n\n"
            f"【问题类型统计】\n{type_summary}\n\n"
            f"已切换到问题列表，并筛选出需人工处理的问题。\n"
            f"第一个问题已自动选中，请检查并手动处理。"
        )
    
    def _fix_image_issues(self):
        """修复选中图片的所有可自动修复问题"""
        selection = self.image_tree.selection()
        if not selection or not self.image_summary_data:
            messagebox.showwarning("无选中图片", "请先选择一个图片")
            return
        
        # 获取选中的行索引
        selected_item = selection[0]
        item_index = self.image_tree.index(selected_item)
        
        # 获取排序后的数据
        sort_value = self.image_sort_var.get()
        if sort_value == "total_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=True)
        elif sort_value == "total_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=False)
        elif sort_value == "errors_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=True)
        elif sort_value == "errors_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=False)
        elif sort_value == "auto_fixable_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=True)
        elif sort_value == "auto_fixable_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=False)
        elif sort_value == "name_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=False)
        elif sort_value == "name_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=True)
        else:
            sorted_data = self.image_summary_data
        
        if item_index >= len(sorted_data):
            messagebox.showerror("错误", "无法获取图片信息")
            return
        
        image_name = sorted_data[item_index]['image_name']
        
        # 预览修复
        preview_data = self.health_fixer.preview_fix_issues_by_image(image_name)
        
        if preview_data['fixable_issues'] == 0:
            messagebox.showinfo(
                "无可修复问题",
                f"图片 '{image_name}' 没有可自动修复的问题。\n\n"
                f"总问题数: {preview_data['total_issues']}\n"
                f"可自动修复: {preview_data['fixable_issues']}\n"
                f"需人工处理: {preview_data['unfixable_issues']}"
            )
            return
        
        # 构建预览消息
        preview_lines = []
        preview_lines.append(f"【图片】{image_name}")
        preview_lines.append("")
        preview_lines.append("【问题统计】")
        preview_lines.append(f"  总问题数: {preview_data['total_issues']}")
        preview_lines.append(f"  可自动修复: {preview_data['fixable_issues']}")
        preview_lines.append(f"  需人工处理: {preview_data['unfixable_issues']}")
        preview_lines.append("")
        
        # 可修复问题类型统计
        if preview_data['fixable_by_type']:
            preview_lines.append("【可修复的问题类型】")
            for issue_type, count in preview_data['fixable_by_type'].items():
                preview_lines.append(f"  • {issue_type}: {count}个")
            preview_lines.append("")
        
        # 不可修复问题类型统计
        if preview_data['unfixable_by_type']:
            preview_lines.append("【需人工处理的问题类型】")
            for issue_type, count in preview_data['unfixable_by_type'].items():
                preview_lines.append(f"  • {issue_type}: {count}个")
            preview_lines.append("")
        
        # 示例问题
        if preview_data['fixable_issues_list']:
            preview_lines.append("【将被修复的问题示例】")
            for i, issue in enumerate(preview_data['fixable_issues_list'][:3], 1):
                severity_symbol = "❌" if issue.severity == IssueSeverity.ERROR else \
                                 "⚠️" if issue.severity == IssueSeverity.WARNING else "ℹ️"
                preview_lines.append(f"  {i}. {severity_symbol} {issue.message[:60]}{'...' if len(issue.message) > 60 else ''}")
            if len(preview_data['fixable_issues_list']) > 3:
                preview_lines.append(f"  还有{len(preview_data['fixable_issues_list']) - 3}个问题...")
            preview_lines.append("")
        
        if preview_data['unfixable_issues_list']:
            preview_lines.append("【将被跳过的问题（需人工处理）】")
            for i, issue in enumerate(preview_data['unfixable_issues_list'][:2], 1):
                severity_symbol = "❌" if issue.severity == IssueSeverity.ERROR else \
                                 "⚠️" if issue.severity == IssueSeverity.WARNING else "ℹ️"
                preview_lines.append(f"  {i}. {severity_symbol} {issue.message[:60]}{'...' if len(issue.message) > 60 else ''}")
            if len(preview_data['unfixable_issues_list']) > 2:
                preview_lines.append(f"  还有{len(preview_data['unfixable_issues_list']) - 2}个问题...")
            preview_lines.append("")
        
        preview_lines.append("【安全提示】")
        preview_lines.append("  1. 修复前会自动备份原始文件")
        preview_lines.append("  2. 只修复可自动处理的问题")
        preview_lines.append("  3. 人工处理的问题需要您手动解决")
        preview_lines.append("")
        
        preview_text = "\n".join(preview_lines)
        
        # 显示确认对话框
        confirm = messagebox.askyesno(
            "确认修复",
            f"{preview_text}\n\n是否确认修复该图片的所有可自动修复问题？",
            icon="warning",
            default="no"
        )
        
        if not confirm:
            return
        
        # 开始修复会话
        session_id = self.health_fixer.start_fix_session()
        
        try:
            # 执行修复
            results = self.health_fixer.fix_issues_by_image(image_name, start_session=False)
            
            # 结束修复会话并获取回执
            receipt = self.health_fixer.end_fix_session()
            
            # 显示修复结果
            success_count = sum(1 for op in results if op.result == FixResult.SUCCESS)
            total_count = len(results)
            
            messagebox.showinfo(
                "修复完成",
                f"图片 '{image_name}' 修复完成！\n\n"
                f"修复结果:\n"
                f"  尝试修复: {total_count}个\n"
                f"  成功: {success_count}个\n"
                f"  失败: {total_count - success_count}个\n\n"
                f"修复回执已生成，可在'修复历史'中查看详细报告。"
            )
            
            # 刷新界面
            self.run_health_check()
            
        except Exception as e:
            messagebox.showerror("修复失败", f"修复过程中发生错误:\n{e}")
            # 如果有活动的修复会话，结束它
            if self.health_fixer.current_receipt:
                self.health_fixer.end_fix_session()
    
    def _view_image_fix_diff(self):
        """查看选中图片的修复差异"""
        selection = self.image_tree.selection()
        if not selection or not self.image_summary_data:
            messagebox.showwarning("无选中图片", "请先选择一个图片")
            return
        
        # 获取选中的行索引
        selected_item = selection[0]
        item_index = self.image_tree.index(selected_item)
        
        # 获取排序后的数据
        sort_value = self.image_sort_var.get()
        if sort_value == "total_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=True)
        elif sort_value == "total_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=False)
        elif sort_value == "errors_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=True)
        elif sort_value == "errors_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=False)
        elif sort_value == "auto_fixable_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=True)
        elif sort_value == "auto_fixable_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=False)
        elif sort_value == "name_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=False)
        elif sort_value == "name_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=True)
        else:
            sorted_data = self.image_summary_data
        
        if item_index >= len(sorted_data):
            messagebox.showerror("错误", "无法获取图片信息")
            return
        
        image_name = sorted_data[item_index]['image_name']
        
        # 获取修复差异
        try:
            diff_data = self.health_fixer.get_image_fix_diff(image_name)
            
            if "message" in diff_data and diff_data["message"]:
                messagebox.showinfo("修复差异", diff_data["message"])
                return
            
            # 创建差异查看窗口
            diff_window = tk.Toplevel(self)
            diff_window.title(f"修复差异查看 - {image_name}")
            diff_window.geometry("900x700")
            diff_window.configure(bg=self.bg_main)
            diff_window.transient(self)
            
            # 标题
            title_frame = tk.Frame(diff_window, bg=self.bg_main)
            title_frame.pack(fill="x", padx=14, pady=14)
            
            tk.Label(
                title_frame,
                text=f"🔍 图片修复差异 - {image_name}",
                bg=self.bg_main,
                fg=self.text_main,
                font=("Microsoft YaHei", 16, "bold")
            ).pack(side="left")
            
            # 关闭按钮
            tk.Button(
                title_frame,
                text="关闭",
                command=diff_window.destroy,
                bg=self.border,
                fg=self.text_main,
                font=("Microsoft YaHei", 9),
                padx=12,
                pady=4,
                relief="flat"
            ).pack(side="right")
            
            # 内容容器
            content_frame = tk.Frame(diff_window, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
            content_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
            
            # 使用Text组件显示差异
            diff_text = tk.Text(
                content_frame,
                bg="#1e2229",
                fg=self.text_main,
                font=("Microsoft YaHei", 9),
                wrap="word",
                relief="flat",
                padx=12,
                pady=12
            )
            diff_text.pack(fill="both", expand=True, padx=2, pady=2)
            
            # 获取差异摘要
            diff_summary = self.health_fixer.get_image_fix_diff_summary(image_name)
            diff_text.insert("1.0", diff_summary)
            diff_text.config(state="disabled")
            
            # 滚动条
            scrollbar = tk.Scrollbar(content_frame, command=diff_text.yview)
            diff_text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            
            # 操作按钮框架
            button_frame = tk.Frame(diff_window, bg=self.bg_main)
            button_frame.pack(fill="x", padx=14, pady=(0, 14))
            
            # 导出差异按钮
            def export_diff():
                file_path = filedialog.asksaveasfilename(
                    title="导出修复差异",
                    defaultextension=".txt",
                    filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
                )
                if file_path:
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(diff_summary)
                        messagebox.showinfo("导出成功", f"修复差异已导出到:\n{file_path}")
                    except Exception as e:
                        messagebox.showerror("导出失败", f"导出失败:\n{e}")
            
            tk.Button(
                button_frame,
                text="导出差异报告",
                command=export_diff,
                bg="#3b82f6",
                fg="white",
                font=("Microsoft YaHei", 9),
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2"
            ).pack(side="left", padx=2)
            
            # 查看详细修复回执按钮
            def view_full_receipt():
                if "session_id" in diff_data and diff_data["session_id"]:
                    receipt = self.health_fixer.get_receipt_by_id(diff_data["session_id"])
                    if receipt:
                        # 显示详细回执
                        self._show_receipt_detail(receipt)
                    else:
                        messagebox.showwarning("无详细回执", "无法找到详细的修复回执")
                else:
                    messagebox.showwarning("无会话ID", "该修复记录没有会话ID")
            
            tk.Button(
                button_frame,
                text="查看详细修复回执",
                command=view_full_receipt,
                bg="#10b981",
                fg="white",
                font=("Microsoft YaHei", 9),
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2"
            ).pack(side="left", padx=2)
            
        except Exception as e:
            messagebox.showerror("获取差异失败", f"获取修复差异时发生错误:\n{e}")

    def _view_fix_report(self):
        """查看选中图片的修复报告"""
        selection = self.image_tree.selection()
        if not selection or not self.image_summary_data:
            messagebox.showwarning("无选中图片", "请先选择一个图片")
            return
        
        # 获取选中的行索引
        selected_item = selection[0]
        item_index = self.image_tree.index(selected_item)
        
        # 获取排序后的数据
        sort_value = self.image_sort_var.get()
        if sort_value == "total_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=True)
        elif sort_value == "total_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=False)
        elif sort_value == "errors_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=True)
        elif sort_value == "errors_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=False)
        elif sort_value == "auto_fixable_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=True)
        elif sort_value == "auto_fixable_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=False)
        elif sort_value == "name_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=False)
        elif sort_value == "name_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=True)
        else:
            sorted_data = self.image_summary_data
        
        if item_index >= len(sorted_data):
            messagebox.showerror("错误", "无法获取图片信息")
            return
        
        image_name = sorted_data[item_index]['image_name']
        
        # 获取修复报告
        try:
            report_data = self.health_fixer.get_image_fix_report(image_name)
            
            if "message" in report_data and report_data["message"]:
                messagebox.showinfo("修复报告", report_data["message"])
                return
            
            # 创建报告查看窗口
            report_window = tk.Toplevel(self)
            report_window.title(f"修复报告查看 - {image_name}")
            report_window.geometry("800x600")
            report_window.configure(bg=self.bg_main)
            report_window.transient(self)
            
            # 标题
            title_frame = tk.Frame(report_window, bg=self.bg_main)
            title_frame.pack(fill="x", padx=14, pady=14)
            
            tk.Label(
                title_frame,
                text=f"📋 图片修复报告 - {image_name}",
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
            
            # 内容容器
            content_frame = tk.Frame(report_window, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
            content_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
            
            # 使用Text组件显示报告
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
            
            # 构建报告文本
            lines = []
            lines.append("=" * 60)
            lines.append(f"图片修复报告 - {image_name}")
            lines.append("=" * 60)
            lines.append(f"修复会话: {report_data['session_id']}")
            if report_data['label_file_name']:
                lines.append(f"标签文件: {report_data['label_file_name']}")
            lines.append("")
            
            lines.append("【修复操作统计】")
            lines.append(f"  总操作数: {report_data['total_operations']}")
            lines.append(f"  成功操作: {report_data['successful_operations']}")
            lines.append(f"  失败操作: {report_data['failed_operations']}")
            lines.append(f"  跳过操作: {report_data['skipped_operations']}")
            lines.append("")
            
            lines.append("【修复结果汇总】")
            lines.append(f"  删除标注框: {report_data['deleted_boxes_count']}个")
            lines.append(f"  修正坐标: {report_data['fixed_coordinates_count']}个")
            lines.append(f"  跳过问题: {report_data['skipped_issues_count']}个")
            lines.append("")
            
            if report_data['issue_types']:
                lines.append(f"【涉及问题类型 ({len(report_data['issue_types'])}种)】")
                for issue_type in report_data['issue_types']:
                    lines.append(f"  • {issue_type}")
                lines.append("")
            
            # AI复核预留区域
            lines.append("【AI复核建议 (预留)】")
            lines.append("  此处为AI复核建议预留位置")
            lines.append("  后续可扩展AI自动分析修复效果和提供优化建议")
            lines.append("")
            
            lines.append("=" * 60)
            
            report_text.insert("1.0", "\n".join(lines))
            report_text.config(state="disabled")
            
            # 滚动条
            scrollbar = tk.Scrollbar(content_frame, command=report_text.yview)
            report_text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            
            # 操作按钮框架
            button_frame = tk.Frame(report_window, bg=self.bg_main)
            button_frame.pack(fill="x", padx=14, pady=(0, 14))
            
            # 导出报告按钮
            def export_report():
                file_path = filedialog.asksaveasfilename(
                    title="导出修复报告",
                    defaultextension=".txt",
                    filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
                )
                if file_path:
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write("\n".join(lines))
                        messagebox.showinfo("导出成功", f"修复报告已导出到:\n{file_path}")
                    except Exception as e:
                        messagebox.showerror("导出失败", f"导出失败:\n{e}")
            
            tk.Button(
                button_frame,
                text="导出报告",
                command=export_report,
                bg="#3b82f6",
                fg="white",
                font=("Microsoft YaHei", 9),
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2"
            ).pack(side="left", padx=2)
            
            # 查看详细差异按钮
            def view_diff():
                self._view_image_fix_diff()
                report_window.destroy()
            
            tk.Button(
                button_frame,
                text="查看详细差异",
                command=view_diff,
                bg="#10b981",
                fg="white",
                font=("Microsoft YaHei", 9),
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2"
            ).pack(side="left", padx=2)
            
        except Exception as e:
            messagebox.showerror("获取报告失败", f"获取修复报告时发生错误:\n{e}")

    def _view_fix_history(self):
        """查看选中图片的修复历史"""
        selection = self.image_tree.selection()
        if not selection or not self.image_summary_data:
            messagebox.showwarning("无选中图片", "请先选择一个图片")
            return
        
        # 获取选中的行索引
        selected_item = selection[0]
        item_index = self.image_tree.index(selected_item)
        
        # 获取排序后的数据
        sort_value = self.image_sort_var.get()
        if sort_value == "total_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=True)
        elif sort_value == "total_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['total'], reverse=False)
        elif sort_value == "errors_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=True)
        elif sort_value == "errors_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['errors'], reverse=False)
        elif sort_value == "auto_fixable_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=True)
        elif sort_value == "auto_fixable_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['auto_fixable'], reverse=False)
        elif sort_value == "name_asc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=False)
        elif sort_value == "name_desc":
            sorted_data = sorted(self.image_summary_data, key=lambda x: x['image_name'].lower(), reverse=True)
        else:
            sorted_data = self.image_summary_data
        
        if item_index >= len(sorted_data):
            messagebox.showerror("错误", "无法获取图片信息")
            return
        
        image_name = sorted_data[item_index]['image_name']
        
        # 获取修复历史
        try:
            history_data = self.health_fixer.get_image_fix_history(image_name, limit=10)
            
            if not history_data:
                messagebox.showinfo("无修复历史", f"图片 {image_name} 暂无修复历史记录")
                return
            
            # 创建历史查看窗口
            history_window = tk.Toplevel(self)
            history_window.title(f"修复历史查看 - {image_name}")
            history_window.geometry("900x700")
            history_window.configure(bg=self.bg_main)
            history_window.transient(self)
            
            # 标题
            title_frame = tk.Frame(history_window, bg=self.bg_main)
            title_frame.pack(fill="x", padx=14, pady=14)
            
            tk.Label(
                title_frame,
                text=f"📜 图片修复历史 - {image_name}",
                bg=self.bg_main,
                fg=self.text_main,
                font=("Microsoft YaHei", 16, "bold")
            ).pack(side="left")
            
            # 关闭按钮
            tk.Button(
                title_frame,
                text="关闭",
                command=history_window.destroy,
                bg=self.border,
                fg=self.text_main,
                font=("Microsoft YaHei", 9),
                padx=12,
                pady=4,
                relief="flat"
            ).pack(side="right")
            
            # 内容容器（左右分割）
            content_frame = tk.Frame(history_window, bg=self.bg_main)
            content_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))
            
            # 左栏：历史列表
            left_frame = tk.Frame(content_frame, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
            left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
            
            # 列表标题
            list_title_frame = tk.Frame(left_frame, bg=self.bg_card)
            list_title_frame.pack(fill="x", padx=12, pady=12)
            
            tk.Label(
                list_title_frame,
                text="修复记录列表（最近10次）",
                bg=self.bg_card,
                fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")
            ).pack(side="left")
            
            # 历史列表Treeview
            columns = ("time", "total", "success", "failed", "skipped", "types")
            history_tree = ttk.Treeview(
                left_frame,
                columns=columns,
                show="headings",
                height=12,
                selectmode="browse"
            )
            
            # 设置列标题
            history_tree.heading("time", text="修复时间", anchor="w")
            history_tree.heading("total", text="总操作数", anchor="center")
            history_tree.heading("success", text="成功", anchor="center")
            history_tree.heading("failed", text="失败", anchor="center")
            history_tree.heading("skipped", text="跳过", anchor="center")
            history_tree.heading("types", text="修复类型", anchor="w")
            
            # 设置列宽度
            history_tree.column("time", width=180, stretch=False)
            history_tree.column("total", width=80, stretch=False, anchor="center")
            history_tree.column("success", width=60, stretch=False, anchor="center")
            history_tree.column("failed", width=60, stretch=False, anchor="center")
            history_tree.column("skipped", width=60, stretch=False, anchor="center")
            history_tree.column("types", width=200, stretch=True)
            
            # 添加历史记录
            for i, record in enumerate(history_data):
                # 格式化时间
                time_str = record["start_time"][:19] if len(record["start_time"]) > 19 else record["start_time"]
                # 修复类型显示（最多显示3种）
                types_str = ", ".join(record["fix_types"][:3])
                if len(record["fix_types"]) > 3:
                    types_str += f"...(+{len(record['fix_types']) - 3})"
                
                history_tree.insert(
                    "", "end",
                    values=(
                        time_str,
                        record["total_operations"],
                        record["successful_operations"],
                        record["failed_operations"],
                        record["skipped_operations"],
                        types_str
                    ),
                    tags=(f"record_{i}",)
                )
            
            # 滚动条
            scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=history_tree.yview)
            history_tree.configure(yscrollcommand=scrollbar.set)
            
            # 布局
            history_tree.pack(side="left", fill="both", expand=True, padx=2, pady=(0, 12))
            scrollbar.pack(side="right", fill="y", pady=(0, 12))
            
            # 右栏：详情
            right_frame = tk.Frame(content_frame, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
            right_frame.pack(side="right", fill="both", expand=True)
            
            # 详情标题
            detail_title_frame = tk.Frame(right_frame, bg=self.bg_card)
            detail_title_frame.pack(fill="x", padx=12, pady=12)
            
            tk.Label(
                detail_title_frame,
                text="修复记录详情",
                bg=self.bg_card,
                fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")
            ).pack(side="left")
            
            # 详情文本区域
            detail_text = tk.Text(
                right_frame,
                bg="#1e2229",
                fg=self.text_main,
                font=("Microsoft YaHei", 9),
                wrap="word",
                relief="flat",
                padx=12,
                pady=12,
                height=15
            )
            detail_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
            detail_text.insert("1.0", "请从左侧列表选择一条修复记录查看详情...")
            detail_text.config(state="disabled")
            
            # 详情滚动条
            detail_scrollbar = tk.Scrollbar(right_frame, command=detail_text.yview)
            detail_text.configure(yscrollcommand=detail_scrollbar.set)
            detail_scrollbar.pack(side="right", fill="y", pady=(0, 12))
            
            # 操作按钮框架
            button_frame = tk.Frame(history_window, bg=self.bg_main)
            button_frame.pack(fill="x", padx=14, pady=(0, 14))
            
            # 查看详细报告按钮
            def view_record_detail():
                selection = history_tree.selection()
                if not selection:
                    messagebox.showwarning("无选中记录", "请先选择一条修复记录")
                    return
                
                item_index = history_tree.index(selection[0])
                if item_index < len(history_data):
                    record = history_data[item_index]
                    
                    # 清空详情区域
                    detail_text.config(state="normal")
                    detail_text.delete("1.0", "end")
                    
                    # 构建详情文本
                    lines = []
                    lines.append("=" * 60)
                    lines.append(f"修复记录详情 - {image_name}")
                    lines.append("=" * 60)
                    lines.append(f"会话ID: {record['session_id']}")
                    lines.append(f"开始时间: {record['start_time']}")
                    lines.append(f"结束时间: {record['end_time']}")
                    lines.append("")
                    
                    lines.append("【操作统计】")
                    lines.append(f"  总操作数: {record['total_operations']}")
                    lines.append(f"  成功操作: {record['successful_operations']}")
                    lines.append(f"  失败操作: {record['failed_operations']}")
                    lines.append(f"  跳过操作: {record['skipped_operations']}")
                    lines.append("")
                    
                    lines.append("【修复类型】")
                    for fix_type in record['fix_types']:
                        lines.append(f"  • {fix_type}")
                    lines.append("")
                    
                    lines.append("【操作详情】")
                    if record.get('operations'):
                        for i, op in enumerate(record['operations'][:15], 1):
                            lines.append(f"  {i}. {op.fix_type}: {op.result.value}")
                            lines.append(f"     问题: {op.issue.message[:70]}{'...' if len(op.issue.message) > 70 else ''}")
                            lines.append(f"     结果: {op.message}")
                            if i < 15:
                                lines.append("")
                        if len(record['operations']) > 15:
                            lines.append(f"  还有{len(record['operations']) - 15}个操作未显示...")
                    else:
                        lines.append("  无操作详情")
                    lines.append("")
                    
                    # AI复核预留
                    lines.append("【AI复核 (预留)】")
                    lines.append("  此处为AI复核预留位置")
                    lines.append("  后续可扩展AI分析修复质量、提供优化建议")
                    lines.append("")
                    
                    lines.append("=" * 60)
                    
                    detail_text.insert("1.0", "\n".join(lines))
                    detail_text.config(state="disabled")
            
            tk.Button(
                button_frame,
                text="查看选中记录详情",
                command=view_record_detail,
                bg="#3b82f6",
                fg="white",
                font=("Microsoft YaHei", 9),
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2"
            ).pack(side="left", padx=2)
            
            # 导出历史按钮
            def export_history():
                file_path = filedialog.asksaveasfilename(
                    title="导出修复历史",
                    defaultextension=".txt",
                    filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
                )
                if file_path:
                    try:
                        lines = []
                        lines.append("=" * 60)
                        lines.append(f"图片修复历史报告 - {image_name}")
                        lines.append("=" * 60)
                        lines.append(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        lines.append(f"总记录数: {len(history_data)}")
                        lines.append("")
                        
                        for i, record in enumerate(history_data, 1):
                            lines.append(f"【记录 {i}】")
                            lines.append(f"  会话ID: {record['session_id']}")
                            lines.append(f"  时间: {record['start_time']}")
                            lines.append(f"  总操作数: {record['total_operations']}")
                            lines.append(f"  成功: {record['successful_operations']}")
                            lines.append(f"  失败: {record['failed_operations']}")
                            lines.append(f"  跳过: {record['skipped_operations']}")
                            lines.append(f"  修复类型: {', '.join(record['fix_types'])}")
                            lines.append("")
                        
                        lines.append("=" * 60)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write("\n".join(lines))
                        messagebox.showinfo("导出成功", f"修复历史已导出到:\n{file_path}")
                    except Exception as e:
                        messagebox.showerror("导出失败", f"导出失败:\n{e}")
            
            tk.Button(
                button_frame,
                text="导出历史报告",
                command=export_history,
                bg="#10b981",
                fg="white",
                font=("Microsoft YaHei", 9),
                padx=12,
                pady=6,
                relief="flat",
                cursor="hand2"
            ).pack(side="left", padx=2)
            
            # 绑定选择事件
            def on_history_selected(event):
                view_record_detail()
            
            history_tree.bind("<<TreeviewSelect>>", on_history_selected)
            
        except Exception as e:
            messagebox.showerror("获取历史失败", f"获取修复历史时发生错误:\n{e}")
    
    def destroy(self):
        """销毁窗口，清理回调"""
        if hasattr(self, 'language_manager') and hasattr(self.language_manager, 'unregister_callback'):
            self.language_manager.unregister_callback(self._refresh_ui_on_language_change)
        if hasattr(self, 'style_manager'):
            self.style_manager.unregister_callback(self._refresh_ui_on_style_change)
        super().destroy()


def open_data_health_window(master, context, on_jump_to_image=None):
    """
    打开数据集健康检查窗口（方便函数）
    
    Args:
        master: 父窗口
        context: WorkbenchContext 实例
        on_jump_to_image: 跳转到图片的回调函数
    """
    window = DataHealthWindow(master, context, on_jump_to_image)
    window.transient(master)
    window.grab_set()
    return window