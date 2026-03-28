"""
训练历史结果窗口 - 显示历史训练结果列表，支持选择和对比
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
from datetime import datetime

from core.training_result_analyzer import get_result_analyzer


def get_text(key):
    """根据当前语言配置获取文本"""
    texts = {
        "TITLE_TRAINING_HISTORY": "训练历史结果",
        "LABEL_TRAINER": "训练器",
        "LABEL_RESULTS": "结果列表",
        "LABEL_SELECTED": "已选中",
        "LABEL_DETAILS": "详细信息",
        "BTN_REFRESH": "刷新列表",
        "BTN_VIEW_SINGLE": "查看单个结果",
        "BTN_COMPARE": "对比选中结果",
        "BTN_CLOSE": "关闭",
        "BTN_SELECT_ALL": "全选",
        "BTN_CLEAR_SELECTION": "清空选择",
        "COL_EXP_NAME": "实验名称",
        "COL_TIMESTAMP": "训练时间",
        "COL_MODEL": "模型",
        "COL_BEST_EPOCH": "最佳轮数",
        "COL_BEST_VAL_ACC": "最佳验证准确率",
        "COL_FINAL_VAL_ACC": "最终验证准确率",
        "COL_TAGS": "标签",
        "COL_FAVORITE": "收藏",
        "COL_IMPORTANT": "重要",
        "COL_PATH": "文件路径",
        "MSG_NO_RESULTS": "未找到训练结果",
        "MSG_SELECT_ONE": "请选择一个结果",
        "MSG_SELECT_TWO": "请选择两个结果进行对比",
        "MSG_TRAINER_NOT_SUPPORTED": "此训练器暂不支持历史结果查看",
        "BTN_REUSE_CONFIG": "复用配置",
        "MSG_REUSE_SUCCESS": "配置已复制到训练中心",
        "MSG_REUSE_ERROR": "复用配置失败",
        "MSG_REUSE_SELECT_ONE": "请选择一个结果进行配置复用",
        "BTN_RETRAIN": "一键再训练",
        "MSG_RETRAIN_SUCCESS": "再训练配置已准备",
        "MSG_RETRAIN_ERROR": "再训练配置失败",
        "MSG_RETRAIN_SELECT_ONE": "请选择一个结果进行再训练",
        "LABEL_RETRAIN_REASON": "重新训练原因",
        "LABEL_SORT_BY": "排序方式",
        "SORT_TIME_DESC": "时间（最新）",
        "SORT_TIME_ASC": "时间（最旧）",
        "SORT_BEST_VAL_ACC_DESC": "最佳准确率（高→低）",
        "SORT_BEST_VAL_ACC_ASC": "最佳准确率（低→高）",
        "SORT_FINAL_VAL_ACC_DESC": "最终准确率（高→低）",
        "SORT_FINAL_VAL_ACC_ASC": "最终准确率（低→高）",
        "SORT_BEST_EPOCH_DESC": "最佳轮数（高→低）",
        "SORT_BEST_EPOCH_ASC": "最佳轮数（低→高）",
        "LABEL_GROUP_VIEW": "分组视图",
        "VIEW_ALL": "全部实验",
        "VIEW_FAVORITES": "收藏实验",
        "VIEW_IMPORTANT": "重要实验",
        "VIEW_BY_TAGS": "按标签查看",
        "VIEW_BY_MODEL": "按模型查看",
        "LABEL_TAG_FILTER": "标签筛选",
        "LABEL_MODEL_FILTER": "模型筛选",
        "BTN_BATCH_OPERATIONS": "批量操作",
        "BATCH_ADD_TAGS": "批量加标签",
        "BATCH_FAVORITE": "批量收藏",
        "BATCH_UNFAVORITE": "批量取消收藏",
        "BATCH_IMPORTANT": "批量标重要",
        "BATCH_UNIMPORTANT": "批量取消重要",
        "BATCH_ARCHIVE": "批量归档",
        "BATCH_EXPORT": "批量导出",
        "MSG_SELECT_FOR_BATCH": "请先选择要操作的结果",
        "MSG_BATCH_SUCCESS": "批量操作成功",
        "MSG_BATCH_ERROR": "批量操作失败",
        "LABEL_ADD_TAGS": "添加标签",
        "LABEL_REMOVE_TAGS": "移除标签",
        "BTN_APPLY_TAGS": "应用标签",
        "LABEL_EXPORT_FORMAT": "导出格式",
        "FORMAT_TXT": "文本文件 (.txt)",
        "FORMAT_JSON": "JSON文件 (.json)",
        "FORMAT_CSV": "CSV文件 (.csv)",
        "BTN_EXPORT": "导出",
        "MSG_EXPORT_SUCCESS": "导出成功",
        "MSG_EXPORT_ERROR": "导出失败",
    }
    return texts.get(key, key)


class TrainingHistoryWindow(tk.Toplevel):
    """训练历史结果窗口"""
    
    def __init__(self, master, trainer_id=None):
        super().__init__(master)
        self.master = master
        
        self.title(get_text("TITLE_TRAINING_HISTORY"))
        self.geometry("1400x800")
        self.minsize(1200, 600)
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
        self.trainer_id = trainer_id
        self.results = []
        self.selected_indices = set()  # 选中的行索引
        self.all_loaded_results = []  # 所有加载的结果对象（缓存）
        self.displayed_items = []  # 当前显示的项目列表 [(result, result_obj), ...]
        self.id_to_display_index = {}  # 树形视图ID到displayed_items索引的映射
        self.current_sort = "time_desc"  # 当前排序方式
        self.current_view = "all"  # 当前视图（all, favorites, important, by_tags, by_model）
        self.current_tag_filter = ""  # 当前标签筛选
        self.current_model_filter = ""  # 当前模型筛选
        
        # 构建UI
        self._build_ui()
        
        # 加载结果
        self._load_results()
    
    def _build_ui(self):
        """构建UI界面"""
        # 主容器
        main_container = tk.Frame(self, bg=self.bg_main)
        main_container.pack(fill="both", expand=True, padx=14, pady=14)
        
        # 顶部信息栏
        self._build_top_bar(main_container)
        
        # 中间区域：结果列表和详细信息
        middle_container = tk.Frame(main_container, bg=self.bg_main)
        middle_container.pack(fill="both", expand=True, pady=(14, 0))
        
        # 两列布局
        left_panel = tk.Frame(middle_container, bg=self.bg_main)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 7))
        
        right_panel = tk.Frame(middle_container, bg=self.bg_main)
        right_panel.pack(side="right", fill="both", expand=True, padx=(7, 0))
        
        # 左面板：结果列表
        self._build_results_list(left_panel)
        
        # 右面板：详细信息
        self._build_details_panel(right_panel)
        
        # 底部按钮栏
        self._build_bottom_bar(main_container)
    
    def _build_top_bar(self, parent):
        """构建顶部信息栏"""
        top_frame = tk.Frame(parent, bg=self.bg_card, height=60, highlightthickness=1, 
                           highlightbackground=self.border)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)
        
        # 左侧：训练器信息
        left_frame = tk.Frame(top_frame, bg=self.bg_card)
        left_frame.pack(side="left", padx=20, pady=10)
        
        trainer_text = f"训练器: {self.trainer_id.upper() if self.trainer_id else '未指定'}"
        tk.Label(left_frame, text=trainer_text, bg=self.bg_card, fg=self.text_main,
                font=("Microsoft YaHei", 12, "bold")).pack(side="left")
        
        # 右侧：刷新按钮和结果数量
        right_frame = tk.Frame(top_frame, bg=self.bg_card)
        right_frame.pack(side="right", padx=20, pady=10)
        
        self.result_count_label = tk.Label(right_frame, text="加载中...", bg=self.bg_card, fg=self.text_sub,
                                          font=("Microsoft YaHei", 10))
        self.result_count_label.pack(side="right", padx=(10, 0))
        
        refresh_btn = tk.Button(right_frame, text=get_text("BTN_REFRESH"), bg=self.border, fg=self.text_main,
                               font=("Microsoft YaHei", 10), relief="flat", padx=12, pady=4,
                               command=self._load_results)
        refresh_btn.pack(side="right")
    
    def _build_results_list(self, parent):
        """构建结果列表"""
        # 列表卡片
        list_card = tk.Frame(parent, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        list_card.pack(fill="both", expand=True)
        
        tk.Label(list_card, text=get_text("LABEL_RESULTS"), bg=self.bg_card, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        
        # 筛选工具栏
        filter_frame = tk.Frame(list_card, bg=self.bg_card)
        filter_frame.pack(fill="x", padx=12, pady=(0, 8))
        
        # 筛选标签
        tk.Label(filter_frame, text="筛选:", bg=self.bg_card, fg=self.text_sub,
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 8))
        
        # 只看收藏按钮
        self.show_favorites_only = tk.BooleanVar(value=False)
        favorites_check = tk.Checkbutton(filter_frame, text="只看收藏", bg=self.bg_card, fg=self.text_main,
                                        selectcolor=self.bg_card, activebackground=self.bg_card,
                                        variable=self.show_favorites_only, font=("Microsoft YaHei", 9),
                                        command=self._apply_filters)
        favorites_check.pack(side="left", padx=(0, 12))
        
        # 只看重要按钮
        self.show_important_only = tk.BooleanVar(value=False)
        important_check = tk.Checkbutton(filter_frame, text="只看重要", bg=self.bg_card, fg=self.text_main,
                                        selectcolor=self.bg_card, activebackground=self.bg_card,
                                        variable=self.show_important_only, font=("Microsoft YaHei", 9),
                                        command=self._apply_filters)
        important_check.pack(side="left", padx=(0, 12))
        
        # 标签筛选输入框
        tk.Label(filter_frame, text="标签筛选:", bg=self.bg_card, fg=self.text_sub,
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 8))
        
        self.tag_filter_var = tk.StringVar()
        tag_filter_entry = tk.Entry(filter_frame, textvariable=self.tag_filter_var, bg="#1b2028", fg=self.text_main,
                                   relief="flat", font=("Microsoft YaHei", 9), width=20)
        tag_filter_entry.pack(side="left", padx=(0, 8))
        
        # 应用筛选按钮
        apply_filter_btn = tk.Button(filter_frame, text="应用", bg=self.border, fg=self.text_main,
                                    font=("Microsoft YaHei", 9), relief="flat", padx=8, pady=2,
                                    command=self._apply_filters)
        apply_filter_btn.pack(side="left", padx=(0, 8))
        
        # 重置筛选按钮
        reset_filter_btn = tk.Button(filter_frame, text="重置", bg=self.border, fg=self.text_main,
                                    font=("Microsoft YaHei", 9), relief="flat", padx=8, pady=2,
                                    command=self._reset_filters)
        reset_filter_btn.pack(side="left")
        
        # 分隔线
        separator1 = tk.Frame(filter_frame, height=1, bg=self.border)
        separator1.pack(side="left", fill="y", padx=12)
        
        # 排序工具栏
        tk.Label(filter_frame, text=get_text("LABEL_SORT_BY"), bg=self.bg_card, fg=self.text_sub,
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 8))
        
        # 排序方式下拉框
        sort_options = [
            ("time_desc", get_text("SORT_TIME_DESC")),
            ("time_asc", get_text("SORT_TIME_ASC")),
            ("best_val_acc_desc", get_text("SORT_BEST_VAL_ACC_DESC")),
            ("best_val_acc_asc", get_text("SORT_BEST_VAL_ACC_ASC")),
            ("final_val_acc_desc", get_text("SORT_FINAL_VAL_ACC_DESC")),
            ("final_val_acc_asc", get_text("SORT_FINAL_VAL_ACC_ASC")),
            ("best_epoch_desc", get_text("SORT_BEST_EPOCH_DESC")),
            ("best_epoch_asc", get_text("SORT_BEST_EPOCH_ASC"))
        ]
        
        self.sort_var = tk.StringVar(value="time_desc")
        sort_combo = ttk.Combobox(filter_frame, textvariable=self.sort_var, 
                                 values=[opt[1] for opt in sort_options],
                                 state="readonly", width=20)
        sort_combo.pack(side="left", padx=(0, 12))
        
        # 保存排序映射
        self.sort_map = {opt[1]: opt[0] for opt in sort_options}
        self.reverse_sort_map = {opt[0]: opt[1] for opt in sort_options}
        
        # 绑定排序变更事件
        self.sort_var.trace("w", lambda *args: self._apply_sorting())
        
        # 分隔线
        separator2 = tk.Frame(filter_frame, height=1, bg=self.border)
        separator2.pack(side="left", fill="y", padx=12)
        
        # 分组视图工具栏
        tk.Label(filter_frame, text=get_text("LABEL_GROUP_VIEW"), bg=self.bg_card, fg=self.text_sub,
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 8))
        
        # 分组视图选项
        view_options = [
            ("all", get_text("VIEW_ALL")),
            ("favorites", get_text("VIEW_FAVORITES")),
            ("important", get_text("VIEW_IMPORTANT")),
            ("by_tags", get_text("VIEW_BY_TAGS")),
            ("by_model", get_text("VIEW_BY_MODEL"))
        ]
        
        self.view_var = tk.StringVar(value=get_text("VIEW_ALL"))
        view_combo = ttk.Combobox(filter_frame, textvariable=self.view_var,
                                 values=[opt[1] for opt in view_options],
                                 state="readonly", width=15)
        view_combo.pack(side="left", padx=(0, 12))
        
        # 保存视图映射
        self.view_map = {opt[1]: opt[0] for opt in view_options}
        self.reverse_view_map = {opt[0]: opt[1] for opt in view_options}
        
        # 绑定视图变更事件
        self.view_var.trace("w", lambda *args: self._apply_view())
        
        # 标签筛选输入框（用于按标签查看视图）
        self.tag_filter_container = tk.Frame(filter_frame, bg=self.bg_card)
        tk.Label(self.tag_filter_container, text=get_text("LABEL_TAG_FILTER"), bg=self.bg_card, fg=self.text_sub,
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 8))
        self.view_tag_filter_var = tk.StringVar()
        self.view_tag_filter_entry = tk.Entry(self.tag_filter_container, textvariable=self.view_tag_filter_var, 
                                             bg="#1b2028", fg=self.text_main, relief="flat", 
                                             font=("Microsoft YaHei", 9), width=15)
        self.view_tag_filter_entry.pack(side="left", padx=(0, 8))
        self.view_tag_filter_btn = tk.Button(self.tag_filter_container, text="应用", bg=self.border, fg=self.text_main,
                                           font=("Microsoft YaHei", 9), relief="flat", padx=8, pady=2,
                                           command=self._apply_view)
        self.view_tag_filter_btn.pack(side="left")
        self.tag_filter_container.pack_forget()  # 默认隐藏
        
        # 模型筛选输入框（用于按模型查看视图）
        self.model_filter_container = tk.Frame(filter_frame, bg=self.bg_card)
        tk.Label(self.model_filter_container, text=get_text("LABEL_MODEL_FILTER"), bg=self.bg_card, fg=self.text_sub,
                font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 8))
        self.view_model_filter_var = tk.StringVar()
        self.view_model_filter_entry = tk.Entry(self.model_filter_container, textvariable=self.view_model_filter_var,
                                               bg="#1b2028", fg=self.text_main, relief="flat",
                                               font=("Microsoft YaHei", 9), width=15)
        self.view_model_filter_entry.pack(side="left", padx=(0, 8))
        self.view_model_filter_btn = tk.Button(self.model_filter_container, text="应用", bg=self.border, fg=self.text_main,
                                             font=("Microsoft YaHei", 9), relief="flat", padx=8, pady=2,
                                             command=self._apply_view)
        self.view_model_filter_btn.pack(side="left")
        self.model_filter_container.pack_forget()  # 默认隐藏
        
        # 创建树形视图
        columns = ("select", "name", "timestamp", "model", "best_epoch", "best_val_acc", "final_val_acc", "tags", "favorite", "important")
        self.tree = ttk.Treeview(list_card, columns=columns, show="headings", height=15)
        
        # 定义列
        self.tree.heading("select", text="选择")
        self.tree.heading("name", text=get_text("COL_EXP_NAME"))
        self.tree.heading("timestamp", text=get_text("COL_TIMESTAMP"))
        self.tree.heading("model", text=get_text("COL_MODEL"))
        self.tree.heading("best_epoch", text=get_text("COL_BEST_EPOCH"))
        self.tree.heading("best_val_acc", text=get_text("COL_BEST_VAL_ACC"))
        self.tree.heading("final_val_acc", text=get_text("COL_FINAL_VAL_ACC"))
        self.tree.heading("tags", text=get_text("COL_TAGS"))
        self.tree.heading("favorite", text=get_text("COL_FAVORITE"))
        self.tree.heading("important", text=get_text("COL_IMPORTANT"))
        
        # 设置列宽
        self.tree.column("select", width=50, anchor="center")
        self.tree.column("name", width=120, anchor="w")
        self.tree.column("timestamp", width=140, anchor="center")
        self.tree.column("model", width=80, anchor="center")
        self.tree.column("best_epoch", width=80, anchor="center")
        self.tree.column("best_val_acc", width=100, anchor="center")
        self.tree.column("final_val_acc", width=100, anchor="center")
        self.tree.column("tags", width=100, anchor="w")
        self.tree.column("favorite", width=50, anchor="center")
        self.tree.column("important", width=50, anchor="center")
        
        # 样式化
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background=self.bg_card, foreground=self.text_main,
                       fieldbackground=self.bg_card, borderwidth=0, font=('Consolas', 9))
        style.configure("Treeview.Heading", background=self.border, foreground=self.text_main,
                       relief="flat", font=('Consolas', 9, 'bold'))
        style.map("Treeview", background=[('selected', '#2d3440')])
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.tree.pack(side="left", fill="both", expand=True, padx=12, pady=(0, 10))
        scrollbar.pack(side="right", fill="y", padx=(0, 12), pady=(0, 10))
        
        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # 选择操作按钮
        selection_frame = tk.Frame(list_card, bg=self.bg_card)
        selection_frame.pack(fill="x", padx=12, pady=(0, 10))
        
        select_all_btn = tk.Button(selection_frame, text=get_text("BTN_SELECT_ALL"), bg=self.border, fg=self.text_main,
                                  font=("Microsoft YaHei", 9), relief="flat", padx=8, pady=3,
                                  command=self._select_all)
        select_all_btn.pack(side="left", padx=(0, 8))
        
        clear_selection_btn = tk.Button(selection_frame, text=get_text("BTN_CLEAR_SELECTION"), bg=self.border, fg=self.text_main,
                                       font=("Microsoft YaHei", 9), relief="flat", padx=8, pady=3,
                                       command=self._clear_selection)
        clear_selection_btn.pack(side="left")
    
    def _build_details_panel(self, parent):
        """构建详细信息面板"""
        # 详细信息卡片
        details_card = tk.Frame(parent, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        details_card.pack(fill="both", expand=True)
        
        tk.Label(details_card, text=get_text("LABEL_DETAILS"), bg=self.bg_card, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        
        # 选中信息
        selected_frame = tk.Frame(details_card, bg=self.bg_card)
        selected_frame.pack(fill="x", padx=12, pady=(0, 10))
        
        self.selected_label = tk.Label(selected_frame, text="未选中任何结果", bg=self.bg_card, fg=self.text_sub,
                                      font=("Microsoft YaHei", 10))
        self.selected_label.pack(anchor="w")
        
        # 详细信息文本区域
        details_frame = tk.Frame(details_card, bg=self.bg_card)
        details_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        
        self.details_text = scrolledtext.ScrolledText(
            details_frame,
            bg="#1b2028",
            fg=self.text_main,
            font=("Consolas", 9),
            wrap="word",
            height=20,
            relief="flat"
        )
        self.details_text.pack(fill="both", expand=True)
        self.details_text.insert("1.0", "选择一个结果查看详细信息...")
        self.details_text.config(state="disabled")
    
    def _build_bottom_bar(self, parent):
        """构建底部按钮栏"""
        bottom_frame = tk.Frame(parent, bg=self.bg_main, height=60)
        bottom_frame.pack(fill="x", pady=(14, 0))
        bottom_frame.pack_propagate(False)
        
        # 左侧按钮
        left_frame = tk.Frame(bottom_frame, bg=self.bg_main)
        left_frame.pack(side="left", padx=20)
        
        view_single_btn = tk.Button(left_frame, text=get_text("BTN_VIEW_SINGLE"), bg=self.border, fg=self.text_main,
                                   font=("Microsoft YaHei", 10), relief="flat", padx=15, pady=5,
                                   command=self._view_single_result)
        view_single_btn.pack(side="left", padx=(0, 8))
        
        compare_btn = tk.Button(left_frame, text=get_text("BTN_COMPARE"), bg=self.accent_blue, fg="white",
                               font=("Microsoft YaHei", 10, "bold"), relief="flat", padx=15, pady=5,
                               command=self._compare_results)
        compare_btn.pack(side="left", padx=(0, 8))
        
        reuse_btn = tk.Button(left_frame, text=get_text("BTN_REUSE_CONFIG"), bg=self.accent_green, fg="white",
                             font=("Microsoft YaHei", 10, "bold"), relief="flat", padx=15, pady=5,
                             command=self._reuse_config)
        reuse_btn.pack(side="left", padx=(0, 8))
        
        batch_btn = tk.Button(left_frame, text=get_text("BTN_BATCH_OPERATIONS"), bg=self.accent_blue, fg="white",
                            font=("Microsoft YaHei", 10, "bold"), relief="flat", padx=15, pady=5,
                            command=self._batch_operations)
        batch_btn.pack(side="left", padx=(0, 8))
        
        retrain_btn = tk.Button(left_frame, text=get_text("BTN_RETRAIN"), bg=self.accent_yellow, fg="white",
                              font=("Microsoft YaHei", 10, "bold"), relief="flat", padx=15, pady=5,
                              command=self._retrain_experiment)
        retrain_btn.pack(side="left", padx=(0, 8))
        
        # 右侧关闭按钮
        right_frame = tk.Frame(bottom_frame, bg=self.bg_main)
        right_frame.pack(side="right", padx=20)
        
        close_btn = tk.Button(right_frame, text=get_text("BTN_CLOSE"), bg=self.accent_red, fg="white",
                             font=("Microsoft YaHei", 10, "bold"), relief="flat", padx=25, pady=6,
                             command=self.destroy)
        close_btn.pack(side="right")
    
    def _load_results(self):
        """加载训练结果"""
        if not self.trainer_id:
            messagebox.showinfo("提示", "未指定训练器")
            return
        
        try:
            # 通过主窗口获取训练中心管理器
            if hasattr(self.master, 'training_center'):
                center = self.master.training_center
            else:
                from core.training_center_manager import get_training_center
                center = get_training_center()
            
            # 获取结果列表
            self.results = center.list_training_results(self.trainer_id, limit=50)
            
            # 清空缓存
            self.all_loaded_results = []
            
            # 更新结果数量
            self.result_count_label.config(text=f"找到 {len(self.results)} 个结果")
            
            if not self.results:
                # 清空树形视图
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                # 清空选择
                self.selected_indices.clear()
                
                # 添加占位行
                self.tree.insert("", "end", values=("", "无结果", "-", "-", "-", "-", "-"))
                self.details_text.config(state="normal")
                self.details_text.delete("1.0", tk.END)
                self.details_text.insert("1.0", get_text("MSG_NO_RESULTS"))
                self.details_text.config(state="disabled")
                return
            
            # 使用新的显示系统刷新显示
            self._refresh_display()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载结果失败: {str(e)}")
    
    def _on_tree_select(self, event):
        """树形视图选择事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        selected_id = selection[0]
        try:
            index = int(selected_id)
            if 0 <= index < len(self.results):
                # 切换选择状态
                if index in self.selected_indices:
                    self.selected_indices.remove(index)
                    # 更新显示（空表示未选中）
                    self.tree.set(selected_id, "select", "")
                else:
                    self.selected_indices.add(index)
                    # 更新显示（✓表示选中）
                    self.tree.set(selected_id, "select", "✓")
                
                # 更新详细信息
                self._update_details(index)
                self._update_selected_label()
        except ValueError:
            pass
    
    def _select_all(self):
        """全选"""
        for i in range(len(self.results)):
            self.selected_indices.add(i)
            item_id = str(i)
            if self.tree.exists(item_id):
                self.tree.set(item_id, "select", "✓")
        
        self._update_selected_label()
    
    def _clear_selection(self):
        """清空选择"""
        self.selected_indices.clear()
        
        for i in range(len(self.results)):
            item_id = str(i)
            if self.tree.exists(item_id):
                self.tree.set(item_id, "select", "")
        
        self._update_selected_label()
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", "选择一个结果查看详细信息...")
        self.details_text.config(state="disabled")
    
    def _update_details(self, index):
        """更新详细信息"""
        if index < 0 or index >= len(self.results):
            return
        
        result = self.results[index]
        config = result.get("config", {})
        
        # 构建详细信息文本
        details = []
        details.append(f"=== 实验: {result['name']} ===")
        details.append(f"训练时间: {result['timestamp']}")
        details.append(f"结果文件: {result['path']}")
        details.append("")
        details.append("--- 训练配置 ---")
        details.append(f"模型: {config.get('model_name', '未知')}")
        details.append(f"类别数: {config.get('num_classes', '未知')}")
        details.append(f"训练轮数: {config.get('epochs', '未知')}")
        details.append(f"批大小: {config.get('batch_size', '未知')}")
        details.append(f"学习率: {config.get('learning_rate', '未知')}")
        details.append("")
        
        if "best_epoch" in config:
            details.append("--- 训练结果 ---")
            details.append(f"最佳验证准确率: {config.get('best_val_acc', 0):.2f}% (第 {config['best_epoch']} 轮)")
            details.append(f"最终验证准确率: {config.get('final_val_acc', 0):.2f}%")
        
        # 更新文本区域
        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", "\n".join(details))
        self.details_text.config(state="disabled")
    
    def _update_selected_label(self):
        """更新选中标签"""
        count = len(self.selected_indices)
        if count == 0:
            self.selected_label.config(text="未选中任何结果", fg=self.text_sub)
        else:
            self.selected_label.config(text=f"已选中 {count} 个结果", fg=self.accent_green)
    
    def _view_single_result(self):
        """查看单个结果"""
        if len(self.selected_indices) != 1:
            messagebox.showwarning("提示", get_text("MSG_SELECT_ONE"))
            return
        
        index = list(self.selected_indices)[0]
        result = self.results[index]
        
        try:
            from ui.training_result_window import TrainingResultWindow
            
            result_window = TrainingResultWindow(self, log_path=result["path"])
            result_window.title(f"{self.trainer_id}训练结果 - {result['name']}")
            
        except Exception as e:
            messagebox.showerror("错误", f"打开结果窗口失败: {str(e)}")
    
    def _compare_results(self):
        """对比结果"""
        if len(self.selected_indices) < 2:
            messagebox.showwarning("提示", get_text("MSG_SELECT_TWO"))
            return
        
        selected_indices = sorted(list(self.selected_indices))
        
        # 限制最多对比4个结果
        if len(selected_indices) > 4:
            selected_indices = selected_indices[:4]
            messagebox.showinfo("提示", "最多支持对比4个结果，已选择前4个")
        
        # 获取选中的结果路径
        selected_paths = []
        selected_names = []
        
        for index in selected_indices:
            result = self.results[index]
            selected_paths.append(result["path"])
            selected_names.append(result["name"])
        
        # 打开对比窗口
        try:
            from ui.training_comparison_window import TrainingComparisonWindow
            
            compare_window = TrainingComparisonWindow(self, selected_paths, selected_names)
            compare_window.title(f"结果对比 - {self.trainer_id}")
            
        except ImportError:
            # 如果对比窗口不存在，显示提示
            messagebox.showinfo("提示", 
                f"结果对比功能暂未完全实现。\n\n"
                f"已选中 {len(selected_indices)} 个结果:\n"
                f"{', '.join(selected_names)}\n\n"
                f"对比窗口正在开发中...")
        except Exception as e:
            messagebox.showerror("错误", f"打开对比窗口失败: {str(e)}")
    
    def _reuse_config(self):
        """复用选中结果的配置"""
        if len(self.selected_indices) != 1:
            messagebox.showwarning("提示", get_text("MSG_REUSE_SELECT_ONE"))
            return
        
        index = list(self.selected_indices)[0]
        result = self.results[index]
        
        try:
            # 加载训练日志获取配置
            from core.training_result_analyzer import get_result_analyzer
            from core.config_comparator import get_config_comparator
            
            analyzer = get_result_analyzer()
            result_obj = analyzer.load_result(result["path"])
            
            if not result_obj:
                messagebox.showerror("错误", "无法加载训练结果")
                return
            
            # 准备复用配置
            comparator = get_config_comparator()
            reused_config = comparator.prepare_config_for_reuse(result_obj.config)
            
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
                    self.destroy()  # 关闭历史窗口
                    return
            
            # 更新现有训练中心窗口的配置
            if training_center_window and hasattr(training_center_window, 'current_config'):
                training_center_window.current_config = reused_config
                training_center_window._load_current_config()
                training_center_window.deiconify()  # 显示窗口
                training_center_window.focus_force()
                
                messagebox.showinfo("提示", get_text("MSG_REUSE_SUCCESS"))
                self.destroy()  # 关闭历史窗口
            else:
                messagebox.showerror("错误", "无法找到训练中心窗口")
                
        except Exception as e:
            messagebox.showerror("错误", f"{get_text('MSG_REUSE_ERROR')}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _retrain_experiment(self):
        """一键再训练选中结果"""
        if len(self.selected_indices) != 1:
            messagebox.showwarning("提示", get_text("MSG_RETRAIN_SELECT_ONE"))
            return
        
        index = list(self.selected_indices)[0]
        result = self.results[index]
        
        try:
            # 加载训练日志获取配置和批注
            from core.training_result_analyzer import get_result_analyzer
            from core.config_comparator import get_config_comparator
            
            analyzer = get_result_analyzer()
            result_obj = analyzer.load_result(result["path"])
            
            if not result_obj:
                messagebox.showerror("错误", "无法加载训练结果")
                return
            
            # 准备复用配置
            comparator = get_config_comparator()
            reused_config = comparator.prepare_config_for_reuse(result_obj.config, suffix="再训练")
            
            # 添加批注信息
            notes = {
                "experiment_notes": f"基于实验 '{result['name']}' 的再训练",
                "change_description": "基于历史实验配置进行再训练",
                "reason_for_retraining": "优化模型性能/调整超参数",
                "source_experiment": result["path"],
                "source_experiment_name": result["name"],
                "retrain_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 如果原实验有批注，保留部分信息
            if hasattr(result_obj, 'notes') and result_obj.notes:
                original_notes = result_obj.notes
                # 保留原实验备注
                if "experiment_notes" in original_notes and original_notes["experiment_notes"]:
                    notes["original_experiment_notes"] = original_notes["experiment_notes"]
                # 保留其他信息
                notes["original_notes"] = original_notes
            
            reused_config["notes"] = notes
            
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
                    messagebox.showinfo("提示", get_text("MSG_RETRAIN_SUCCESS"))
                    self.destroy()  # 关闭历史窗口
                    return
            
            # 更新现有训练中心窗口的配置
            if training_center_window and hasattr(training_center_window, 'current_config'):
                training_center_window.current_config = reused_config
                training_center_window._load_current_config()
                training_center_window.deiconify()  # 显示窗口
                training_center_window.focus_force()
                
                messagebox.showinfo("提示", get_text("MSG_RETRAIN_SUCCESS"))
                self.destroy()  # 关闭历史窗口
            else:
                messagebox.showerror("错误", "无法找到训练中心窗口")
                
        except Exception as e:
            messagebox.showerror("错误", f"{get_text('MSG_RETRAIN_ERROR')}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _batch_operations(self):
        """批量操作"""
        if not self.selected_indices:
            messagebox.showwarning("提示", get_text("MSG_SELECT_FOR_BATCH"))
            return
        
        # 打开批量操作对话框
        from ui.batch_operations_dialog import BatchOperationsDialog
        dialog = BatchOperationsDialog(
            self,
            selected_indices=list(self.selected_indices),
            results=self.results,
            on_success=self._refresh_display
        )
    
    def _apply_sorting(self):
        """应用排序"""
        sort_key = self.sort_map.get(self.sort_var.get(), "time_desc")
        self.current_sort = sort_key
        
        # 重新加载并应用当前视图和排序
        self._refresh_display()
    
    def _apply_view(self):
        """应用分组视图"""
        view_key = self.view_map.get(self.view_var.get(), "all")
        self.current_view = view_key
        
        # 更新筛选输入框的显示状态
        if view_key == "by_tags":
            self.tag_filter_container.pack(side="left", padx=(0, 12))
            self.model_filter_container.pack_forget()
            # 更新当前标签筛选
            self.current_tag_filter = self.view_tag_filter_var.get().strip().lower()
        elif view_key == "by_model":
            self.model_filter_container.pack(side="left", padx=(0, 12))
            self.tag_filter_container.pack_forget()
            # 更新当前模型筛选
            self.current_model_filter = self.view_model_filter_var.get().strip().lower()
        else:
            self.tag_filter_container.pack_forget()
            self.model_filter_container.pack_forget()
            self.current_tag_filter = ""
            self.current_model_filter = ""
        
        # 重新加载并应用当前视图和排序
        self._refresh_display()
    
    def _refresh_display(self):
        """刷新显示：应用所有筛选、排序和视图"""
        # 如果还没有加载完整结果对象，先加载
        if not self.all_loaded_results and self.results:
            analyzer = get_result_analyzer()
            self.all_loaded_results = []
            for result in self.results:
                try:
                    result_obj = analyzer.load_result(result["path"])
                    self.all_loaded_results.append((result, result_obj))
                except Exception:
                    self.all_loaded_results.append((result, None))
        
        # 获取当前显示的结果
        display_items = self._get_filtered_items()
        
        # 应用排序
        sorted_items = self._apply_sorting_to_items(display_items)
        
        # 更新树形视图
        self._update_tree_with_items(sorted_items)
    
    def _get_filtered_items(self):
        """获取经过视图筛选的结果"""
        filtered_items = []
        
        for result, result_obj in self.all_loaded_results:
            include = True
            
            # 根据当前视图进行筛选
            if self.current_view == "favorites":
                if not result_obj or not getattr(result_obj, 'is_favorite', False):
                    include = False
            elif self.current_view == "important":
                if not result_obj or not getattr(result_obj, 'is_important', False):
                    include = False
            elif self.current_view == "by_tags":
                if not result_obj:
                    include = False
                elif self.current_tag_filter:
                    tags = getattr(result_obj, 'tags', [])
                    tag_matched = any(self.current_tag_filter in tag.lower() for tag in tags)
                    if not tag_matched:
                        include = False
            elif self.current_view == "by_model":
                if not result_obj:
                    include = False
                elif self.current_model_filter:
                    config = getattr(result_obj, 'config', {})
                    model_name = config.get('model_name', '').lower()
                    if self.current_model_filter not in model_name:
                        include = False
            
            # 默认排除已归档的实验（安全清理方案）
            if include and result_obj:
                is_archived = getattr(result_obj, 'is_archived', False)
                if is_archived:
                    include = False
            
            # 应用原有的筛选条件（兼容性）
            if include:
                # 收藏筛选
                if self.show_favorites_only.get():
                    if not result_obj or not getattr(result_obj, 'is_favorite', False):
                        include = False
                
                # 重要筛选
                if include and self.show_important_only.get():
                    if not result_obj or not getattr(result_obj, 'is_important', False):
                        include = False
                
                # 标签筛选
                if include and self.tag_filter_var.get().strip():
                    tag_filter = self.tag_filter_var.get().strip().lower()
                    if not result_obj:
                        include = False
                    else:
                        tags = getattr(result_obj, 'tags', [])
                        tag_matched = any(tag_filter in tag.lower() for tag in tags)
                        if not tag_matched:
                            include = False
            
            if include:
                filtered_items.append((result, result_obj))
        
        return filtered_items
    
    def _apply_sorting_to_items(self, items):
        """对结果进行排序"""
        if not items:
            return items
        
        # 解析排序键
        sort_key = self.current_sort
        
        def get_sort_value(item):
            result, result_obj = item
            config = result.get("config", {})
            
            if sort_key == "time_desc" or sort_key == "time_asc":
                # 按时间排序
                timestamp = result.get("timestamp", "")
                return timestamp
            
            elif sort_key.startswith("best_val_acc"):
                # 按最佳验证准确率排序
                val = config.get("best_val_acc", 0)
                if isinstance(val, str) and val != "-":
                    try:
                        return float(val.rstrip("%"))
                    except:
                        return 0.0
                return float(val) if isinstance(val, (int, float)) else 0.0
            
            elif sort_key.startswith("final_val_acc"):
                # 按最终验证准确率排序
                val = config.get("final_val_acc", 0)
                if isinstance(val, str) and val != "-":
                    try:
                        return float(val.rstrip("%"))
                    except:
                        return 0.0
                return float(val) if isinstance(val, (int, float)) else 0.0
            
            elif sort_key.startswith("best_epoch"):
                # 按最佳轮数排序
                val = config.get("best_epoch", 0)
                if isinstance(val, str) and val != "-":
                    try:
                        return int(val)
                    except:
                        return 0
                return int(val) if isinstance(val, (int, float)) else 0
            
            return 0
        
        # 排序
        reverse = sort_key.endswith("_desc")
        sorted_items = sorted(items, key=get_sort_value, reverse=reverse)
        
        return sorted_items
    
    def _update_tree_with_items(self, items):
        """用排序后的项目更新树形视图"""
        # 清空树形视图
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 清空选择
        self.selected_indices.clear()
        
        # 保存当前显示的项目
        self.displayed_items = items
        self.id_to_display_index = {}
        
        # 添加排序后的项目到树形视图
        for i, (result, result_obj) in enumerate(items):
            config = result.get("config", {})
            
            # 格式化值
            best_epoch = config.get("best_epoch", "-")
            best_val_acc = config.get("best_val_acc", "-")
            final_val_acc = config.get("final_val_acc", "-")
            
            if isinstance(best_val_acc, (int, float)):
                best_val_acc = f"{best_val_acc:.2f}%"
            if isinstance(final_val_acc, (int, float)):
                final_val_acc = f"{final_val_acc:.2f}%"
            
            # 获取标签/收藏/重要标记
            tags_display = ""
            favorite_display = ""
            important_display = ""
            
            if result_obj:
                # 标签（显示前3个标签，用逗号分隔）
                tags = getattr(result_obj, 'tags', [])
                if tags:
                    tags_display = ", ".join(tags[:3])
                    if len(tags) > 3:
                        tags_display += f" (+{len(tags)-3})"
                
                # 收藏（显示★或空）
                is_favorite = getattr(result_obj, 'is_favorite', False)
                favorite_display = "★" if is_favorite else ""
                
                # 重要标记（显示❗或空）
                is_important = getattr(result_obj, 'is_important', False)
                important_display = "❗" if is_important else ""
            
            values = (
                "",  # 选择状态（空表示未选中）
                result["name"],
                result["timestamp"],
                config.get("model_name", "未知"),
                best_epoch,
                best_val_acc,
                final_val_acc,
                tags_display,
                favorite_display,
                important_display,
            )
            
            tree_id = str(i)
            self.tree.insert("", "end", values=values, iid=tree_id)
            self.id_to_display_index[tree_id] = i
        
        # 更新结果数量显示
        self.result_count_label.config(text=f"找到 {len(items)} 个结果 (已筛选)")
        
        # 更新选中标签
        self._update_selected_label()
    
    def _apply_filters(self):
        """应用筛选条件（兼容原有筛选系统）"""
        # 使用新的显示系统刷新显示
        self._refresh_display()
    
    def _reset_filters(self):
        """重置筛选条件"""
        self.show_favorites_only.set(False)
        self.show_important_only.set(False)
        self.tag_filter_var.set("")
        self._apply_filters()


def open_training_history(master, trainer_id=None):
    """打开训练历史窗口（工厂函数）"""
    if trainer_id is None:
        # 尝试从主窗口获取当前训练器
        if hasattr(master, 'current_trainer_id'):
            trainer_id = master.current_trainer_id
        else:
            messagebox.showinfo("提示", "请先选择训练器")
            return None
    
    # 检查训练器是否支持历史结果
    supported_trainers = ["classification", "yolo_v8"]
    if trainer_id not in supported_trainers:
        messagebox.showinfo("提示", 
            f"训练器 '{trainer_id}' 暂不支持历史结果查看。\n"
            f"目前支持: {', '.join(supported_trainers)}")
        return None
    
    # 创建窗口
    win = TrainingHistoryWindow(master, trainer_id)
    
    # 设置窗口标题
    win.title(f"训练历史 - {trainer_id.upper()}")
    
    return win


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.withdraw()
    
    win = TrainingHistoryWindow(root, "classification")
    root.mainloop()