"""
训练中心窗口 - 通用训练中心UI
提供训练器选择、配置编辑、训练前体检和训练启动功能
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os

from core.training_center_manager import get_training_center
from core.trainer_registry import initialize_registry
from core.ui_style_manager import get_style_manager
from core.language_manager import get_language_manager, t


def get_text(key):
    """根据当前语言配置获取文本（兼容旧版本）"""
    return t(key)


class TrainingCenterWindow(tk.Toplevel):
    """训练中心窗口"""
    
    def __init__(self, master, config_data=None):
        super().__init__(master)
        self.master = master
        self.config_data = config_data or {}
        
        self.title(get_text("TITLE_TRAINING_CENTER"))
        self.geometry("1000x700")
        self.minsize(900, 600)
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
        
        # UI管理器
        self.style_manager = get_style_manager()
        self.language_manager = get_language_manager()
        
        # 更新颜色值从风格管理器
        self._update_colors_from_style()
        
        # 训练中心管理器
        initialize_registry()
        self.training_center = get_training_center()
        
        # 当前状态
        self.current_trainer_id = None
        # 智能处理配置数据：支持两种格式
        # 1. 包含'training'键的配置字典（来自主窗口）
        # 2. 直接的训练配置字典（来自复用功能）
        if "training" in self.config_data:
            self.current_config = self.config_data.get("training", {}).copy()
        elif self.config_data and isinstance(self.config_data, dict):
            # 假设是直接的训练配置
            self.current_config = self.config_data.copy()
        else:
            self.current_config = {}
        self.health_report = None
        
        # 构建UI
        self._build_ui()
        
        # 注册回调
        self.language_manager.register_callback(self._refresh_ui_on_language_change)
        self.style_manager.register_callback(self._refresh_ui_on_style_change)
        
        # 初始化训练器列表
        self._load_trainers()
        
        # 加载当前配置
        self._load_current_config()
    
    def _update_colors_from_style(self):
        """从风格管理器更新颜色值"""
        theme = self.style_manager.get_current_theme_definition()
        
        # 更新基础颜色
        self.bg_main = theme.colors.get("background", "#16181d")
        self.bg_card = theme.colors.get("surface", "#252a33")
        self.text_main = theme.colors.get("text_primary", "#f5f7fa")
        self.text_sub = theme.colors.get("text_secondary", "#aeb6c2")
        self.border = theme.colors.get("border", "#2d3440")
        self.accent_green = theme.colors.get("success", "#67d39a")
        self.accent_yellow = theme.colors.get("warning", "#ff9d57")
        self.accent_red = theme.colors.get("error", "#ff6b6b")
        self.accent_blue = theme.colors.get("primary", "#4da3ff")
        
        # 更新窗口背景
        self.configure(bg=self.bg_main)
    
    def _refresh_ui_on_style_change(self):
        """风格切换时刷新UI样式"""
        # 更新颜色值
        self._update_colors_from_style()
        
        # 刷新窗口背景
        self.configure(bg=self.bg_main)
        
        # 刷新主容器背景
        if hasattr(self, 'main_container'):
            self.main_container.config(bg=self.bg_main)
        
        # 刷新所有卡片的背景和文字颜色
        card_widgets = [
            'trainer_card', 'config_card', 'health_card', 'action_card'
        ]
        
        for card_name in card_widgets:
            if hasattr(self, card_name):
                card = getattr(self, card_name)
                try:
                    card.config(bg=self.bg_card, highlightbackground=self.border)
                except:
                    pass
        
        # 刷新标题标签
        if hasattr(self, 'title_label'):
            try:
                self.title_label.config(bg=self.bg_main, fg=self.text_main)
            except:
                pass
        
        # 刷新主要按钮颜色
        button_widgets = [
            'run_health_check_btn', 'start_training_btn', 'save_config_btn',
            'load_config_btn', 'view_result_btn', 'view_history_btn'
        ]
        
        for btn_name in button_widgets:
            if hasattr(self, btn_name):
                btn = getattr(self, btn_name)
                try:
                    btn.config(bg=self.accent_blue, fg=self.text_main)
                except:
                    pass
        
        # 刷新文本区域
        if hasattr(self, 'config_text'):
            try:
                self.config_text.config(bg=self.bg_card, fg=self.text_main, 
                                      insertbackground=self.text_main)
            except:
                pass
        
        # 刷新健康检查结果区域
        if hasattr(self, 'health_text'):
            try:
                self.health_text.config(bg=self.bg_card, fg=self.text_main)
            except:
                pass
        
        print(f"训练中心风格已刷新，当前风格: {self.style_manager.current_style.value}")
    
    def _refresh_ui_on_language_change(self):
        """语言切换时刷新UI文案"""
        # 更新窗口标题
        self.title(get_text("TITLE_TRAINING_CENTER"))
        
        # 更新按钮文本
        if hasattr(self, 'run_health_check_btn'):
            self.run_health_check_btn.config(text=get_text("BTN_RUN_HEALTH_CHECK"))
        if hasattr(self, 'start_training_btn'):
            self.start_training_btn.config(text=get_text("BTN_START_TRAINING"))
        if hasattr(self, 'save_config_btn'):
            self.save_config_btn.config(text=get_text("BTN_SAVE_CONFIG"))
        if hasattr(self, 'load_config_btn'):
            self.load_config_btn.config(text=get_text("BTN_LOAD_CONFIG"))
        if hasattr(self, 'view_result_btn'):
            self.view_result_btn.config(text=get_text("BTN_VIEW_RESULT"))
        if hasattr(self, 'view_history_btn'):
            self.view_history_btn.config(text=get_text("BTN_VIEW_HISTORY"))
    
    def _build_ui(self):
        """构建UI界面"""
        # 主容器
        main_container = tk.Frame(self, bg=self.bg_main)
        main_container.pack(fill="both", expand=True, padx=14, pady=14)
        
        # 两列布局
        left_panel = tk.Frame(main_container, bg=self.bg_main)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 7))
        
        right_panel = tk.Frame(main_container, bg=self.bg_main)
        right_panel.pack(side="right", fill="both", expand=True, padx=(7, 0))
        
        # 左面板：训练器选择和配置
        self._build_left_panel(left_panel)
        
        # 右面板：体检结果和控制
        self._build_right_panel(right_panel)
    
    def _build_left_panel(self, parent):
        """构建左面板"""
        # 训练器选择卡片
        trainer_card = tk.Frame(parent, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        trainer_card.pack(fill="x", pady=(0, 14))
        
        tk.Label(trainer_card, text=get_text("LABEL_SELECT_TRAINER"), bg=self.bg_card, fg=self.text_main, 
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        
        # 训练器选择框
        trainer_frame = tk.Frame(trainer_card, bg=self.bg_card)
        trainer_frame.pack(fill="x", padx=12, pady=(0, 10))
        
        tk.Label(trainer_frame, text="训练器:", bg=self.bg_card, fg=self.text_sub, 
                font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 8))
        
        self.trainer_combo = ttk.Combobox(trainer_frame, state="readonly", width=30)
        self.trainer_combo.pack(side="left", fill="x", expand=True)
        self.trainer_combo.bind("<<ComboboxSelected>>", self._on_trainer_selected)
        
        # 训练器描述
        self.trainer_desc_label = tk.Label(trainer_card, text="", bg=self.bg_card, fg=self.text_sub, 
                                          font=("Microsoft YaHei", 9), wraplength=400, justify="left")
        self.trainer_desc_label.pack(anchor="w", padx=12, pady=(0, 10))
        
        # 配置编辑卡片
        config_card = tk.Frame(parent, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        config_card.pack(fill="both", expand=True)
        
        tk.Label(config_card, text=get_text("LABEL_TRAINING_CONFIG"), bg=self.bg_card, fg=self.text_main, 
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        
        # 配置编辑区域
        config_edit_frame = tk.Frame(config_card, bg=self.bg_card)
        config_edit_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        
        # JSON编辑器
        self.config_text = scrolledtext.ScrolledText(
            config_edit_frame, 
            bg=self.bg_card_2, 
            fg=self.text_sub,
            font=("Consolas", 10),
            wrap="word",
            height=20
        )
        self.config_text.pack(fill="both", expand=True)
        
        # 配置操作按钮
        config_btn_frame = tk.Frame(config_card, bg=self.bg_card)
        config_btn_frame.pack(fill="x", padx=12, pady=(0, 10))
        
        tk.Button(config_btn_frame, text="加载默认配置", bg=self.border, fg=self.text_main, 
                 relief="flat", command=self._load_default_config).pack(side="left", padx=(0, 8))
        tk.Button(config_btn_frame, text="验证JSON格式", bg=self.border, fg=self.text_main, 
                 relief="flat", command=self._validate_json).pack(side="left")
        
        # 配置要求显示卡片（第二期新增）
        config_req_card = tk.Frame(parent, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        config_req_card.pack(fill="x", pady=(14, 0))
        
        tk.Label(config_req_card, text="当前训练器配置要求", bg=self.bg_card, fg=self.text_main, 
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        
        # 配置要求详情
        req_frame = tk.Frame(config_req_card, bg=self.bg_card)
        req_frame.pack(fill="x", padx=12, pady=(0, 10))
        
        self.config_req_text = tk.Text(
            req_frame,
            bg=self.bg_card_2,
            fg=self.text_sub,
            font=("Consolas", 9),
            wrap="word",
            height=6,
            relief="flat"
        )
        self.config_req_text.pack(fill="x", expand=True)
        self.config_req_text.insert("1.0", "选择训练器后显示配置要求...")
        self.config_req_text.config(state="disabled")
    
    def _build_right_panel(self, parent):
        """构建右面板"""
        # 体检结果卡片
        health_card = tk.Frame(parent, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        health_card.pack(fill="both", expand=True, pady=(0, 14))
        
        tk.Label(health_card, text=get_text("LABEL_HEALTH_CHECK"), bg=self.bg_card, fg=self.text_main, 
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        
        # 体检状态
        status_frame = tk.Frame(health_card, bg=self.bg_card)
        status_frame.pack(fill="x", padx=12, pady=(0, 10))
        
        tk.Label(status_frame, text="状态:", bg=self.bg_card, fg=self.text_sub, 
                font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 8))
        
        self.health_status_label = tk.Label(status_frame, text=get_text("STATUS_PENDING"), bg=self.bg_card, 
                                           fg=self.text_sub, font=("Microsoft YaHei", 10, "bold"))
        self.health_status_label.pack(side="left")
        
        # 体检结果详情
        result_frame = tk.Frame(health_card, bg=self.bg_card)
        result_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            bg=self.bg_card_2,
            fg=self.text_sub,
            font=("Consolas", 9),
            wrap="word",
            height=15
        )
        self.result_text.pack(fill="both", expand=True)
        self.result_text.insert("1.0", "等待运行训练前体检...\n\n点击'运行体检'按钮开始检查。")
        self.result_text.config(state="disabled")
        
        # 控制卡片
        control_card = tk.Frame(parent, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        control_card.pack(fill="x")
        
        control_btn_frame = tk.Frame(control_card, bg=self.bg_card)
        control_btn_frame.pack(fill="x", padx=12, pady=12)
        
        # 按钮
        self.health_check_btn = tk.Button(control_btn_frame, text=get_text("BTN_RUN_HEALTH_CHECK"), 
                                         bg=self.accent_blue, fg="white", relief="flat",
                                         activebackground="#4b7cff", activeforeground="white",
                                         command=self._run_health_check)
        self.health_check_btn.pack(side="left", padx=(0, 8))
        
        self.start_training_btn = tk.Button(control_btn_frame, text=get_text("BTN_START_TRAINING"), 
                                           bg=self.accent_blue, fg=self.text_main, relief="flat",
                                           activebackground=self.accent_blue, activeforeground=self.text_main,
                                           command=self._start_training, state="disabled")
        self.start_training_btn.pack(side="left", padx=(0, 8))
        
        self.open_monitor_btn = tk.Button(control_btn_frame, text=get_text("BTN_OPEN_MONITOR"), 
                                         bg=self.border, fg=self.text_main, relief="flat",
                                         command=self._open_monitor)
        self.open_monitor_btn.pack(side="left", padx=(0, 8))
        
        self.view_result_btn = tk.Button(control_btn_frame, text="查看结果", 
                                        bg=self.border, fg=self.text_main, relief="flat",
                                        command=self._view_training_result, state="normal")
        self.view_result_btn.pack(side="left", padx=(0, 8))
        
        self.view_history_btn = tk.Button(control_btn_frame, text="历史结果", 
                                         bg=self.border, fg=self.text_main, relief="flat",
                                         command=self._view_training_history, state="normal")
        self.view_history_btn.pack(side="left", padx=(0, 8))
        
        tk.Button(control_btn_frame, text=get_text("BTN_CLOSE"), 
                 bg=self.border, fg=self.text_main, relief="flat",
                 command=self.destroy).pack(side="right")
    
    def _load_trainers(self):
        """加载训练器列表"""
        trainers = self.training_center.get_available_trainers()
        
        if not trainers:
            self.trainer_combo["values"] = ["未找到可用训练器"]
            self.trainer_combo.set("未找到可用训练器")
            return
        
        # 构建显示名称，添加标识
        display_names = []
        for t in trainers:
            name = f"{t['display_name']} ({t['trainer_id']})"
            if t.get('is_placeholder', False):
                name += " [示例]"
            elif t.get('can_train', False):
                name += " [可训练]"
            else:
                name += " [暂不支持]"
            display_names.append(name)
        
        self.trainer_combo["values"] = display_names
        
        # 默认选择第一个
        if display_names:
            self.trainer_combo.set(display_names[0])
            self._on_trainer_selected()
    
    def _on_trainer_selected(self, event=None):
        """训练器选择事件"""
        selection = self.trainer_combo.get()
        if not selection or "未找到" in selection:
            return
        
        # 提取trainer_id（处理可能的后缀如"[示例]"）
        if "(" in selection and ")" in selection:
            # 提取括号内的内容
            import re
            match = re.search(r'\(([^)]+)\)', selection)
            if match:
                trainer_id = match.group(1)
            else:
                trainer_id = "yolo_v8"  # 默认
        else:
            trainer_id = "yolo_v8"  # 默认
        
        self.current_trainer_id = trainer_id
        
        # 更新训练器描述
        trainer_info = self.training_center.get_trainer_info(trainer_id)
        if trainer_info:
            # 获取训练器列表中的额外信息
            trainers_list = self.training_center.get_available_trainers()
            trainer_extra = next((t for t in trainers_list if t['trainer_id'] == trainer_id), {})
            
            is_placeholder = trainer_extra.get('is_placeholder', True)
            can_train = trainer_extra.get('can_train', False)
            supported = trainer_extra.get('supported', False)
            
            # 构建描述
            desc = f"{trainer_info['description']}\n"
            desc += f"任务类型: {trainer_info['task_type']} | 框架: {trainer_info['framework']}\n"
            
            if is_placeholder:
                desc += f"⚠️ 这是一个示例训练器，不实际执行训练\n"
            elif not supported:
                desc += f"⚠️ 此训练器尚未完全支持\n"
            elif can_train:
                desc += f"✅ 此训练器可真实启动训练\n"
            
            self.trainer_desc_label.config(text=desc)
            
            # 更新配置要求显示
            self._update_config_requirements(trainer_info)
            
            # 加载默认配置
            self._load_default_config_for_trainer(trainer_id)
            
            # 更新按钮状态
            self._update_button_states(can_train, supported)
        else:
            self.trainer_desc_label.config(text="")
            self._clear_config_requirements()
            self._update_button_states(False, False)
    
    def _update_config_requirements(self, trainer_info):
        """更新配置要求显示"""
        try:
            self.config_req_text.config(state="normal")
            self.config_req_text.delete("1.0", tk.END)
            
            # 标题
            self.config_req_text.insert("end", f"【{trainer_info['display_name']}】配置要求\n")
            self.config_req_text.insert("end", "=" * 40 + "\n\n")
            
            # 必需配置项
            self.config_req_text.insert("end", "🔴 必需配置项:\n")
            for key in trainer_info.get("required_config_keys", []):
                self.config_req_text.insert("end", f"  • {key}\n")
            
            # 必需文件
            self.config_req_text.insert("end", "\n📁 必需文件:\n")
            for file in trainer_info.get("required_files", []):
                self.config_req_text.insert("end", f"  • {file}\n")
            
            # 必需依赖
            self.config_req_text.insert("end", "\n📦 必需依赖包:\n")
            for dep in trainer_info.get("required_dependencies", []):
                self.config_req_text.insert("end", f"  • {dep}\n")
            
            # 配置schema（如果有）
            if trainer_info.get("config_schema"):
                self.config_req_text.insert("end", "\n📋 配置字段说明:\n")
                for key, schema in trainer_info.get("config_schema", {}).items():
                    label = schema.get("label", key)
                    required = "🔴" if schema.get("required", False) else "⚪"
                    desc = schema.get("description", "")
                    self.config_req_text.insert("end", f"  {required} {label}: {desc}\n")
            
            self.config_req_text.config(state="disabled")
        except Exception as e:
            self.config_req_text.config(state="normal")
            self.config_req_text.delete("1.0", tk.END)
            self.config_req_text.insert("end", f"配置要求显示错误: {str(e)}")
            self.config_req_text.config(state="disabled")
    
    def _clear_config_requirements(self):
        """清空配置要求显示"""
        self.config_req_text.config(state="normal")
        self.config_req_text.delete("1.0", tk.END)
        self.config_req_text.insert("end", "选择训练器后显示配置要求...")
        self.config_req_text.config(state="disabled")
    
    def _update_button_states(self, can_train: bool, supported: bool):
        """更新按钮状态"""
        if can_train and supported:
            self.start_training_btn.config(state="normal", bg="#3a6df0", text="启动训练")
            self.health_check_btn.config(state="normal", bg=self.accent_blue)
        elif supported:
            self.start_training_btn.config(state="normal", bg="#3a6df0", text="启动训练")
            self.health_check_btn.config(state="normal", bg=self.accent_blue)
        else:
            self.start_training_btn.config(state="disabled", bg=self.border, text="暂不支持训练")
            self.health_check_btn.config(state="normal", bg=self.accent_blue)  # 体检按钮仍可用
    
    def _load_current_config(self):
        """加载当前配置到编辑器"""
        try:
            config_json = json.dumps(self.current_config, indent=2, ensure_ascii=False)
            self.config_text.delete("1.0", tk.END)
            self.config_text.insert("1.0", config_json)
        except:
            self.config_text.delete("1.0", tk.END)
            self.config_text.insert("1.0", "{}")
    
    def _load_default_config(self):
        """加载默认配置"""
        if not self.current_trainer_id:
            messagebox.showwarning("提示", get_text("MSG_NO_TRAINER"))
            return
        
        self._load_default_config_for_trainer(self.current_trainer_id)
    
    def _load_default_config_for_trainer(self, trainer_id):
        """为指定训练器加载默认配置"""
        template = self.training_center.generate_config_template(trainer_id)
        
        # 合并当前配置（保留用户已修改的值）
        merged_config = template.copy()
        merged_config.update(self.current_config)
        
        self.current_config = merged_config
        self._load_current_config()
    
    def _validate_json(self):
        """验证JSON格式"""
        try:
            config_text = self.config_text.get("1.0", tk.END).strip()
            if not config_text:
                config_text = "{}"
            
            parsed = json.loads(config_text)
            self.current_config = parsed
            
            messagebox.showinfo("验证通过", "JSON格式正确")
            return True
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON格式错误", f"第{e.lineno}行，第{e.colno}列: {e.msg}")
            return False
    
    def _run_health_check(self):
        """运行训练前体检"""
        # 验证并获取配置
        if not self._validate_json():
            return
        
        if not self.current_trainer_id:
            messagebox.showwarning("提示", get_text("MSG_NO_TRAINER"))
            return
        
        # 更新状态
        self.health_status_label.config(text=get_text("STATUS_CHECKING"), fg=self.accent_yellow)
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", "检查中...请稍候。\n")
        self.result_text.config(state="disabled")
        self.update()
        
        try:
            # 运行体检
            report = self.training_center.run_health_check(self.current_trainer_id, self.current_config)
            self.health_report = report
            
            # 更新状态显示
            status = report.get("overall_status", "pending")
            if status == "passed":
                self.health_status_label.config(text=get_text("STATUS_PASSED"), fg=self.accent_green)
            elif status == "warning":
                self.health_status_label.config(text=get_text("STATUS_WARNING"), fg=self.accent_yellow)
            elif status == "error":
                self.health_status_label.config(text=get_text("STATUS_ERROR"), fg=self.accent_red)
            else:
                self.health_status_label.config(text=get_text("STATUS_PENDING"), fg=self.text_sub)
            
            # 更新按钮状态（考虑训练器是否支持训练）
            trainers_list = self.training_center.get_available_trainers()
            current_trainer = next((t for t in trainers_list if t['trainer_id'] == self.current_trainer_id), {})
            is_placeholder = current_trainer.get('is_placeholder', True)
            can_train = current_trainer.get('can_train', False)
            
            if status in ["passed", "warning"] and can_train and not is_placeholder:
                self.start_training_btn.config(state="normal", bg="#3a6df0", text="启动训练")
            elif status in ["passed", "warning"] and (is_placeholder or not can_train):
                self.start_training_btn.config(state="normal", bg="#ff9d57", text="示例训练器")
            elif status == "error":
                self.start_training_btn.config(state="disabled", bg=self.border, text="存在错误")
            else:
                self.start_training_btn.config(state="disabled", bg=self.border, text="启动训练")
            
            # 显示结果
            result_text = self.training_center.export_health_report(report, "text")
            
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", result_text)
            self.result_text.config(state="disabled")
            
        except Exception as e:
            self.health_status_label.config(text=get_text("STATUS_ERROR"), fg=self.accent_red)
            
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", f"体检过程出错:\n{str(e)}")
            self.result_text.config(state="disabled")
    
    def _start_training(self):
        """启动训练"""
        # 检查是否为占位训练器
        trainers_list = self.training_center.get_available_trainers()
        current_trainer = next((t for t in trainers_list if t['trainer_id'] == self.current_trainer_id), {})
        
        is_placeholder = current_trainer.get('is_placeholder', True)
        can_train = current_trainer.get('can_train', False)
        
        if is_placeholder:
            messagebox.showinfo("占位训练器", "这是一个示例训练器，不实际执行训练。\n\n当前选择的是占位训练器，用于演示多训练器接入口。\n只有YOLOv8训练器可真实启动训练。")
            return
        
        if not can_train:
            messagebox.showwarning("暂不支持", "此训练器尚未实现真实训练功能。\n\n目前只有YOLOv8训练器可真实启动训练。")
            return
        
        if not self.health_report or not self.health_report.get("can_start_training", False):
            messagebox.showwarning("提示", get_text("MSG_CHECK_FIRST"))
            return
        
        # 保存配置到全局配置
        if hasattr(self.master, 'config_data') and isinstance(self.master.config_data, dict):
            if "training" not in self.master.config_data:
                self.master.config_data["training"] = {}
            self.master.config_data["training"].update(self.current_config)
            
            # 保存到配置文件
            try:
                from core.config_manager import save_config
                save_config(self.master.config_data)
            except:
                pass
        
        # 关闭训练中心窗口
        self.destroy()
        
        # 使用现有的训练监控启动训练
        if hasattr(self.master, 'show_training_window_placeholder'):
            try:
                # 更新配置
                self.master.config_data["training"] = self.current_config
                
                # 调用现有训练启动函数
                self.master.show_training_window_placeholder()
                messagebox.showinfo("训练启动", get_text("MSG_TRAINING_STARTED"))
            except Exception as e:
                messagebox.showerror("启动失败", f"训练启动失败: {str(e)}")
        else:
            messagebox.showwarning("功能不可用", "训练启动功能不可用，请使用训练监控按钮")
    
    def _open_monitor(self):
        """打开训练监控窗口"""
        if hasattr(self.master, '_open_training_monitor'):
            self.master._open_training_monitor()
        elif hasattr(self.master, 'root'):
            try:
                from ui.training_monitor_window import open_training_monitor
                open_training_monitor(self.master.root)
            except:
                messagebox.showerror("错误", "无法打开训练监控窗口")
    
    def _view_training_result(self):
        """查看训练结果"""
        try:
            from ui.training_result_window import TrainingResultWindow
            
            if not self.current_trainer_id:
                messagebox.showinfo("提示", "请先选择训练器")
                return
            
            # 使用训练中心管理器查找最新结果
            result_path = self.training_center.find_latest_training_result(self.current_trainer_id)
            
            if result_path and os.path.exists(result_path):
                # 打开结果窗口
                result_window = TrainingResultWindow(self, log_path=result_path)
                # 设置窗口标题
                exp_name = os.path.basename(os.path.dirname(result_path))
                result_window.title(f"{self.current_trainer_id}训练结果 - {exp_name}")
            else:
                # 如果没有找到结果，让用户选择文件
                from tkinter import filedialog
                
                # 根据训练器类型设置初始目录
                initial_dir = "."
                if self.current_trainer_id == "classification":
                    initial_dir = "runs/classification"
                elif self.current_trainer_id == "yolo_v8":
                    initial_dir = "runs/train"
                
                file_path = filedialog.askopenfilename(
                    title="选择训练结果文件",
                    filetypes=[("训练日志", "*.json"), ("所有文件", "*.*")],
                    initialdir=initial_dir
                )
                
                if file_path and os.path.exists(file_path):
                    result_window = TrainingResultWindow(self, log_path=file_path)
                else:
                    messagebox.showinfo("提示", 
                        f"未找到{self.current_trainer_id}训练结果文件。\n\n"
                        f"请先运行{self.current_trainer_id}训练，或手动选择训练日志文件。\n"
                        f"训练日志文件通常位于: {initial_dir}/实验名/training_log.json")
                
        except Exception as e:
            messagebox.showerror("错误", f"打开训练结果窗口失败: {str(e)}")
    
    def _view_training_history(self):
        """查看训练历史"""
        try:
            from ui.training_history_window import open_training_history
            
            # 获取当前训练器ID
            if not self.current_trainer_id:
                messagebox.showinfo("提示", "请先选择训练器")
                return
            
            # 打开历史窗口
            history_window = open_training_history(self, self.current_trainer_id)
            
            if history_window:
                # 设置窗口标题
                history_window.title(f"训练历史 - {self.current_trainer_id}")
            
        except ImportError as e:
            messagebox.showerror("错误", f"无法导入训练历史模块: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"打开训练历史窗口失败: {str(e)}")
    
    def destroy(self):
        """销毁窗口，清理回调"""
        if hasattr(self, 'language_manager'):
            self.language_manager.unregister_callback(self._refresh_ui_on_language_change)
        if hasattr(self, 'style_manager'):
            self.style_manager.unregister_callback(self._refresh_ui_on_style_change)
        super().destroy()


def open_training_center(master, config_data=None):
    """打开训练中心窗口（工厂函数）"""
    if master is not None and hasattr(master, "_training_center_window"):
        win = getattr(master, "_training_center_window")
        try:
            if win is not None and win.winfo_exists():
                win.deiconify()
                win.lift()
                win.focus_force()
                return win
        except:
            pass
    
    win = TrainingCenterWindow(master, config_data)
    
    if master is not None:
        try:
            master._training_center_window = win
            
            def _clear_ref():
                try:
                    if hasattr(master, "_training_center_window"):
                        master._training_center_window = None
                except:
                    pass
            
            win.protocol("WM_DELETE_WINDOW", lambda: (_clear_ref(), win.destroy()))
        except:
            pass
    
    return win


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.withdraw()
    
    test_config = {
        "training": {
            "data": "data.yaml",
            "model": "yolov8n.pt",
            "epochs": 100
        }
    }
    
    win = TrainingCenterWindow(root, test_config)
    root.mainloop()