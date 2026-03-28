"""
训练结果对比窗口 - 对比多个训练结果
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
import matplotlib
matplotlib.use('TkAgg')  # 设置后端
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime

from core.training_result_analyzer import get_result_analyzer, ClassificationTrainingResult


def get_text(key):
    """根据当前语言配置获取文本"""
    texts = {
        "TITLE_TRAINING_COMPARISON": "训练结果对比",
        "LABEL_SUMMARY_COMPARISON": "摘要对比",
        "LABEL_CURVE_COMPARISON": "曲线对比",
        "LABEL_RESULT_DETAILS": "结果详情",
        "BTN_CLOSE": "关闭",
        "BTN_EXPORT_COMPARISON": "导出对比报告",
        "BTN_REUSE_CONFIG": "复用配置",
        "BTN_REUSE_CONFIG_A": "复用实验A配置",
        "BTN_REUSE_CONFIG_B": "复用实验B配置",
        "TAB_SUMMARY": "摘要对比",
        "TAB_CURVES": "曲线对比",
        "TAB_DETAILS": "详细数据",
        "TAB_CONFIG_COMPARISON": "配置对比",
        "COL_EXP_NAME": "实验名称",
        "COL_MODEL": "模型",
        "COL_BEST_EPOCH": "最佳轮数",
        "COL_BEST_VAL_ACC": "最佳验证准确率",
        "COL_FINAL_VAL_ACC": "最终验证准确率",
        "COL_TRAINING_TIME": "训练时间",
        "COL_AUGMENTATION": "数据增强",
        "COL_PRETRAINED": "预训练权重",
        "COL_SCHEDULER": "学习率调度",
        "COL_FIELD_NAME": "字段名",
        "COL_VALUE_A": "实验A的值",
        "COL_VALUE_B": "实验B的值",
        "COL_IS_DIFFERENT": "是否不同",
        "MSG_LOAD_FAILED": "加载训练结果失败",
        "MSG_NO_VALID_RESULTS": "没有有效的训练结果可对比",
        "MSG_REUSE_SUCCESS": "配置已复制到训练中心",
        "MSG_REUSE_ERROR": "复用配置失败",
        "TAB_NOTES_COMPARISON": "批注对比",
        "LABEL_EXPERIMENT_NOTES": "实验备注",
        "LABEL_CHANGE_DESCRIPTION": "改动说明",
        "LABEL_RETRAIN_REASON": "重新训练原因",
        "LABEL_SOURCE_EXPERIMENT": "来源实验",
        "MSG_NO_NOTES": "没有批注数据可对比",
    }
    return texts.get(key, key)


class TrainingComparisonWindow(tk.Toplevel):
    """训练结果对比窗口"""
    
    def __init__(self, master, log_paths, exp_names=None):
        super().__init__(master)
        self.master = master
        
        self.title(get_text("TITLE_TRAINING_COMPARISON"))
        self.geometry("1600x900")
        self.minsize(1400, 700)
        self.configure(bg="#16181d")
        self.transient(master)
        self.grab_set()
        
        # 样式
        self.bg_main = "#16181d"
        self.bg_card = "#252a33"
        self.text_main = "#f5f7fa"
        self.text_sub = "#aeb6c2"
        self.border = "#2d3440"
        self.accent_green = "#67d39a"
        self.accent_yellow = "#ff9d57"
        self.accent_red = "#ff6b6b"
        self.accent_blue = "#4da3ff"
        
        # 数据
        self.log_paths = log_paths
        self.exp_names = exp_names or [f"实验{i+1}" for i in range(len(log_paths))]
        self.results = []
        self.analyzer = get_result_analyzer()
        
        # 图形相关
        self.figures = []
        self.canvases = []
        
        # 颜色序列（用于区分不同实验）
        self.color_sequence = [
            "#4da3ff",  # 蓝色
            "#67d39a",  # 绿色
            "#ff9d57",  # 橙色
            "#a855f7",  # 紫色
            "#ff6b6b",  # 红色
            "#00d4aa",  # 青色
        ]
        
        # 加载结果
        self._load_results()
        
        # 如果没有有效结果，显示错误
        if not self.results:
            self._show_error(get_text("MSG_NO_VALID_RESULTS"))
            return
        
        # 构建UI
        self._build_ui()
    
    def _load_results(self):
        """加载训练结果"""
        for i, (log_path, exp_name) in enumerate(zip(self.log_paths, self.exp_names)):
            try:
                result = self.analyzer.load_result(log_path)
                if result:
                    # 添加实验名称
                    setattr(result, 'exp_name', exp_name)
                    self.results.append(result)
                else:
                    print(f"警告: 无法加载结果 {log_path}")
            except Exception as e:
                print(f"错误: 加载结果 {log_path} 失败: {e}")
    
    def _build_ui(self):
        """构建UI界面"""
        # 主容器
        main_container = tk.Frame(self, bg=self.bg_main)
        main_container.pack(fill="both", expand=True, padx=14, pady=14)
        
        # 顶部信息栏
        self._build_top_bar(main_container)
        
        # 标签页容器
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True, pady=(14, 0))
        
        # 样式化标签页
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.bg_main, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.bg_card, foreground=self.text_main,
                       padding=[10, 5], font=('Microsoft YaHei', 10))
        style.map('TNotebook.Tab', background=[('selected', '#2d3440')], 
                 foreground=[('selected', self.accent_blue)])
        
        # 创建标签页
        self._build_summary_tab()
        self._build_curves_tab()
        self._build_details_tab()
        self._build_config_comparison_tab()
        self._build_notes_comparison_tab()
        
        # 底部按钮栏
        self._build_bottom_bar(main_container)
    
    def _build_top_bar(self, parent):
        """构建顶部信息栏"""
        top_frame = tk.Frame(parent, bg=self.bg_card, height=60, highlightthickness=1, 
                           highlightbackground=self.border)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)
        
        # 显示对比信息
        info_text = f"正在对比 {len(self.results)} 个训练结果"
        tk.Label(top_frame, text=info_text, bg=self.bg_card, fg=self.text_main,
                font=("Microsoft YaHei", 12, "bold")).pack(side="left", padx=20, pady=10)
        
        # 显示实验名称
        exp_text = f"实验: {', '.join(self.exp_names[:3])}"
        if len(self.exp_names) > 3:
            exp_text += f" 等{len(self.exp_names)}个"
        
        tk.Label(top_frame, text=exp_text, bg=self.bg_card, fg=self.text_sub,
                font=("Consolas", 9)).pack(side="right", padx=20, pady=10)
    
    def _build_summary_tab(self):
        """构建摘要对比标签页"""
        summary_frame = tk.Frame(self.notebook, bg=self.bg_main)
        self.notebook.add(summary_frame, text=get_text("TAB_SUMMARY"))
        
        # 滚动容器
        canvas = tk.Canvas(summary_frame, bg=self.bg_main, highlightthickness=0)
        scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_main)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建对比表格
        self._create_summary_table(scrollable_frame)
        
        # 创建关键指标对比图
        if all(isinstance(r, ClassificationTrainingResult) for r in self.results):
            self._create_key_metrics_chart(scrollable_frame)
    
    def _create_summary_table(self, parent):
        """创建摘要对比表格"""
        tk.Label(parent, text=get_text("LABEL_SUMMARY_COMPARISON"), bg=self.bg_main, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 创建表格框架
        table_frame = tk.Frame(parent, bg=self.bg_card, highlightthickness=1,
                              highlightbackground=self.border)
        table_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        # 创建树形视图
        columns = ("exp_name", "model", "best_epoch", "best_val_acc", "final_val_acc", 
                  "training_time", "augmentation", "pretrained", "scheduler")
        
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=min(10, len(self.results) + 1))
        
        # 定义列
        tree.heading("exp_name", text=get_text("COL_EXP_NAME"))
        tree.heading("model", text=get_text("COL_MODEL"))
        tree.heading("best_epoch", text=get_text("COL_BEST_EPOCH"))
        tree.heading("best_val_acc", text=get_text("COL_BEST_VAL_ACC"))
        tree.heading("final_val_acc", text=get_text("COL_FINAL_VAL_ACC"))
        tree.heading("training_time", text=get_text("COL_TRAINING_TIME"))
        tree.heading("augmentation", text=get_text("COL_AUGMENTATION"))
        tree.heading("pretrained", text=get_text("COL_PRETRAINED"))
        tree.heading("scheduler", text=get_text("COL_SCHEDULER"))
        
        # 设置列宽
        tree.column("exp_name", width=120, anchor="w")
        tree.column("model", width=80, anchor="center")
        tree.column("best_epoch", width=80, anchor="center")
        tree.column("best_val_acc", width=100, anchor="center")
        tree.column("final_val_acc", width=100, anchor="center")
        tree.column("training_time", width=80, anchor="center")
        tree.column("augmentation", width=80, anchor="center")
        tree.column("pretrained", width=80, anchor="center")
        tree.column("scheduler", width=100, anchor="center")
        
        # 样式化
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background=self.bg_card, foreground=self.text_main,
                       fieldbackground=self.bg_card, borderwidth=0, font=('Consolas', 9))
        style.configure("Treeview.Heading", background=self.border, foreground=self.text_main,
                       relief="flat", font=('Consolas', 9, 'bold'))
        style.map("Treeview", background=[('selected', '#2d3440')])
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 添加数据
        for i, result in enumerate(self.results):
            exp_name = getattr(result, 'exp_name', f"实验{i+1}")
            
            # 获取模型名称
            model_name = result.config.get("model_name", "未知")
            
            # 获取最佳指标
            if isinstance(result, ClassificationTrainingResult):
                best_epoch = result.best_epoch
                best_val_acc = f"{result.best_val_acc:.2f}%"
                final_val_acc = f"{result.final_val_acc:.2f}%"
            else:
                best_epoch = "-"
                best_val_acc = "-"
                final_val_acc = "-"
            
            # 训练时间
            training_time = result.summary.get("training_time", "未知")
            
            # 能力使用
            capabilities = result.capabilities
            augmentation = "是" if capabilities.get("augmentation_used") else "否"
            pretrained = "是" if capabilities.get("pretrained_used") else "否"
            scheduler = capabilities.get("scheduler_used", "无")
            
            values = (
                exp_name,
                model_name,
                best_epoch,
                best_val_acc,
                final_val_acc,
                training_time,
                augmentation,
                pretrained,
                scheduler,
            )
            
            tree.insert("", "end", values=values)
        
        # 如果有多个结果，添加最佳表现标记
        if len(self.results) > 1 and all(isinstance(r, ClassificationTrainingResult) for r in self.results):
            # 找到最佳验证准确率
            best_acc_index = max(range(len(self.results)), 
                               key=lambda i: self.results[i].best_val_acc if isinstance(self.results[i], ClassificationTrainingResult) else 0)
            
            # 标记最佳结果
            for i, item in enumerate(tree.get_children()):
                if i == best_acc_index:
                    tree.item(item, tags=("best",))
            
            # 配置最佳标记样式
            tree.tag_configure("best", background="#2d3440")
    
    def _create_key_metrics_chart(self, parent):
        """创建关键指标对比图"""
        tk.Label(parent, text="关键指标对比图", bg=self.bg_main, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=(20, 5))
        
        # 创建图表容器
        chart_frame = tk.Frame(parent, bg=self.bg_card, highlightthickness=1,
                              highlightbackground=self.border)
        chart_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        # 创建Matplotlib图形
        fig = Figure(figsize=(12, 5), dpi=100, facecolor=self.bg_card)
        
        # 子图1：准确率对比
        ax1 = fig.add_subplot(121)
        ax1.set_facecolor(self.bg_card)
        
        # 子图2：训练时间对比
        ax2 = fig.add_subplot(122)
        ax2.set_facecolor(self.bg_card)
        
        fig.patch.set_facecolor(self.bg_card)
        
        # 准备数据
        exp_names = []
        best_val_accs = []
        final_val_accs = []
        training_times = []
        
        for i, result in enumerate(self.results):
            if isinstance(result, ClassificationTrainingResult):
                exp_name = getattr(result, 'exp_name', f"实验{i+1}")
                exp_names.append(exp_name)
                best_val_accs.append(result.best_val_acc)
                final_val_accs.append(result.final_val_acc)
                
                # 解析训练时间
                time_str = result.summary.get("training_time", "0秒")
                try:
                    if "小时" in time_str:
                        parts = time_str.split("小时")
                        hours = int(parts[0])
                        minutes_part = parts[1].split("分")[0] if "分" in parts[1] else "0"
                        minutes = int(minutes_part)
                        total_minutes = hours * 60 + minutes
                    elif "分" in time_str:
                        minutes = int(time_str.split("分")[0])
                        total_minutes = minutes
                    elif "秒" in time_str:
                        seconds = int(time_str.split("秒")[0])
                        total_minutes = seconds / 60
                    else:
                        total_minutes = 0
                    
                    training_times.append(total_minutes)
                except:
                    training_times.append(0)
        
        if exp_names:
            # 绘制准确率对比
            x = range(len(exp_names))
            width = 0.35
            
            bars1 = ax1.bar([i - width/2 for i in x], best_val_accs, width, 
                          label='最佳验证准确率', color=self.accent_green)
            bars2 = ax1.bar([i + width/2 for i in x], final_val_accs, width, 
                          label='最终验证准确率', color=self.accent_blue)
            
            ax1.set_xlabel('实验', color=self.text_sub, fontsize=10)
            ax1.set_ylabel('准确率 (%)', color=self.text_sub, fontsize=10)
            ax1.set_title('准确率对比', color=self.text_main, fontsize=12, pad=10)
            ax1.set_xticks(x)
            ax1.set_xticklabels(exp_names, color=self.text_sub, fontsize=9)
            ax1.tick_params(colors=self.text_sub)
            ax1.grid(True, alpha=0.2, color=self.border)
            ax1.legend(facecolor=self.bg_card, edgecolor=self.border, 
                      labelcolor=self.text_main, fontsize=9)
            
            # 在柱状图上添加数值
            for bar in bars1:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{height:.1f}%', ha='center', va='bottom', 
                        color=self.text_main, fontsize=8)
            
            for bar in bars2:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{height:.1f}%', ha='center', va='bottom', 
                        color=self.text_main, fontsize=8)
            
            # 绘制训练时间对比
            bars3 = ax2.bar(x, training_times, color=self.accent_yellow)
            
            ax2.set_xlabel('实验', color=self.text_sub, fontsize=10)
            ax2.set_ylabel('训练时间 (分钟)', color=self.text_sub, fontsize=10)
            ax2.set_title('训练时间对比', color=self.text_main, fontsize=12, pad=10)
            ax2.set_xticks(x)
            ax2.set_xticklabels(exp_names, color=self.text_sub, fontsize=9)
            ax2.tick_params(colors=self.text_sub)
            ax2.grid(True, alpha=0.2, color=self.border)
            
            # 在柱状图上添加数值
            for bar in bars3:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{height:.1f}', ha='center', va='bottom', 
                        color=self.text_main, fontsize=8)
            
            # 设置坐标轴颜色
            for ax in [ax1, ax2]:
                ax.spines['bottom'].set_color(self.border)
                ax.spines['top'].set_color(self.border)
                ax.spines['left'].set_color(self.border)
                ax.spines['right'].set_color(self.border)
            
            # 添加到画布
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
            # 保存引用
            self.figures.append(fig)
            self.canvases.append(canvas)
        else:
            tk.Label(chart_frame, text="没有足够的分类训练结果数据生成对比图", 
                    bg=self.bg_card, fg=self.text_sub, font=("Microsoft YaHei", 10)).pack(pady=20)
    
    def _build_curves_tab(self):
        """构建曲线对比标签页"""
        curves_frame = tk.Frame(self.notebook, bg=self.bg_main)
        self.notebook.add(curves_frame, text=get_text("TAB_CURVES"))
        
        # 检查是否有分类训练结果
        classification_results = [r for r in self.results if isinstance(r, ClassificationTrainingResult)]
        
        if len(classification_results) < 2:
            tk.Label(curves_frame, text="需要至少2个分类训练结果才能进行曲线对比", 
                    bg=self.bg_main, fg=self.text_sub, font=("Microsoft YaHei", 12)).pack(pady=50)
            return
        
        # 创建主容器（水平和垂直滚动）
        main_canvas = tk.Canvas(curves_frame, bg=self.bg_main, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(curves_frame, orient="vertical", command=main_canvas.yview)
        h_scrollbar = ttk.Scrollbar(curves_frame, orient="horizontal", command=main_canvas.xview)
        
        curves_container = tk.Frame(main_canvas, bg=self.bg_main)
        
        curves_container.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=curves_container, anchor="nw")
        main_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 布局
        main_canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        curves_frame.grid_rowconfigure(0, weight=1)
        curves_frame.grid_columnconfigure(0, weight=1)
        
        # 创建曲线对比图
        self._create_curve_comparisons(curves_container, classification_results)
    
    def _create_curve_comparisons(self, parent, results):
        """创建曲线对比图"""
        # 损失曲线对比
        self._create_single_curve_comparison(
            parent, results, 
            title="损失曲线对比",
            y_label="Loss",
            train_data_func=lambda r: r.train_loss_values,
            val_data_func=lambda r: r.val_loss_values,
            train_label="训练损失",
            val_label="验证损失",
            index=0,
            total_count=2
        )
        
        # 准确率曲线对比
        self._create_single_curve_comparison(
            parent, results,
            title="准确率曲线对比",
            y_label="Accuracy (%)",
            train_data_func=lambda r: r.train_acc_values,
            val_data_func=lambda r: r.val_acc_values,
            train_label="训练准确率",
            val_label="验证准确率",
            index=1,
            total_count=2
        )
    
    def _create_single_curve_comparison(self, parent, results, title, y_label, 
                                      train_data_func, val_data_func, 
                                      train_label, val_label, index, total_count):
        """创建单个曲线对比图"""
        frame = tk.Frame(parent, bg=self.bg_card, highlightthickness=1,
                        highlightbackground=self.border)
        
        # 根据图形数量决定布局
        if total_count <= 2:
            frame.pack(fill="both", expand=True, padx=10, pady=10)
        else:
            # 两列布局
            column = index % 2
            row = index // 2
            frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
            parent.grid_rowconfigure(row, weight=1)
            parent.grid_columnconfigure(column, weight=1)
        
        # 创建Matplotlib图形
        fig = Figure(figsize=(10, 5), dpi=100, facecolor=self.bg_card)
        ax = fig.add_subplot(111)
        
        # 设置颜色
        ax.set_facecolor(self.bg_card)
        fig.patch.set_facecolor(self.bg_card)
        
        # 绘制每个结果的曲线
        for i, result in enumerate(results):
            color = self.color_sequence[i % len(self.color_sequence)]
            exp_name = getattr(result, 'exp_name', f"实验{i+1}")
            
            # 训练数据
            train_data = train_data_func(result)
            if train_data:
                epochs = list(range(1, len(train_data) + 1))
                ax.plot(epochs, train_data, 
                       color=color, 
                       linewidth=2,
                       linestyle='-',
                       label=f"{exp_name} - {train_label}")
            
            # 验证数据（如果存在）
            val_data = val_data_func(result)
            if val_data and len(val_data) == len(train_data):
                ax.plot(epochs, val_data,
                       color=color,
                       linewidth=2,
                       linestyle='--',
                       label=f"{exp_name} - {val_label}")
        
        # 设置图形属性
        ax.set_title(title, color=self.text_main, fontsize=12, pad=10)
        ax.set_xlabel("Epoch", color=self.text_sub, fontsize=10)
        ax.set_ylabel(y_label, color=self.text_sub, fontsize=10)
        
        # 设置刻度颜色
        ax.tick_params(colors=self.text_sub)
        ax.grid(True, alpha=0.2, color=self.border)
        
        # 设置坐标轴颜色
        ax.spines['bottom'].set_color(self.border)
        ax.spines['top'].set_color(self.border)
        ax.spines['left'].set_color(self.border)
        ax.spines['right'].set_color(self.border)
        
        # 添加图例
        ax.legend(facecolor=self.bg_card, edgecolor=self.border, 
                 labelcolor=self.text_main, fontsize=9, ncol=2)
        
        # 添加到画布
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        # 保存引用
        self.figures.append(fig)
        self.canvases.append(canvas)
    
    def _build_details_tab(self):
        """构建详细数据标签页"""
        details_frame = tk.Frame(self.notebook, bg=self.bg_main)
        self.notebook.add(details_frame, text=get_text("TAB_DETAILS"))
        
        # 创建笔记本（嵌套标签页）
        inner_notebook = ttk.Notebook(details_frame)
        inner_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 样式化内部标签页
        style = ttk.Style()
        style.configure('inner.TNotebook', background=self.bg_main, borderwidth=0)
        style.configure('inner.TNotebook.Tab', background=self.bg_card, foreground=self.text_main,
                       padding=[8, 3], font=('Microsoft YaHei', 9))
        style.map('inner.TNotebook.Tab', background=[('selected', '#2d3440')], 
                 foreground=[('selected', self.accent_blue)])
        
        inner_notebook.configure(style='inner.TNotebook')
        
        # 为每个结果创建标签页
        for i, result in enumerate(self.results):
            exp_name = getattr(result, 'exp_name', f"实验{i+1}")
            tab_frame = tk.Frame(inner_notebook, bg=self.bg_main)
            inner_notebook.add(tab_frame, text=exp_name)
            
            self._create_result_details(tab_frame, result, exp_name)
    
    def _build_config_comparison_tab(self):
        """构建配置对比标签页"""
        if len(self.results) < 2:
            # 如果少于2个结果，不创建配置对比标签页
            return
        
        config_frame = tk.Frame(self.notebook, bg=self.bg_main)
        self.notebook.add(config_frame, text=get_text("TAB_CONFIG_COMPARISON"))
        
        # 导入配置对比器
        from core.config_comparator import get_config_comparator
        
        # 获取前两个结果的配置进行对比
        config_a = self.results[0].config
        config_b = self.results[1].config
        exp_name_a = getattr(self.results[0], 'exp_name', '实验A')
        exp_name_b = getattr(self.results[1], 'exp_name', '实验B')
        
        comparator = get_config_comparator()
        differences = comparator.compare_configs(config_a, config_b, exclude_fields=["name", "project"])
        summary = comparator.get_summary(config_a, config_b)
        
        # 主容器
        main_container = tk.Frame(config_frame, bg=self.bg_main)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部摘要
        summary_frame = tk.Frame(main_container, bg=self.bg_card, highlightthickness=1,
                                highlightbackground=self.border)
        summary_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(summary_frame, text=f"配置对比摘要: {exp_name_a} vs {exp_name_b}", 
                bg=self.bg_card, fg=self.text_main, font=("Microsoft YaHei", 11, "bold")).pack(
                anchor="w", padx=12, pady=(10, 5))
        
        summary_text = tk.Text(summary_frame, bg=self.bg_card, fg=self.text_main,
                              font=("Consolas", 9), wrap="word", height=4, relief="flat")
        summary_text.pack(fill="x", padx=12, pady=(0, 10))
        
        summary_info = (f"总字段数: {summary['total_fields']} | "
                       f"差异字段: {summary['different_fields']} | "
                       f"差异比例: {summary['different_percentage']:.1f}%")
        
        if summary['key_differences']:
            summary_info += f"\n关键差异: {', '.join(summary['key_differences'])}"
        
        summary_text.insert("1.0", summary_info)
        summary_text.config(state="disabled")
        
        # 配置差异表格
        table_frame = tk.Frame(main_container, bg=self.bg_card, highlightthickness=1,
                              highlightbackground=self.border)
        table_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        tk.Label(table_frame, text="详细配置差异", bg=self.bg_card, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 5))
        
        # 创建树形视图
        columns = ("field", "value_a", "value_b", "is_different")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        tree.heading("field", text=get_text("COL_FIELD_NAME"))
        tree.heading("value_a", text=get_text("COL_VALUE_A"))
        tree.heading("value_b", text=get_text("COL_VALUE_B"))
        tree.heading("is_different", text=get_text("COL_IS_DIFFERENT"))
        
        tree.column("field", width=120, anchor="w")
        tree.column("value_a", width=150, anchor="w")
        tree.column("value_b", width=150, anchor="w")
        tree.column("is_different", width=80, anchor="center")
        
        # 样式化
        style = ttk.Style()
        style.configure("Treeview", background=self.bg_card, foreground=self.text_main,
                       fieldbackground=self.bg_card, borderwidth=0, font=('Consolas', 9))
        style.configure("Treeview.Heading", background=self.border, foreground=self.text_main,
                       relief="flat", font=('Consolas', 9, 'bold'))
        style.map("Treeview", background=[('selected', '#2d3440')])
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=12, pady=(0, 10))
        scrollbar.pack(side="right", fill="y", padx=(0, 12), pady=(0, 10))
        
        # 添加数据
        for diff in differences:
            field = diff["field"]
            value_a = diff["value_a"]
            value_b = diff["value_b"]
            is_diff = "✓" if diff["is_different"] else ""
            
            tree.insert("", "end", values=(field, value_a, value_b, is_diff))
        
        # 复用按钮区域
        reuse_frame = tk.Frame(main_container, bg=self.bg_main)
        reuse_frame.pack(fill="x", pady=(0, 10))
        
        # 只有2个结果时显示复用按钮
        if len(self.results) == 2:
            btn_frame = tk.Frame(reuse_frame, bg=self.bg_main)
            btn_frame.pack()
            
            reuse_a_btn = tk.Button(btn_frame, text=get_text("BTN_REUSE_CONFIG_A"), 
                                   bg=self.accent_green, fg="white",
                                   font=("Microsoft YaHei", 10, "bold"), relief="flat",
                                   padx=15, pady=5,
                                   command=lambda: self._reuse_config(0))
            reuse_a_btn.pack(side="left", padx=(0, 10))
            
            reuse_b_btn = tk.Button(btn_frame, text=get_text("BTN_REUSE_CONFIG_B"),
                                   bg=self.accent_blue, fg="white",
                                   font=("Microsoft YaHei", 10, "bold"), relief="flat",
                                   padx=15, pady=5,
                                   command=lambda: self._reuse_config(1))
            reuse_b_btn.pack(side="left", padx=(0, 10))
            
            reuse_both_btn = tk.Button(btn_frame, text="对比后复用", 
                                      bg=self.accent_yellow, fg="white",
                                      font=("Microsoft YaHei", 10), relief="flat",
                                      padx=15, pady=5,
                                      command=self._reuse_config_comparison)
            reuse_both_btn.pack(side="left")
    
    def _create_result_details(self, parent, result, exp_name):
        """创建单个结果的详细数据"""
        # 滚动容器
        canvas = tk.Canvas(parent, bg=self.bg_main, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_main)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建配置信息表格
        self._create_config_table(scrollable_frame, result, exp_name)
        
        # 创建epoch数据表格（如果有）
        if result.epochs:
            self._create_epochs_table(scrollable_frame, result)
    
    def _create_config_table(self, parent, result, exp_name):
        """创建配置信息表格"""
        tk.Label(parent, text=f"{exp_name} - 训练配置", bg=self.bg_main, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 创建框架
        config_frame = tk.Frame(parent, bg=self.bg_card, highlightthickness=1,
                               highlightbackground=self.border)
        config_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        # 使用文本部件显示配置
        config_text = scrolledtext.ScrolledText(
            config_frame,
            bg=self.bg_card,
            fg=self.text_main,
            font=("Consolas", 9),
            wrap="word",
            height=12,
            relief="flat",
            padx=10,
            pady=10
        )
        config_text.pack(fill="both", expand=True)
        
        # 格式化配置为JSON
        config_json = json.dumps(result.config, indent=2, ensure_ascii=False)
        config_text.insert("1.0", config_json)
        config_text.config(state="disabled")
    
    def _create_epochs_table(self, parent, result):
        """创建epoch数据表格"""
        tk.Label(parent, text="训练历史 (每个epoch)", bg=self.bg_main, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 创建表格框架
        table_frame = tk.Frame(parent, bg=self.bg_card, highlightthickness=1,
                              highlightbackground=self.border)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        
        # 创建树形视图
        columns = ("epoch", "train_loss", "train_acc", "val_loss", "val_acc", "learning_rate")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        # 定义列
        tree.heading("epoch", text="Epoch")
        tree.heading("train_loss", text="训练损失")
        tree.heading("train_acc", text="训练准确率(%)")
        tree.heading("val_loss", text="验证损失")
        tree.heading("val_acc", text="验证准确率(%)")
        tree.heading("learning_rate", text="学习率")
        
        tree.column("epoch", width=60, anchor="center")
        tree.column("train_loss", width=80, anchor="center")
        tree.column("train_acc", width=100, anchor="center")
        tree.column("val_loss", width=80, anchor="center")
        tree.column("val_acc", width=100, anchor="center")
        tree.column("learning_rate", width=80, anchor="center")
        
        # 样式化
        style = ttk.Style()
        style.configure("Treeview", background=self.bg_card, foreground=self.text_main,
                       fieldbackground=self.bg_card, borderwidth=0, font=('Consolas', 9))
        style.configure("Treeview.Heading", background=self.border, foreground=self.text_main,
                       relief="flat", font=('Consolas', 9, 'bold'))
        style.map("Treeview", background=[('selected', '#2d3440')])
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 添加数据
        for epoch_data in result.epochs:
            values = (
                epoch_data.get("epoch", ""),
                f"{epoch_data.get('train_loss', 0):.4f}" if epoch_data.get('train_loss') is not None else "",
                f"{epoch_data.get('train_accuracy', 0):.2f}" if epoch_data.get('train_accuracy') is not None else "",
                f"{epoch_data.get('val_loss', 0):.4f}" if epoch_data.get('val_loss') is not None else "",
                f"{epoch_data.get('val_accuracy', 0):.2f}" if epoch_data.get('val_accuracy') is not None else "",
                f"{epoch_data.get('learning_rate', 0):.6f}" if epoch_data.get('learning_rate') is not None else "",
            )
            tree.insert("", "end", values=values)
    
    def _build_notes_comparison_tab(self):
        """构建批注对比标签页"""
        notes_frame = tk.Frame(self.notebook, bg=self.bg_main)
        self.notebook.add(notes_frame, text=get_text("TAB_NOTES_COMPARISON"))
        
        # 检查是否有批注数据
        results_with_notes = []
        for result in self.results:
            notes = getattr(result, 'notes', {})
            if notes:
                results_with_notes.append((result, notes))
        
        if len(results_with_notes) < 2:
            tk.Label(notes_frame, text=get_text("MSG_NO_NOTES"), bg=self.bg_main,
                    fg=self.text_sub, font=("Microsoft YaHei", 12)).pack(pady=50)
            return
        
        # 滚动容器
        canvas = tk.Canvas(notes_frame, bg=self.bg_main, highlightthickness=0)
        scrollbar = ttk.Scrollbar(notes_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_main)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建批注对比表格
        self._create_notes_comparison_table(scrollable_frame, results_with_notes)
    
    def _create_notes_comparison_table(self, parent, results_with_notes):
        """创建批注对比表格"""
        tk.Label(parent, text="实验批注对比", bg=self.bg_main, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 定义要对比的批注字段
        note_fields = [
            ("experiment_notes", get_text("LABEL_EXPERIMENT_NOTES")),
            ("change_description", get_text("LABEL_CHANGE_DESCRIPTION")),
            ("reason_for_retraining", get_text("LABEL_RETRAIN_REASON")),
            ("source_experiment", get_text("LABEL_SOURCE_EXPERIMENT")),
        ]
        
        # 为每个字段创建对比表格
        for field_name, field_label in note_fields:
            self._create_single_note_field_comparison(parent, results_with_notes, field_name, field_label)
    
    def _create_single_note_field_comparison(self, parent, results_with_notes, field_name, field_label):
        """创建单个批注字段的对比"""
        # 字段标题
        tk.Label(parent, text=field_label, bg=self.bg_main, fg=self.accent_blue,
                font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", padx=10, pady=(20, 5))
        
        # 表格框架
        table_frame = tk.Frame(parent, bg=self.bg_card, highlightthickness=1,
                              highlightbackground=self.border)
        table_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # 创建树形视图
        columns = ("exp_name", "value", "is_empty")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                           height=min(5, len(results_with_notes) + 1))
        
        tree.heading("exp_name", text="实验名称")
        tree.heading("value", text="内容")
        tree.heading("is_empty", text="是否为空")
        
        tree.column("exp_name", width=100, anchor="w")
        tree.column("value", width=300, anchor="w")
        tree.column("is_empty", width=60, anchor="center")
        
        # 样式化
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background=self.bg_card, foreground=self.text_main,
                       fieldbackground=self.bg_card, borderwidth=0, font=('Consolas', 9))
        style.configure("Treeview.Heading", background=self.border, foreground=self.text_main,
                       relief="flat", font=('Consolas', 9, 'bold'))
        style.map("Treeview", background=[('selected', '#2d3440')])
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 添加数据
        all_values_same = True
        first_value = None
        
        for i, (result, notes) in enumerate(results_with_notes):
            exp_name = getattr(result, 'exp_name', f"实验{i+1}")
            value = notes.get(field_name, "")
            is_empty = "是" if not value else "否"
            
            # 检查所有值是否相同
            if first_value is None:
                first_value = value
            elif value != first_value:
                all_values_same = False
            
            # 显示内容（截断过长的文本）
            display_value = value
            if len(display_value) > 100:
                display_value = display_value[:100] + "..."
            
            tree.insert("", "end", values=(exp_name, display_value, is_empty))
        
        # 如果所有值都相同，添加提示
        if all_values_same and first_value:
            same_frame = tk.Frame(parent, bg=self.bg_main)
            same_frame.pack(fill="x", padx=10, pady=(0, 5))
            
            tk.Label(same_frame, text="✓ 所有实验的批注内容相同", bg=self.bg_main, fg=self.accent_green,
                    font=("Microsoft YaHei", 9)).pack(anchor="w")
        
        # 如果有差异，显示差异统计
        elif not all_values_same:
            diff_frame = tk.Frame(parent, bg=self.bg_main)
            diff_frame.pack(fill="x", padx=10, pady=(0, 5))
            
            empty_count = sum(1 for _, notes in results_with_notes if not notes.get(field_name, ""))
            filled_count = len(results_with_notes) - empty_count
            
            diff_text = f"差异统计: {filled_count}个有内容, {empty_count}个为空"
            tk.Label(diff_frame, text=diff_text, bg=self.bg_main, fg=self.accent_yellow,
                    font=("Microsoft YaHei", 9)).pack(anchor="w")
    
    def _build_bottom_bar(self, parent):
        """构建底部按钮栏"""
        bottom_frame = tk.Frame(parent, bg=self.bg_main, height=60)
        bottom_frame.pack(fill="x", pady=(14, 0))
        bottom_frame.pack_propagate(False)
        
        # 左侧按钮
        left_frame = tk.Frame(bottom_frame, bg=self.bg_main)
        left_frame.pack(side="left", padx=20)
        
        export_btn = tk.Button(
            left_frame,
            text=get_text("BTN_EXPORT_COMPARISON"),
            bg=self.border,
            fg=self.text_main,
            font=("Microsoft YaHei", 10),
            relief="flat",
            padx=15,
            pady=5,
            command=self._export_comparison
        )
        export_btn.pack(side="left", padx=5)
        
        reuse_btn = tk.Button(
            left_frame,
            text=get_text("BTN_REUSE_CONFIG"),
            bg=self.accent_green,
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            relief="flat",
            padx=15,
            pady=5,
            command=lambda: self._reuse_config(0) if len(self.results) > 0 else None
        )
        reuse_btn.pack(side="left", padx=5)
        
        # 右侧关闭按钮
        right_frame = tk.Frame(bottom_frame, bg=self.bg_main)
        right_frame.pack(side="right", padx=20)
        
        close_btn = tk.Button(
            right_frame,
            text=get_text("BTN_CLOSE"),
            bg=self.accent_red,
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            relief="flat",
            padx=25,
            pady=6,
            command=self.destroy
        )
        close_btn.pack(side="right", padx=5)
    
    def _show_error(self, message):
        """显示错误消息"""
        error_label = tk.Label(self, text=message, bg=self.bg_main, fg=self.accent_red,
                              font=("Microsoft YaHei", 12, "bold"))
        error_label.pack(pady=50)
        
        close_btn = tk.Button(
            self,
            text=get_text("BTN_CLOSE"),
            bg=self.accent_red,
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            relief="flat",
            padx=25,
            pady=6,
            command=self.destroy
        )
        close_btn.pack(pady=20)
    
    def _export_comparison(self):
        """导出对比报告"""
        # 实现导出对比报告的逻辑
        messagebox.showinfo("提示", "导出对比报告功能暂未实现")
    
    def _reuse_config(self, result_index):
        """复用指定索引的结果配置"""
        if result_index < 0 or result_index >= len(self.results):
            messagebox.showerror("错误", "无效的结果索引")
            return
        
        try:
            result = self.results[result_index]
            exp_name = getattr(result, 'exp_name', f"实验{result_index+1}")
            
            # 导入配置对比器
            from core.config_comparator import get_config_comparator
            comparator = get_config_comparator()
            
            # 准备复用配置
            reused_config = comparator.prepare_config_for_reuse(result.config)
            
            # 获取训练中心窗口
            training_center_window = None
            
            # 尝试找到已存在的训练中心窗口
            if hasattr(self.master, '_training_center_window'):
                training_center_window = self.master._training_center_window
            elif hasattr(self.master, 'root') and hasattr(self.master.root, '_training_center_window'):
                training_center_window = self.master.root._training_center_window
            else:
                # 如果不存在，尝试导入并打开
                from ui.training_center_window import open_training_center
                training_center_window = open_training_center(self.master, reused_config)
                if training_center_window:
                    messagebox.showinfo("提示", get_text("MSG_REUSE_SUCCESS"))
                    return
            
            # 更新现有训练中心窗口的配置
            if training_center_window and hasattr(training_center_window, 'current_config'):
                training_center_window.current_config = reused_config
                training_center_window._load_current_config()
                training_center_window.deiconify()  # 显示窗口
                training_center_window.focus_force()
                
                messagebox.showinfo("提示", get_text("MSG_REUSE_SUCCESS"))
            else:
                messagebox.showerror("错误", "无法找到训练中心窗口")
                
        except Exception as e:
            messagebox.showerror("错误", f"{get_text('MSG_REUSE_ERROR')}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _reuse_config_comparison(self):
        """复用配置对比结果（打开两个训练中心窗口）"""
        if len(self.results) < 2:
            messagebox.showwarning("提示", "需要至少2个结果进行对比复用")
            return
        
        try:
            from core.config_comparator import get_config_comparator
            from ui.training_center_window import open_training_center
            
            comparator = get_config_comparator()
            
            # 复用第一个配置
            config_a = self.results[0].config
            reused_config_a = comparator.prepare_config_for_reuse(config_a, suffix="对比A")
            
            # 复用第二个配置  
            config_b = self.results[1].config
            reused_config_b = comparator.prepare_config_for_reuse(config_b, suffix="对比B")
            
            # 打开两个训练中心窗口
            win_a = open_training_center(self.master, reused_config_a)
            win_b = open_training_center(self.master, reused_config_b)
            
            if win_a and win_b:
                # 设置窗口位置，避免重叠
                win_a.geometry("1000x700+100+100")
                win_b.geometry("1000x700+1120+100")
                
                messagebox.showinfo("提示", "已打开两个训练中心窗口进行配置对比")
            else:
                messagebox.showwarning("提示", "无法打开训练中心窗口")
                
        except Exception as e:
            messagebox.showerror("错误", f"复用配置对比失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def destroy(self):
        """销毁窗口，清理资源"""
        # 清理matplotlib图形
        for fig in self.figures:
            plt.close(fig)
        super().destroy()


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.withdraw()
    
    # 创建一些测试结果路径
    test_paths = []
    test_names = []
    
    for i in range(3):
        test_paths.append(f"test_log_{i+1}.json")
        test_names.append(f"测试实验{i+1}")
    
    win = TrainingComparisonWindow(root, test_paths, test_names)
    root.mainloop()