"""
训练结果查看窗口 - 显示训练结果摘要和曲线
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import os
import matplotlib
matplotlib.use('TkAgg')  # 设置后端
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.training_result_analyzer import get_result_analyzer, ClassificationTrainingResult, TrainingResult
from core.closed_loop_manager import ClosedLoopManager, BadCaseSource


def get_text(key):
    """根据当前语言配置获取文本"""
    texts = {
        "TITLE_TRAINING_RESULT": "训练结果分析",
        "LABEL_SUMMARY": "训练摘要",
        "LABEL_CURVES": "训练曲线",
        "LABEL_TRAIN_LOSS": "训练损失",
        "LABEL_VAL_LOSS": "验证损失",
        "LABEL_TRAIN_ACC": "训练准确率",
        "LABEL_VAL_ACC": "验证准确率",
        "LABEL_LEARNING_RATE": "学习率",
        "BTN_CLOSE": "关闭",
        "BTN_SAVE_CURVES": "保存曲线图",
        "BTN_EXPORT_REPORT": "导出报告",
        "MSG_NO_RESULT": "未加载训练结果",
        "MSG_LOAD_FAILED": "加载训练结果失败",
        "MSG_NO_CURVES": "没有足够的数据生成曲线",
        "TAB_SUMMARY": "摘要",
        "TAB_CURVES": "曲线",
        "TAB_DETAILS": "详细数据",
        "TAB_NOTES": "实验批注",
        "LABEL_EXPERIMENT_NOTES": "实验备注",
        "LABEL_CHANGE_DESCRIPTION": "改动说明",
        "LABEL_RETRAIN_REASON": "重新训练原因",
        "LABEL_SOURCE_EXPERIMENT": "来源实验",
        "BTN_SAVE_NOTES": "保存批注",
        "BTN_ADD_TO_CLOSED_LOOP": "添加到闭环修正",
        "MSG_SAVE_SUCCESS": "批注保存成功",
        "MSG_SAVE_ERROR": "批注保存失败",
    }
    return texts.get(key, key)


class TrainingResultWindow(tk.Toplevel):
    """训练结果查看窗口"""
    
    def __init__(self, master, log_path=None, result=None):
        super().__init__(master)
        self.master = master
        
        self.title(get_text("TITLE_TRAINING_RESULT"))
        self.geometry("1200x800")
        self.minsize(1000, 600)
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
        
        # 结果数据
        self.log_path = log_path
        self.result = result
        self.analyzer = get_result_analyzer()
        
        # 图形相关
        self.figures = []
        self.canvases = []
        
        # 如果提供了日志路径但未提供结果，则加载结果
        if self.log_path and not self.result:
            self.result = self.analyzer.load_result(self.log_path)
        
        # 构建UI
        self._build_ui()
        
        # 如果加载失败，显示错误
        if not self.result:
            self._show_error(get_text("MSG_LOAD_FAILED"))
    
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
        self._build_notes_tab()
        
        # 底部按钮栏
        self._build_bottom_bar(main_container)
    
    def _build_top_bar(self, parent):
        """构建顶部信息栏"""
        top_frame = tk.Frame(parent, bg=self.bg_card, height=60, highlightthickness=1, 
                           highlightbackground=self.border)
        top_frame.pack(fill="x", pady=(0, 14))
        top_frame.pack_propagate(False)
        
        if self.result:
            # 显示基本信息
            info_text = f"{self.result.trainer_id.upper()} 训练结果"
            if self.result.config.get("model_name"):
                info_text += f" | 模型: {self.result.config['model_name']}"
            if self.result.summary.get("training_time"):
                info_text += f" | 训练时间: {self.result.summary['training_time']}"
            
            tk.Label(top_frame, text=info_text, bg=self.bg_card, fg=self.text_main,
                    font=("Microsoft YaHei", 12, "bold")).pack(side="left", padx=20, pady=10)
            
            # 显示结果文件路径
            path_text = f"结果文件: {os.path.basename(self.result.log_path)}"
            tk.Label(top_frame, text=path_text, bg=self.bg_card, fg=self.text_sub,
                    font=("Consolas", 9)).pack(side="right", padx=20, pady=10)
        else:
            tk.Label(top_frame, text=get_text("MSG_NO_RESULT"), bg=self.bg_card, fg=self.accent_red,
                    font=("Microsoft YaHei", 12, "bold")).pack(padx=20, pady=10)
    
    def _build_summary_tab(self):
        """构建摘要标签页"""
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
        
        # 显示摘要文本
        if self.result:
            summary_text = self.analyzer.get_result_summary_text(self.result)
            
            # 创建文本区域
            text_widget = scrolledtext.ScrolledText(
                scrollable_frame,
                bg=self.bg_card,
                fg=self.text_main,
                font=("Consolas", 10),
                wrap="word",
                height=30,
                width=100,
                relief="flat",
                padx=15,
                pady=15
            )
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            text_widget.insert("1.0", summary_text)
            text_widget.config(state="disabled")
        else:
            tk.Label(scrollable_frame, text=get_text("MSG_NO_RESULT"), bg=self.bg_main,
                    fg=self.text_sub, font=("Microsoft YaHei", 12)).pack(pady=50)
    
    def _build_curves_tab(self):
        """构建曲线标签页"""
        curves_frame = tk.Frame(self.notebook, bg=self.bg_main)
        self.notebook.add(curves_frame, text=get_text("TAB_CURVES"))
        
        if not self.result or not isinstance(self.result, ClassificationTrainingResult):
            # 不支持或没有数据
            tk.Label(curves_frame, text=get_text("MSG_NO_CURVES"), bg=self.bg_main,
                    fg=self.text_sub, font=("Microsoft YaHei", 12)).pack(pady=50)
            return
        
        # 创建图形容器
        self._create_curves(curves_frame)
    
    def _create_curves(self, parent):
        """创建训练曲线图"""
        result = self.result
        
        # 检查是否有足够的数据
        if len(result.train_loss_values) < 2:
            tk.Label(parent, text="训练数据不足，无法生成曲线", bg=self.bg_main,
                    fg=self.text_sub, font=("Microsoft YaHei", 12)).pack(pady=50)
            return
        
        # 创建主容器（水平和垂直滚动）
        main_canvas = tk.Canvas(parent, bg=self.bg_main, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=main_canvas.yview)
        h_scrollbar = ttk.Scrollbar(parent, orient="horizontal", command=main_canvas.xview)
        
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
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # 创建多个图形（损失、准确率、学习率）
        curves_data = [
            {
                "title": get_text("LABEL_TRAIN_LOSS"),
                "y_data": result.train_loss_values,
                "y_label": "Loss",
                "color": self.accent_red,
                "has_val": len(result.val_loss_values) > 0,
                "val_data": result.val_loss_values,
                "val_label": get_text("LABEL_VAL_LOSS"),
                "val_color": self.accent_yellow
            },
            {
                "title": get_text("LABEL_TRAIN_ACC"),
                "y_data": result.train_acc_values,
                "y_label": "Accuracy (%)",
                "color": self.accent_green,
                "has_val": len(result.val_acc_values) > 0,
                "val_data": result.val_acc_values,
                "val_label": get_text("LABEL_VAL_ACC"),
                "val_color": self.accent_blue
            }
        ]
        
        # 如果有学习率数据，也显示
        if len(result.learning_rate_values) > 0 and any(lr > 0 for lr in result.learning_rate_values):
            curves_data.append({
                "title": get_text("LABEL_LEARNING_RATE"),
                "y_data": result.learning_rate_values,
                "y_label": "Learning Rate",
                "color": "#a855f7",  # 紫色
                "has_val": False
            })
        
        # 创建图形
        for i, curve_info in enumerate(curves_data):
            self._create_single_curve(curves_container, curve_info, i, len(curves_data))
    
    def _create_single_curve(self, parent, curve_info, index, total_count):
        """创建单个曲线图"""
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
        fig = Figure(figsize=(8, 4), dpi=100, facecolor=self.bg_card)
        ax = fig.add_subplot(111)
        
        # 设置颜色
        ax.set_facecolor(self.bg_card)
        fig.patch.set_facecolor(self.bg_card)
        
        # 绘制训练曲线
        epochs = list(range(1, len(curve_info["y_data"]) + 1))
        ax.plot(epochs, curve_info["y_data"], 
                color=curve_info["color"], 
                linewidth=2,
                label=curve_info.get("val_label", curve_info["title"]))
        
        # 如果有验证曲线，也绘制
        if curve_info.get("has_val") and curve_info.get("val_data"):
            ax.plot(epochs, curve_info["val_data"], 
                    color=curve_info["val_color"], 
                    linewidth=2,
                    label=curve_info["val_label"])
        
        # 设置图形属性
        ax.set_title(curve_info["title"], color=self.text_main, fontsize=12, pad=10)
        ax.set_xlabel("Epoch", color=self.text_sub, fontsize=10)
        ax.set_ylabel(curve_info["y_label"], color=self.text_sub, fontsize=10)
        
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
                 labelcolor=self.text_main, fontsize=9)
        
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
        
        if not self.result:
            tk.Label(details_frame, text=get_text("MSG_NO_RESULT"), bg=self.bg_main,
                    fg=self.text_sub, font=("Microsoft YaHei", 12)).pack(pady=50)
            return
        
        # 创建树形视图显示详细数据
        self._create_details_tree(details_frame)
    
    def _create_details_tree(self, parent):
        """创建详细数据树形视图"""
        # 创建滚动容器
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
        self._create_config_table(scrollable_frame)
        
        # 创建epoch数据表格（如果有）
        if self.result.epochs:
            self._create_epochs_table(scrollable_frame)
    
    def _create_config_table(self, parent):
        """创建配置信息表格"""
        tk.Label(parent, text="训练配置", bg=self.bg_main, fg=self.text_main,
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
            height=10,
            relief="flat",
            padx=10,
            pady=10
        )
        config_text.pack(fill="both", expand=True)
        
        # 格式化配置为JSON
        config_json = json.dumps(self.result.config, indent=2, ensure_ascii=False)
        config_text.insert("1.0", config_json)
        config_text.config(state="disabled")
    
    def _create_epochs_table(self, parent):
        """创建epoch数据表格"""
        tk.Label(parent, text="训练历史 (每个epoch)", bg=self.bg_main, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 创建表格框架
        table_frame = tk.Frame(parent, bg=self.bg_card, highlightthickness=1,
                              highlightbackground=self.border)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        
        # 创建树形视图
        columns = ("epoch", "train_loss", "train_acc", "val_loss", "val_acc", "learning_rate")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
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
        for epoch_data in self.result.epochs:
            values = (
                epoch_data.get("epoch", ""),
                f"{epoch_data.get('train_loss', 0):.4f}" if epoch_data.get('train_loss') is not None else "",
                f"{epoch_data.get('train_accuracy', 0):.2f}" if epoch_data.get('train_accuracy') is not None else "",
                f"{epoch_data.get('val_loss', 0):.4f}" if epoch_data.get('val_loss') is not None else "",
                f"{epoch_data.get('val_accuracy', 0):.2f}" if epoch_data.get('val_accuracy') is not None else "",
                f"{epoch_data.get('learning_rate', 0):.6f}" if epoch_data.get('learning_rate') is not None else "",
            )
            tree.insert("", "end", values=values)
    
    def _build_bottom_bar(self, parent):
        """构建底部按钮栏"""
        bottom_frame = tk.Frame(parent, bg=self.bg_main, height=60)
        bottom_frame.pack(fill="x", pady=(14, 0))
        bottom_frame.pack_propagate(False)
        
        # 左侧按钮
        left_frame = tk.Frame(bottom_frame, bg=self.bg_main)
        left_frame.pack(side="left", padx=20)
        
        if self.result and isinstance(self.result, ClassificationTrainingResult):
            # 保存曲线按钮
            save_btn = tk.Button(
                left_frame,
                text=get_text("BTN_SAVE_CURVES"),
                bg=self.border,
                fg=self.text_main,
                font=("Microsoft YaHei", 10),
                relief="flat",
                padx=15,
                pady=5,
                command=self._save_curves
            )
            save_btn.pack(side="left", padx=5)
            
            # 导出报告按钮
            export_btn = tk.Button(
                left_frame,
                text=get_text("BTN_EXPORT_REPORT"),
                bg=self.border,
                fg=self.text_main,
                font=("Microsoft YaHei", 10),
                relief="flat",
                padx=15,
                pady=5,
                command=self._export_report
            )
            export_btn.pack(side="left", padx=5)
            
            # 添加到闭环修正按钮
            add_to_closed_loop_btn = tk.Button(
                left_frame,
                text=get_text("BTN_ADD_TO_CLOSED_LOOP"),
                bg=self.accent_yellow,
                fg=self.text_main,
                font=("Microsoft YaHei", 10),
                relief="flat",
                padx=15,
                pady=5,
                command=self._add_to_closed_loop
            )
            add_to_closed_loop_btn.pack(side="left", padx=5)
        
        # 右侧关闭按钮
        right_frame = tk.Frame(bottom_frame, bg=self.bg_main)
        right_frame.pack(side="right", padx=20)
        
        close_btn = tk.Button(
            right_frame,
            text=get_text("BTN_CLOSE"),
            bg=self.accent_red,
            fg=self.text_main,
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
            fg=self.text_main,
            font=("Microsoft YaHei", 10, "bold"),
            relief="flat",
            padx=25,
            pady=6,
            command=self.destroy
        )
        close_btn.pack(pady=20)
    
    def _build_notes_tab(self):
        """构建实验批注标签页"""
        notes_frame = tk.Frame(self.notebook, bg=self.bg_main)
        self.notebook.add(notes_frame, text=get_text("TAB_NOTES"))
        
        if not self.result:
            tk.Label(notes_frame, text=get_text("MSG_NO_RESULT"), bg=self.bg_main,
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
        
        # 创建批注表单
        self._create_notes_form(scrollable_frame)
    
    def _create_notes_form(self, parent):
        """创建批注表单"""
        # 获取批注数据
        notes = getattr(self.result, 'notes', {})
        
        # 创建表单容器
        form_frame = tk.Frame(parent, bg=self.bg_card, highlightthickness=1,
                             highlightbackground=self.border)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题
        tk.Label(form_frame, text="实验批注", bg=self.bg_card, fg=self.text_main,
                font=("Microsoft YaHei", 12, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # 创建文本输入字段
        self.notes_entries = {}
        
        # 实验备注
        self._create_text_field(form_frame, "experiment_notes", 
                               get_text("LABEL_EXPERIMENT_NOTES"),
                               notes.get("experiment_notes", ""),
                               height=6)
        
        # 改动说明
        self._create_text_field(form_frame, "change_description",
                               get_text("LABEL_CHANGE_DESCRIPTION"),
                               notes.get("change_description", ""),
                               height=4)
        
        # 重新训练原因
        self._create_text_field(form_frame, "reason_for_retraining",
                               get_text("LABEL_RETRAIN_REASON"),
                               notes.get("reason_for_retraining", ""),
                               height=4)
        
        # 来源实验（只读）
        source_info = notes.get("source_experiment", "")
        if source_info:
            self._create_readonly_field(form_frame, "source_experiment",
                                      get_text("LABEL_SOURCE_EXPERIMENT"),
                                      os.path.basename(source_info))
        
        # 保存按钮
        save_frame = tk.Frame(form_frame, bg=self.bg_card)
        save_frame.pack(fill="x", padx=15, pady=(20, 15))
        
        save_btn = tk.Button(
            save_frame,
            text=get_text("BTN_SAVE_NOTES"),
            bg=self.accent_green,
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            command=self._save_notes
        )
        save_btn.pack(side="right")
    
    def _create_text_field(self, parent, field_name, label_text, default_value, height=4):
        """创建文本输入字段"""
        field_frame = tk.Frame(parent, bg=self.bg_card)
        field_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 标签
        tk.Label(field_frame, text=label_text, bg=self.bg_card, fg=self.text_main,
                font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # 文本输入框
        text_widget = scrolledtext.ScrolledText(
            field_frame,
            bg="#1b2028",
            fg=self.text_main,
            font=("Microsoft YaHei", 9),
            wrap="word",
            height=height,
            relief="flat",
            padx=8,
            pady=8
        )
        text_widget.pack(fill="x")
        text_widget.insert("1.0", default_value)
        
        # 保存引用
        self.notes_entries[field_name] = text_widget
    
    def _create_readonly_field(self, parent, field_name, label_text, value):
        """创建只读字段"""
        field_frame = tk.Frame(parent, bg=self.bg_card)
        field_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 标签
        tk.Label(field_frame, text=label_text, bg=self.bg_card, fg=self.text_main,
                font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # 值显示
        value_frame = tk.Frame(field_frame, bg="#1b2028", height=40)
        value_frame.pack(fill="x")
        value_frame.pack_propagate(False)
        
        tk.Label(value_frame, text=value, bg="#1b2028", fg=self.text_sub,
                font=("Consolas", 9), anchor="w", justify="left").pack(fill="both", padx=8, pady=8)
        
        # 保存引用
        self.notes_entries[field_name] = value_frame
    
    def _save_notes(self):
        """保存批注"""
        try:
            # 收集表单数据
            new_notes = {}
            
            for field_name, widget in self.notes_entries.items():
                if isinstance(widget, scrolledtext.ScrolledText):
                    # 文本输入框
                    value = widget.get("1.0", tk.END).strip()
                    if value:
                        new_notes[field_name] = value
                elif field_name == "source_experiment":
                    # 只读字段，从原批注中获取
                    original_notes = getattr(self.result, 'notes', {})
                    if "source_experiment" in original_notes:
                        new_notes[field_name] = original_notes["source_experiment"]
            
            # 保存到训练日志文件
            if new_notes:
                # 使用分析器的保存方法
                success = self.analyzer.save_notes(self.log_path, new_notes)
                
                if success:
                    # 更新内存中的结果对象
                    if hasattr(self.result, 'notes'):
                        self.result.notes.update(new_notes)
                    else:
                        self.result.notes = new_notes
                    
                    # 显示成功消息
                    from tkinter import messagebox
                    messagebox.showinfo("成功", get_text("MSG_SAVE_SUCCESS"))
                else:
                    from tkinter import messagebox
                    messagebox.showerror("错误", "保存批注失败，请查看控制台输出")
            else:
                # 没有有效数据
                from tkinter import messagebox
                messagebox.showinfo("提示", "没有需要保存的批注数据")
                
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"{get_text('MSG_SAVE_ERROR')}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _save_curves(self):
        """保存曲线图"""
        # 实现保存曲线的逻辑
        print("保存曲线图功能暂未实现")
    
    def _export_report(self):
        """导出报告"""
        # 实现导出报告的逻辑
        print("导出报告功能暂未实现")
    
    def _add_to_closed_loop(self):
        """添加到闭环修正"""
        if not self.result:
            from tkinter import messagebox
            messagebox.showwarning("警告", "没有训练结果")
            return
        
        # 创建闭环管理器实例
        manager = ClosedLoopManager()
        
        # 生成问题摘要
        experiment_name = self.result.config.get("name", "未知实验")
        best_val_acc = getattr(self.result, 'best_val_acc', 0.0)
        problem_summary = f"训练结果问题 - {experiment_name} (最佳验证准确率: {best_val_acc:.2f}%)"
        
        # 尝试从结果中提取图片名（如果有）
        image_name = "training_result"
        if hasattr(self.result, 'log_path'):
            image_name = os.path.basename(self.result.log_path)
        
        # 添加bad case
        success, message = manager.add_bad_case(
            image_name=image_name,
            source_type=BadCaseSource.TRAINING_RESULT,
            problem_summary=problem_summary,
            issue_type="训练结果问题",
            class_name="",  # 暂时留空
            confidence=0.0,
            file_path=self.result.log_path if hasattr(self.result, 'log_path') else "",
            label_path="",
            resolution_note=f"来自训练结果: {experiment_name}"
        )
        
        from tkinter import messagebox
        if success:
            messagebox.showinfo("成功", f"已添加到闭环修正中心\n{message}")
        else:
            messagebox.showerror("错误", f"添加失败: {message}")
    
    def destroy(self):
        """销毁窗口，清理资源"""
        # 清理matplotlib图形
        for fig in self.figures:
            plt.close(fig)
        super().destroy()