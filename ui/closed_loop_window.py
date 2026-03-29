#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
closed_loop_window.py - 闭环修正中心窗口

功能：
1. bad case 列表查看与管理
2. 低表现类别查看与管理
3. 再训练建议摘要
4. 闭环修正报告
5. 跳转到问题处理链路
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from typing import Optional, List, Dict, Any

from core.closed_loop_manager import (
    ClosedLoopManager,
    BadCaseRecord,
    BadCaseSource,
    BadCaseStatus,
    LowPerformanceClass,
    ClosedLoopReport,
    create_bad_case_from_quality_check,
    create_bad_case_from_training_result,
    create_low_performance_class_simple
)
from core.context.workbench_context import WorkbenchContext
from core.language_manager import t


class ClosedLoopWindow:
    """闭环修正中心窗口"""
    
    def __init__(self, master, context: WorkbenchContext):
        """
        初始化闭环修正中心窗口
        
        Args:
            master: 父窗口
            context: WorkbenchContext 实例
        """
        self.master = master
        self.context = context
        
        # 窗口配置
        self.window = tk.Toplevel(master)
        self.window.title(t("TITLE_CLOSED_LOOP"))
        self.window.geometry("1200x800")
        self.window.configure(bg="#16181d")
        self.window.transient(master)
        self.window.grab_set()
        
        # 样式
        self.bg_main = "#16181d"
        self.bg_card = "#20242c"
        self.bg_card_2 = "#252a33"
        self.text_main = "#f5f7fa"
        self.text_sub = "#aeb6c2"
        self.accent = "#6ea8fe"
        self.border = "#2d3440"
        self.btn_bg = "#2a303a"
        self.btn_hover = "#343b47"
        self.error_color = "#f87171"
        self.warning_color = "#fbbf24"
        self.success_color = "#10b981"
        
        # 管理器实例
        self.manager = ClosedLoopManager()
        
        # 当前选中项
        self.selected_bad_case_id = None
        self.selected_low_perf_key = None
        
        # 构建UI
        self._build_ui()
        
        # 初始加载
        self._refresh_bad_cases_list()
        self._refresh_low_performance_list()
        self._update_summary()
    
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
            text=f"🔄 {t('TITLE_CLOSED_LOOP')}",
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
        
        # 顶部按钮栏
        top_button_frame = tk.Frame(main_frame, bg=self.bg_main)
        top_button_frame.pack(fill="x", pady=(0, 12))
        
        # 生成报告按钮
        tk.Button(
            top_button_frame,
            text="生成闭环报告",
            command=self._generate_report,
            bg="#3b82f6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=2)
        
        # 查看建议摘要按钮
        tk.Button(
            top_button_frame,
            text="查看建议摘要",
            command=self._show_training_suggestions,
            bg="#10b981",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=2)
        
        # 刷新按钮
        tk.Button(
            top_button_frame,
            text="刷新数据",
            command=self._refresh_all,
            bg=self.btn_bg,
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=2)
        
        # 添加测试数据按钮（开发用）
        tk.Button(
            top_button_frame,
            text="添加测试数据",
            command=self._add_test_data,
            bg="#8b5cf6",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=2)
        
        # 主内容区域（左右分栏）
        content_frame = tk.Frame(main_frame, bg=self.bg_main)
        content_frame.pack(fill="both", expand=True)
        
        # 左栏：Bad Cases
        left_frame = tk.Frame(content_frame, bg=self.bg_main)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        # 右栏：低表现类别和详情
        right_frame = tk.Frame(content_frame, bg=self.bg_main)
        right_frame.pack(side="right", fill="both", expand=True)
        
        # ==================== 左栏内容 ====================
        
        # Bad Cases 卡片
        bad_cases_card = self._create_card(left_frame, "📝 Bad Cases 列表")
        bad_cases_card.pack(fill="both", expand=True)
        
        # Bad Cases 表格容器
        bad_cases_container = tk.Frame(bad_cases_card, bg=self.bg_card)
        bad_cases_container.pack(fill="both", expand=True, padx=12, pady=12)
        
        # 创建Treeview
        columns = ("status", "image_name", "source", "problem", "time", "class")
        self.bad_cases_tree = ttk.Treeview(
            bad_cases_container,
            columns=columns,
            show="headings",
            height=12
        )
        
        # 设置列标题
        self.bad_cases_tree.heading("status", text="状态", anchor="center")
        self.bad_cases_tree.heading("image_name", text="图片名", anchor="w")
        self.bad_cases_tree.heading("source", text="来源", anchor="w")
        self.bad_cases_tree.heading("problem", text="问题摘要", anchor="w")
        self.bad_cases_tree.heading("time", text="时间", anchor="w")
        self.bad_cases_tree.heading("class", text="类别", anchor="w")
        
        # 设置列宽度
        self.bad_cases_tree.column("status", width=80, stretch=False, anchor="center")
        self.bad_cases_tree.column("image_name", width=150, stretch=False, anchor="w")
        self.bad_cases_tree.column("source", width=100, stretch=False, anchor="w")
        self.bad_cases_tree.column("problem", width=200, stretch=True, anchor="w")
        self.bad_cases_tree.column("time", width=120, stretch=False, anchor="w")
        self.bad_cases_tree.column("class", width=80, stretch=False, anchor="w")
        
        # 滚动条
        bad_cases_scrollbar = ttk.Scrollbar(bad_cases_container, orient="vertical", command=self.bad_cases_tree.yview)
        self.bad_cases_tree.configure(yscrollcommand=bad_cases_scrollbar.set)
        
        # 布局
        self.bad_cases_tree.grid(row=0, column=0, sticky="nsew")
        bad_cases_scrollbar.grid(row=0, column=1, sticky="ns")
        
        bad_cases_container.grid_rowconfigure(0, weight=1)
        bad_cases_container.grid_columnconfigure(0, weight=1)
        
        # Bad Cases 操作按钮
        bad_cases_btn_frame = tk.Frame(bad_cases_card, bg=self.bg_card)
        bad_cases_btn_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        tk.Button(
            bad_cases_btn_frame,
            text="查看详情",
            command=self._view_bad_case_detail,
            bg=self.accent,
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=4,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=2)
        
        tk.Button(
            bad_cases_btn_frame,
            text="标记为已处理",
            command=self._mark_bad_case_resolved,
            bg=self.success_color,
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=4,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=2)
        
        tk.Button(
            bad_cases_btn_frame,
            text="跳转到图片",
            command=self._jump_to_bad_case_image,
            bg="#f59e0b",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=4,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=2)
        
        tk.Button(
            bad_cases_btn_frame,
            text="删除选中",
            command=self._delete_selected_bad_case,
            bg=self.error_color,
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=4,
            relief="flat",
            cursor="hand2"
        ).pack(side="right", padx=2)
        
        # ==================== 右栏内容 ====================
        
        # 右栏上部分：低表现类别
        low_perf_card = self._create_card(right_frame, "📊 低表现类别")
        low_perf_card.pack(fill="both", expand=True, pady=(0, 12))
        
        # 低表现类别表格容器
        low_perf_container = tk.Frame(low_perf_card, bg=self.bg_card)
        low_perf_container.pack(fill="both", expand=True, padx=12, pady=12)
        
        # 创建Treeview
        low_perf_columns = ("class_name", "problem", "status", "priority", "actions")
        self.low_perf_tree = ttk.Treeview(
            low_perf_container,
            columns=low_perf_columns,
            show="headings",
            height=8
        )
        
        # 设置列标题
        self.low_perf_tree.heading("class_name", text="类别名", anchor="w")
        self.low_perf_tree.heading("problem", text="问题描述", anchor="w")
        self.low_perf_tree.heading("status", text="状态", anchor="center")
        self.low_perf_tree.heading("priority", text="优先级", anchor="center")
        self.low_perf_tree.heading("actions", text="建议动作", anchor="w")
        
        # 设置列宽度
        self.low_perf_tree.column("class_name", width=100, stretch=False, anchor="w")
        self.low_perf_tree.column("problem", width=200, stretch=True, anchor="w")
        self.low_perf_tree.column("status", width=80, stretch=False, anchor="center")
        self.low_perf_tree.column("priority", width=60, stretch=False, anchor="center")
        self.low_perf_tree.column("actions", width=150, stretch=False, anchor="w")
        
        # 滚动条
        low_perf_scrollbar = ttk.Scrollbar(low_perf_container, orient="vertical", command=self.low_perf_tree.yview)
        self.low_perf_tree.configure(yscrollcommand=low_perf_scrollbar.set)
        
        # 布局
        self.low_perf_tree.grid(row=0, column=0, sticky="nsew")
        low_perf_scrollbar.grid(row=0, column=1, sticky="ns")
        
        low_perf_container.grid_rowconfigure(0, weight=1)
        low_perf_container.grid_columnconfigure(0, weight=1)
        
        # 低表现类别操作按钮
        low_perf_btn_frame = tk.Frame(low_perf_card, bg=self.bg_card)
        low_perf_btn_frame.pack(fill="x", padx=12, pady=(0, 12))
        
        tk.Button(
            low_perf_btn_frame,
            text="查看详情",
            command=self._view_low_perf_detail,
            bg=self.accent,
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=4,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=2)
        
        tk.Button(
            low_perf_btn_frame,
            text="标记为已处理",
            command=self._mark_low_perf_resolved,
            bg=self.success_color,
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=4,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=2)
        
        tk.Button(
            low_perf_btn_frame,
            text="跳转到质检",
            command=self._jump_to_quality_check,
            bg="#f59e0b",
            fg="white",
            font=("Microsoft YaHei", 9),
            padx=10,
            pady=4,
            relief="flat",
            cursor="hand2"
        ).pack(side="left", padx=2)
        
        # 右栏下部分：详情和摘要
        detail_card = self._create_card(right_frame, "📋 详情与摘要")
        detail_card.pack(fill="both", expand=True)
        
        # 详情文本区域
        self.detail_text = tk.Text(
            detail_card,
            bg="#1e2229",
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            wrap="word",
            relief="flat",
            padx=12,
            pady=12,
            height=10
        )
        self.detail_text.pack(fill="both", expand=True, padx=12, pady=12)
        self.detail_text.insert("1.0", "请选择一个bad case或低表现类别查看详情...")
        self.detail_text.config(state="disabled")
        
        # 绑定选择事件
        self.bad_cases_tree.bind("<<TreeviewSelect>>", self._on_bad_case_selected)
        self.low_perf_tree.bind("<<TreeviewSelect>>", self._on_low_perf_selected)
    
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
    
    def _refresh_all(self):
        """刷新所有数据"""
        # 重新加载管理器数据
        self.manager = ClosedLoopManager()
        
        # 刷新列表
        self._refresh_bad_cases_list()
        self._refresh_low_performance_list()
        self._update_summary()
        
        # 清空详情
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", "数据已刷新，请选择一个项目查看详情...")
        self.detail_text.config(state="disabled")
    
    def _refresh_bad_cases_list(self):
        """刷新bad cases列表"""
        # 清空现有项
        for item in self.bad_cases_tree.get_children():
            self.bad_cases_tree.delete(item)
        
        # 获取所有bad cases
        bad_cases = self.manager.get_all_bad_cases()
        
        # 状态颜色映射
        status_colors = {
            BadCaseStatus.PENDING: self.warning_color,
            BadCaseStatus.PROCESSING: self.accent,
            BadCaseStatus.RESOLVED: self.success_color,
            BadCaseStatus.SKIPPED: self.text_sub,
            BadCaseStatus.REOPENED: self.error_color
        }
        
        # 添加记录
        for case in bad_cases:
            # 状态显示文本
            status_text = case.status.value
            
            # 截取问题摘要
            problem_summary = case.problem_summary
            if len(problem_summary) > 30:
                problem_summary = problem_summary[:27] + "..."
            
            # 时间格式化
            time_str = case.create_time
            if len(time_str) > 16:
                time_str = time_str[5:16]  # 显示月-日 时:分
            
            self.bad_cases_tree.insert(
                "", "end",
                values=(
                    status_text,
                    case.image_name,
                    case.source_type.value,
                    problem_summary,
                    time_str,
                    case.class_name
                ),
                tags=(case.id,)
            )
            
            # 设置状态颜色
            if case.status in status_colors:
                self.bad_cases_tree.tag_configure(
                    case.id,
                    foreground=status_colors[case.status]
                )
    
    def _refresh_low_performance_list(self):
        """刷新低表现类别列表"""
        # 清空现有项
        for item in self.low_perf_tree.get_children():
            self.low_perf_tree.delete(item)
        
        # 获取所有低表现类别
        low_perf_classes = self.manager.get_all_low_performance_classes()
        
        # 优先级颜色映射
        priority_colors = {
            1: self.success_color,  # 低优先级
            2: self.accent,        # 中优先级
            3: self.warning_color, # 高优先级
            4: self.error_color,   # 紧急
            5: self.error_color    # 非常紧急
        }
        
        # 添加记录
        for cls in low_perf_classes:
            # 截取问题描述
            problem_desc = cls.problem_description
            if len(problem_desc) > 30:
                problem_desc = problem_desc[:27] + "..."
            
            # 截取建议动作
            actions = ""
            if cls.suggested_actions:
                actions = cls.suggested_actions[0]
                if len(actions) > 20:
                    actions = actions[:17] + "..."
            
            # 优先级显示
            priority_text = "⭐" * cls.priority
            
            self.low_perf_tree.insert(
                "", "end",
                values=(
                    cls.class_name,
                    problem_desc,
                    cls.status,
                    priority_text,
                    actions
                ),
                tags=(f"{cls.class_name}_{cls.create_time}",)
            )
            
            # 设置优先级颜色
            if cls.priority in priority_colors:
                self.low_perf_tree.tag_configure(
                    f"{cls.class_name}_{cls.create_time}",
                    foreground=priority_colors.get(cls.priority, self.text_main)
                )
    
    def _update_summary(self):
        """更新摘要信息（在标题栏显示）"""
        bad_cases = self.manager.get_all_bad_cases()
        low_perf_classes = self.manager.get_all_low_performance_classes()
        
        pending_bad_cases = len([c for c in bad_cases if c.status == BadCaseStatus.PENDING])
        pending_classes = len([c for c in low_perf_classes if c.status == "待处理"])
        
        # 更新窗口标题
        title = f"🔄 闭环修正中心"
        if pending_bad_cases > 0 or pending_classes > 0:
            title += f" (待处理: {pending_bad_cases}个bad case, {pending_classes}个低表现类别)"
        
        self.window.title(title)
    
    def _on_bad_case_selected(self, event):
        """bad case选择事件"""
        selection = self.bad_cases_tree.selection()
        if not selection:
            self.selected_bad_case_id = None
            return
        
        item = selection[0]
        self.selected_bad_case_id = self.bad_cases_tree.item(item, "tags")[0]
        
        # 显示详情
        self._show_bad_case_detail(self.selected_bad_case_id)
    
    def _on_low_perf_selected(self, event):
        """低表现类别选择事件"""
        selection = self.low_perf_tree.selection()
        if not selection:
            self.selected_low_perf_key = None
            return
        
        item = selection[0]
        self.selected_low_perf_key = self.low_perf_tree.item(item, "tags")[0]
        
        # 显示详情
        self._show_low_perf_detail(self.selected_low_perf_key)
    
    def _show_bad_case_detail(self, case_id: str):
        """显示bad case详情"""
        record = self.manager.get_bad_case_by_id(case_id)
        if not record:
            return
        
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        
        lines = []
        lines.append("=" * 60)
        lines.append("Bad Case 详情")
        lines.append("=" * 60)
        lines.append(f"ID: {record.id}")
        lines.append(f"图片名: {record.image_name}")
        lines.append(f"来源: {record.source_type.value}")
        lines.append(f"状态: {record.status.value}")
        lines.append(f"创建时间: {record.create_time}")
        lines.append(f"更新时间: {record.update_time}")
        lines.append("")
        lines.append("【问题详情】")
        lines.append(f"  问题类型: {record.issue_type}")
        lines.append(f"  相关类别: {record.class_name}")
        lines.append(f"  问题摘要: {record.problem_summary}")
        if record.confidence > 0:
            lines.append(f"  置信度/严重度: {record.confidence:.2f}")
        lines.append("")
        
        lines.append("【处理信息】")
        if record.assigned_to:
            lines.append(f"  分配给: {record.assigned_to}")
        if record.resolution_note:
            lines.append(f"  处理说明: {record.resolution_note}")
        if record.resolution_time:
            lines.append(f"  处理时间: {record.resolution_time}")
        lines.append("")
        
        lines.append("【回流路径】")
        lines.append(f"  可跳转到图片: {'是' if record.can_jump_to_image else '否'}")
        if record.jump_target:
            lines.append(f"  跳转目标: {record.jump_target}")
        if record.related_modules:
            lines.append(f"  相关处理模块: {', '.join(record.related_modules)}")
        lines.append("")
        
        # AI建议预留
        if record.ai_suggestions:
            lines.append("【AI建议】")
            for i, suggestion in enumerate(record.ai_suggestions, 1):
                lines.append(f"  {i}. {suggestion}")
            lines.append("")
        
        lines.append("【处理建议】")
        lines.append("  1. 点击【跳转到图片】查看具体问题")
        lines.append("  2. 在标注编辑器中修正问题")
        lines.append("  3. 标记为已处理或重新打开")
        lines.append("")
        lines.append("=" * 60)
        
        self.detail_text.insert("1.0", "\n".join(lines))
        self.detail_text.config(state="disabled")
    
    def _show_low_perf_detail(self, class_key: str):
        """显示低表现类别详情"""
        # 查找对应的记录
        low_perf_classes = self.manager.get_all_low_performance_classes()
        record = None
        for cls in low_perf_classes:
            if f"{cls.class_name}_{cls.create_time}" == class_key:
                record = cls
                break
        
        if not record:
            return
        
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        
        lines = []
        lines.append("=" * 60)
        lines.append("低表现类别详情")
        lines.append("=" * 60)
        lines.append(f"类别名: {record.class_name}")
        lines.append(f"状态: {record.status}")
        lines.append(f"优先级: {record.priority}")
        lines.append(f"创建时间: {record.create_time}")
        lines.append(f"更新时间: {record.update_time}")
        lines.append("")
        
        lines.append("【问题描述】")
        lines.append(f"  {record.problem_description}")
        lines.append("")
        
        lines.append("【性能指标】")
        lines.append(f"  样本数量: {record.sample_count}")
        lines.append(f"  错误数量: {record.error_count}")
        if record.performance_metrics:
            for metric, value in record.performance_metrics.items():
                lines.append(f"  {metric}: {value:.3f}")
        lines.append("")
        
        lines.append("【建议动作】")
        for i, action in enumerate(record.suggested_actions, 1):
            lines.append(f"  {i}. {action}")
        lines.append("")
        
        if record.related_bad_cases:
            lines.append(f"【相关Bad Cases ({len(record.related_bad_cases)}个)】")
            for i, case_id in enumerate(record.related_bad_cases[:3], 1):
                lines.append(f"  {i}. {case_id}")
            if len(record.related_bad_cases) > 3:
                lines.append(f"  还有{len(record.related_bad_cases) - 3}个未显示...")
            lines.append("")
        
        # AI分析预留
        if record.ai_analysis:
            lines.append("【AI分析】")
            lines.append(f"  {record.ai_analysis}")
            lines.append("")
        
        lines.append("【处理建议】")
        lines.append("  1. 点击【跳转到质检】检查该类别的标注质量")
        lines.append("  2. 增加该类别的训练样本")
        lines.append("  3. 重新训练模型并评估效果")
        lines.append("  4. 标记为已处理或调整优先级")
        lines.append("")
        lines.append("=" * 60)
        
        self.detail_text.insert("1.0", "\n".join(lines))
        self.detail_text.config(state="disabled")
    
    def _view_bad_case_detail(self):
        """查看选中的bad case详情"""
        if not self.selected_bad_case_id:
            messagebox.showwarning("未选中", "请先选择一个bad case")
            return
        
        self._show_bad_case_detail(self.selected_bad_case_id)
    
    def _view_low_perf_detail(self):
        """查看选中的低表现类别详情"""
        if not self.selected_low_perf_key:
            messagebox.showwarning("未选中", "请先选择一个低表现类别")
            return
        
        self._show_low_perf_detail(self.selected_low_perf_key)
    
    def _mark_bad_case_resolved(self):
        """标记选中的bad case为已处理"""
        if not self.selected_bad_case_id:
            messagebox.showwarning("未选中", "请先选择一个bad case")
            return
        
        # 确认
        confirm = messagebox.askyesno(
            "确认标记",
            "确认要将选中的bad case标记为【已处理】吗？"
        )
        if not confirm:
            return
        
        # 更新状态
        success, msg = self.manager.update_bad_case_status(
            self.selected_bad_case_id,
            BadCaseStatus.RESOLVED,
            resolution_note="在闭环修正中心标记为已处理"
        )
        
        if success:
            messagebox.showinfo("成功", msg)
            self._refresh_all()
        else:
            messagebox.showerror("失败", msg)
    
    def _mark_low_perf_resolved(self):
        """标记选中的低表现类别为已处理"""
        if not self.selected_low_perf_key:
            messagebox.showwarning("未选中", "请先选择一个低表现类别")
            return
        
        # 这里需要扩展LowPerformanceClass以支持状态更新
        # 暂时使用消息框提示
        messagebox.showinfo(
            "功能预留",
            "低表现类别状态更新功能将在后续版本中实现。\n\n"
            "当前可以通过重新训练和改进标注来处理低表现类别。"
        )
    
    def _jump_to_bad_case_image(self):
        """跳转到bad case对应的图片"""
        if not self.selected_bad_case_id:
            messagebox.showwarning("未选中", "请先选择一个bad case")
            return
        
        success, target, hint = self.manager.get_jump_target_for_bad_case(self.selected_bad_case_id)
        
        if not success:
            messagebox.showerror("跳转失败", hint)
            return
        
        # 显示跳转提示
        messagebox.showinfo(
            "跳转提示",
            f"可以跳转到图片: {target}\n\n{hint}\n\n"
            f"请手动在标注界面打开对应图片进行处理。"
        )
        
        # 记录跳转请求（实际跳转需要与主窗口集成）
        # 这里只是显示提示，实际集成需要在MainWindow中添加回调
        
        # 标记为处理中
        self.manager.update_bad_case_status(
            self.selected_bad_case_id,
            BadCaseStatus.PROCESSING,
            assigned_to="用户"
        )
        
        self._refresh_all()
    
    def _jump_to_quality_check(self):
        """跳转到质检中心"""
        if not self.selected_low_perf_key:
            messagebox.showwarning("未选中", "请先选择一个低表现类别")
            return
        
        # 查找类别名
        low_perf_classes = self.manager.get_all_low_performance_classes()
        class_name = None
        for cls in low_perf_classes:
            if f"{cls.class_name}_{cls.create_time}" == self.selected_low_perf_key:
                class_name = cls.class_name
                break
        
        if class_name:
            messagebox.showinfo(
                "跳转到质检中心",
                f"建议对类别【{class_name}】运行数据健康检查。\n\n"
                f"请在主界面点击【数据健康检查】按钮，然后：\n"
                f"1. 运行健康检查\n"
                f"2. 查看类别分布\n"
                f"3. 检查该类别的问题\n"
                f"4. 进行必要的修正"
            )
        else:
            messagebox.showinfo(
                "跳转到质检中心",
                "建议运行数据健康检查，发现潜在问题。\n\n"
                "请在主界面点击【数据健康检查】按钮。"
            )
    
    def _delete_selected_bad_case(self):
        """删除选中的bad case"""
        if not self.selected_bad_case_id:
            messagebox.showwarning("未选中", "请先选择一个bad case")
            return
        
        # 确认
        confirm = messagebox.askyesno(
            "确认删除",
            "确认要删除选中的bad case吗？此操作不可恢复。"
        )
        if not confirm:
            return
        
        # 这里需要扩展管理器以支持删除
        # 暂时显示提示
        messagebox.showinfo(
            "功能预留",
            "bad case删除功能将在后续版本中实现。\n\n"
            "当前可以通过标记为【已解决】或【已跳过】来管理bad case。"
        )
    
    def _generate_report(self):
        """生成闭环修正报告"""
        # 生成报告
        report = self.manager.generate_closed_loop_report()
        
        # 显示报告
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", report.get_summary_text())
        self.detail_text.config(state="disabled")
        
        # 询问是否保存报告文件
        save = messagebox.askyesno(
            "报告生成成功",
            f"闭环修正报告已生成！\n\n"
            f"报告ID: {report.report_id}\n"
            f"生成时间: {report.generate_time}\n\n"
            f"是否保存报告文件？"
        )
        
        if save:
            file_path = filedialog.asksaveasfilename(
                title="保存闭环修正报告",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if file_path:
                try:
                    if file_path.endswith('.json'):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
                    else:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(report.get_summary_text())
                    
                    messagebox.showinfo("保存成功", f"报告已保存到:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("保存失败", f"保存报告时发生错误:\n{str(e)}")
    
    def _show_training_suggestions(self):
        """显示再训练建议摘要"""
        suggestions = self.manager.get_training_suggestions_summary()
        
        # 显示建议
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", suggestions)
        self.detail_text.config(state="disabled")
        
        # 可以在这里添加更多操作选项
        messagebox.showinfo(
            "再训练建议摘要",
            "再训练建议摘要已显示在详情区域。\n\n"
            "建议根据摘要内容制定训练计划。"
        )
    
    def _add_test_data(self):
        """添加测试数据（开发用）"""
        # 添加一些测试bad cases
        test_cases = [
            create_bad_case_from_quality_check(
                image_name="test_image_001.jpg",
                issue_type="标注错误",
                problem_summary="类别标注错误，将A类标成了B类",
                class_name="A类"
            ),
            create_bad_case_from_quality_check(
                image_name="test_image_002.jpg",
                issue_type="框坐标错误",
                problem_summary="标注框超出图片边界",
                class_name="C类"
            ),
            create_bad_case_from_training_result(
                image_name="test_image_003.jpg",
                problem_summary="模型预测置信度过低，需要检查标注质量",
                class_name="B类",
                confidence=0.35
            ),
            create_bad_case_from_training_result(
                image_name="test_image_004.jpg",
                problem_summary="模型误检，将背景检测为目标",
                class_name="D类",
                confidence=0.42
            )
        ]
        
        # 添加测试低表现类别
        test_classes = [
            create_low_performance_class_simple(
                class_name="A类",
                problem="AP指标较低，仅为0.45，需要改进",
                sample_count=50,
                priority=3
            ),
            create_low_performance_class_simple(
                class_name="B类",
                problem="召回率低，漏检较多",
                sample_count=30,
                priority=2
            ),
            create_low_performance_class_simple(
                class_name="C类",
                problem="与其他类别混淆严重",
                sample_count=20,
                priority=4
            )
        ]
        
        added_count = 0
        
        # 添加bad cases
        for case_data in test_cases:
            success, msg = self.manager.add_bad_case(**case_data)
            if success:
                added_count += 1
        
        # 添加低表现类别
        for class_data in test_classes:
            success, msg = self.manager.add_low_performance_class(**class_data)
            if success:
                added_count += 1
        
        if added_count > 0:
            messagebox.showinfo(
                "测试数据添加成功",
                f"已成功添加{added_count}条测试数据。\n\n"
                f"现在可以测试闭环修正中心的各项功能。"
            )
            self._refresh_all()
        else:
            messagebox.showwarning(
                "添加失败",
                "未能添加测试数据，可能数据已存在或发生错误。"
            )


def open_closed_loop_window(master, context):
    """
    打开闭环修正中心窗口（方便函数）
    
    Args:
        master: 父窗口
        context: WorkbenchContext 实例
    """
    window = ClosedLoopWindow(master, context)
    return window