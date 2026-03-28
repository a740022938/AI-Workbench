import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.config_manager import load_config, save_config
from core.language_manager import t, get_language_manager
from core.ui_style_manager import get_style_manager

def get_text(key):
    """根据当前语言配置获取文本（兼容旧版本）"""
    return t(key)


class SettingsWindow(tk.Toplevel):
    def __init__(self, master, on_saved_callback=None):
        super().__init__(master)
        self.master = master
        self.on_saved_callback = on_saved_callback

        self.title(get_text("BTN_SETTINGS"))
        self.geometry("820x560")
        self.minsize(760, 520)
        self.configure(bg="#16181d")
        self.transient(master)
        self.grab_set()

        self.config_data = load_config()

        self.bg_main = "#16181d"
        self.bg_left = "#1b1f26"
        self.bg_right = "#20242c"
        self.bg_card = "#252a33"
        self.text_main = "#f5f7fa"
        self.text_sub = "#aeb6c2"
        self.border = "#2d3440"
        self.btn_bg = "#2a303a"
        self.btn_hover = "#343b47"

        self.current_page = None
        self.pages = {}
        self.label_refs = {}  # 存储各页面标签引用：page_name -> [(label_widget, key), ...]

        # 初始化语言管理器
        self.language_manager = get_language_manager()
        self.language_manager.register_callback(self._refresh_ui_on_language_change)

        # 初始化风格管理器
        self.style_manager = get_style_manager()
        self.style_manager.register_callback(self._refresh_ui_on_style_change)

        self._build_ui()
        self.show_page("paths")

    def _refresh_ui_on_language_change(self):
        """语言切换时刷新UI文案"""
        # 更新窗口标题
        self.title(get_text("BTN_SETTINGS"))
        
        # 更新导航按钮文本
        for page_key, btn in self.nav_buttons.items():
            if page_key == "paths":
                btn.config(text=get_text("NAV_PATHS"))
            elif page_key == "behavior":
                btn.config(text=get_text("NAV_BEHAVIOR"))
            elif page_key == "inference":
                btn.config(text=get_text("NAV_INFERENCE"))
            elif page_key == "training":
                btn.config(text=get_text("NAV_TRAINING"))
            elif page_key == "appearance":
                btn.config(text=get_text("NAV_APPEARANCE"))
            elif page_key == "language":
                btn.config(text=get_text("NAV_LANGUAGE"))
        
        # 更新当前页内容
        if self.current_page and self.current_page in self.pages:
            self._refresh_current_page()
        
        # 更新取消按钮文本
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.config(text=get_text("BTN_CANCEL"))
        
        # 更新保存按钮文本
        if hasattr(self, 'save_btn'):
            self.save_btn.config(text=get_text("BTN_SAVE_SETTINGS"))
    
    def _refresh_ui_on_style_change(self):
        """风格切换时刷新UI样式"""
        # 重新计算颜色
        self._update_colors_from_style()
        # 刷新当前窗口颜色
        self._apply_style_to_window()

    def _update_colors_from_style(self):
        """从风格管理器更新颜色变量"""
        theme = self.style_manager.get_current_theme_definition()
        self.bg_main = theme.colors.get("background", "#16181d")
        self.bg_left = theme.colors.get("surface", "#252a33")
        self.bg_right = theme.colors.get("surface", "#252a33")  # 使用surface或稍亮
        self.bg_card = theme.colors.get("surface", "#252a33")
        self.text_main = theme.colors.get("text_primary", "#f5f7fa")
        self.text_sub = theme.colors.get("text_secondary", "#aeb6c2")
        self.border = theme.colors.get("border", "#2d3440")
        self.btn_bg = theme.colors.get("hover", "#2d3440")
        self.btn_hover = theme.colors.get("active", "#343b47")

    def _apply_style_to_window(self):
        """将样式应用到当前窗口"""
        # 更新窗口背景
        self.configure(bg=self.bg_main)
        # 更新左侧导航背景
        if hasattr(self, 'left_nav'):
            self.left_nav.config(bg=self.bg_left)
        # 更新内容区域背景
        if hasattr(self, 'content_frame'):
            self.content_frame.config(bg=self.bg_right)
        # 更新所有页面的背景和颜色
        for page in self.pages.values():
            page.config(bg=self.bg_right)
        # 更新导航按钮颜色
        for btn in self.nav_buttons.values():
            btn.config(bg=self.btn_bg, fg=self.text_main, activebackground=self.btn_hover, activeforeground=self.text_main)
        # 刷新当前页标签颜色（通过刷新当前页）
        if self.current_page and self.current_page in self.pages:
            self._refresh_current_page()

    def _refresh_current_page(self):
        """刷新当前页内容"""
        if not self.current_page or self.current_page not in self.pages:
            return
        
        page = self.pages[self.current_page]
        
        # 更新页面标题和子标题
        if hasattr(page, 'title_label') and hasattr(page, 'subtitle_label'):
            title_key = None
            subtitle_key = None
            
            if self.current_page == "paths":
                title_key = "TITLE_PATHS"
                subtitle_key = "SUBTITLE_PATHS"
            elif self.current_page == "behavior":
                title_key = "TITLE_BEHAVIOR"
                subtitle_key = "SUBTITLE_BEHAVIOR"
            elif self.current_page == "inference":
                title_key = "TITLE_INFERENCE"
                subtitle_key = "SUBTITLE_INFERENCE"
            elif self.current_page == "training":
                title_key = "TITLE_TRAINING"
                subtitle_key = "SUBTITLE_TRAINING"
            elif self.current_page == "appearance":
                title_key = "TITLE_APPEARANCE"
                subtitle_key = "SUBTITLE_APPEARANCE"
            elif self.current_page == "language":
                title_key = "TITLE_LANGUAGE"
                subtitle_key = "SUBTITLE_LANGUAGE"
            
            if title_key and subtitle_key:
                page.title_label.config(text=get_text(title_key))
                page.subtitle_label.config(text=get_text(subtitle_key))
        
        # 刷新存储的标签引用
        if self.current_page in self.label_refs:
            for widget, key in self.label_refs[self.current_page]:
                try:
                    widget.config(text=get_text(key))
                except Exception as e:
                    print(f"刷新标签失败 {key}: {e}")
    
    def destroy(self):
        """销毁窗口，清理回调"""
        if hasattr(self, 'language_manager'):
            self.language_manager.unregister_callback(self._refresh_ui_on_language_change)
        if hasattr(self, 'style_manager'):
            self.style_manager.unregister_callback(self._refresh_ui_on_style_change)
        super().destroy()

    def _build_ui(self):
        container = tk.Frame(self, bg=self.bg_main)
        container.pack(fill="both", expand=True, padx=14, pady=14)

        left_nav = tk.Frame(container, bg=self.bg_left, width=180, highlightthickness=1, highlightbackground=self.border)
        left_nav.pack(side="left", fill="y", padx=(0, 8))
        left_nav.pack_propagate(False)

        tk.Label(left_nav, text=get_text("BTN_SETTINGS"), bg=self.bg_left, fg=self.text_main, font=("Microsoft YaHei", 14, "bold")).pack(anchor="w", padx=14, pady=(16, 10))

        self.nav_buttons = {}
        self.nav_buttons["paths"] = self._create_nav_button(left_nav, get_text("NAV_PATHS"), lambda: self.show_page("paths"))
        self.nav_buttons["behavior"] = self._create_nav_button(left_nav, get_text("NAV_BEHAVIOR"), lambda: self.show_page("behavior"))
        self.nav_buttons["inference"] = self._create_nav_button(left_nav, get_text("NAV_INFERENCE"), lambda: self.show_page("inference"))
        self.nav_buttons["training"] = self._create_nav_button(left_nav, get_text("NAV_TRAINING"), lambda: self.show_page("training"))
        self.nav_buttons["appearance"] = self._create_nav_button(left_nav, get_text("NAV_APPEARANCE"), lambda: self.show_page("appearance"))
        self.nav_buttons["language"] = self._create_nav_button(left_nav, get_text("NAV_LANGUAGE"), lambda: self.show_page("language"))

        self.nav_buttons["paths"].pack(fill="x", padx=10, pady=4)
        self.nav_buttons["behavior"].pack(fill="x", padx=10, pady=4)
        self.nav_buttons["inference"].pack(fill="x", padx=10, pady=4)
        self.nav_buttons["training"].pack(fill="x", padx=10, pady=4)
        self.nav_buttons["appearance"].pack(fill="x", padx=10, pady=4)
        self.nav_buttons["language"].pack(fill="x", padx=10, pady=4)

        right_area = tk.Frame(container, bg=self.bg_right, highlightthickness=1, highlightbackground=self.border)
        right_area.pack(side="right", fill="both", expand=True)

        self.content_frame = tk.Frame(right_area, bg=self.bg_right)
        self.content_frame.pack(fill="both", expand=True, padx=16, pady=16)

        bottom_bar = tk.Frame(right_area, bg=self.bg_right)
        bottom_bar.pack(fill="x", padx=16, pady=(0, 16))

        self.cancel_btn = tk.Button(bottom_bar, text=get_text("BTN_CANCEL"), bg=self.btn_bg, fg=self.text_main, relief="flat", activebackground=self.btn_hover, activeforeground=self.text_main, command=self.destroy)
        self.cancel_btn.pack(side="right", padx=(8, 0))
        self.save_btn = tk.Button(bottom_bar, text=get_text("BTN_SAVE_SETTINGS"), bg="#3a6df0", fg="white", relief="flat", activebackground="#4b7cff", activeforeground="white", command=self.save_settings)
        self.save_btn.pack(side="right")

        self._build_pages()

    def _create_nav_button(self, parent, text, command):
        btn = tk.Label(parent, text=text, bg=self.btn_bg, fg=self.text_main, anchor="w", padx=12, pady=10, cursor="hand2", font=("Microsoft YaHei", 10))
        btn.bind("<Enter>", lambda e: btn.config(bg=self.btn_hover))
        btn.bind("<Leave>", lambda e: self._reset_nav_button(btn))
        btn.bind("<Button-1>", lambda e: command())
        return btn

    def _reset_nav_button(self, btn):
        if getattr(btn, "is_active", False):
            btn.config(bg="#40516d")
        else:
            btn.config(bg=self.btn_bg)

    def show_page(self, page_name):
        if self.current_page:
            self.pages[self.current_page].pack_forget()

        self.current_page = page_name
        self.pages[page_name].pack(fill="both", expand=True)

        for name, btn in self.nav_buttons.items():
            btn.is_active = (name == page_name)
            self._reset_nav_button(btn)

    def _build_pages(self):
        self.pages["paths"] = self._build_paths_page()
        self.pages["behavior"] = self._build_behavior_page()
        self.pages["inference"] = self._build_inference_page()
        self.pages["training"] = self._build_training_page()
        self.pages["appearance"] = self._build_appearance_page()
        self.pages["language"] = self._build_language_page()
        self.pages["language"] = self._build_language_page()

    def _page_title(self, parent, title, subtitle):
        title_label = tk.Label(parent, text=title, bg=self.bg_right, fg=self.text_main, font=("Microsoft YaHei", 13, "bold"))
        title_label.pack(anchor="w")
        subtitle_label = tk.Label(parent, text=subtitle, bg=self.bg_right, fg=self.text_sub, font=("Microsoft YaHei", 9))
        subtitle_label.pack(anchor="w", pady=(4, 14))
        # 存储引用，用于语言刷新
        parent.title_label = title_label
        parent.subtitle_label = subtitle_label

    def _build_paths_page(self):
        page = tk.Frame(self.content_frame, bg=self.bg_right)
        page.page_name = "paths"
        self._page_title(page, get_text("TITLE_PATHS"), get_text("SUBTITLE_PATHS"))

        self.path_vars = {
            "image_dir": tk.StringVar(value=self.config_data["paths"].get("image_dir", "")),
            "label_dir": tk.StringVar(value=self.config_data["paths"].get("label_dir", "")),
            "model_path": tk.StringVar(value=self.config_data["paths"].get("model_path", "")),
            "output_dataset_dir": tk.StringVar(value=self.config_data["paths"].get("output_dataset_dir", "")),
            "bad_cases_dir": tk.StringVar(value=self.config_data["paths"].get("bad_cases_dir", "")),
        }

        self._add_path_row(page, "LABEL_IMAGE_DIR", self.path_vars["image_dir"], False)
        self._add_path_row(page, "LABEL_LABEL_DIR", self.path_vars["label_dir"], False)
        self._add_path_row(page, "LABEL_MODEL_PATH", self.path_vars["model_path"], True)
        self._add_path_row(page, "LABEL_OUTPUT_DIR", self.path_vars["output_dataset_dir"], False)
        self._add_path_row(page, "LABEL_BAD_CASE_DIR", self.path_vars["bad_cases_dir"], False)
        return page

    def _add_path_row(self, parent, key, var, is_file):
        card = tk.Frame(parent, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        card.pack(fill="x", pady=6)

        label_widget = tk.Label(card, text=get_text(key), bg=self.bg_card, fg=self.text_main, font=("Microsoft YaHei", 10, "bold"))
        label_widget.pack(anchor="w", padx=12, pady=(10, 4))
        # 存储标签引用用于语言刷新
        page_name = getattr(parent, 'page_name', None)
        if page_name:
            if page_name not in self.label_refs:
                self.label_refs[page_name] = []
            self.label_refs[page_name].append((label_widget, key))

        row = tk.Frame(card, bg=self.bg_card)
        row.pack(fill="x", padx=12, pady=(0, 12))

        entry = tk.Entry(row, textvariable=var, bg="#1b2028", fg=self.text_main, insertbackground=self.text_main, relief="flat", font=("Consolas", 10))
        entry.pack(side="left", fill="x", expand=True, ipady=6)

        def browse():
            if is_file:
                path = filedialog.askopenfilename(title=f"{get_text('BTN_SELECT')}{get_text(key)}", filetypes=[("模型文件", "*.pt *.onnx *.pth"), ("所有文件", "*.*")])
            else:
                path = filedialog.askdirectory(title=f"{get_text('BTN_SELECT')}{get_text(key)}")
            if path:
                var.set(path)

        button_widget = tk.Button(row, text=get_text("BTN_SELECT"), bg=self.btn_bg, fg=self.text_main, relief="flat", activebackground=self.btn_hover, activeforeground=self.text_main, command=browse)
        button_widget.pack(side="left", padx=(8, 0))
        # 存储按钮引用用于语言刷新
        page_name = getattr(parent, 'page_name', None)
        if page_name:
            if page_name not in self.label_refs:
                self.label_refs[page_name] = []
            self.label_refs[page_name].append((button_widget, "BTN_SELECT"))

    def _build_training_page(self):
        page = tk.Frame(self.content_frame, bg=self.bg_right)
        self._page_title(page, get_text("TITLE_TRAINING"), get_text("SUBTITLE_TRAINING"))

        self.training_vars = {
            "epochs": tk.StringVar(value=str(self.config_data.get("training", {}).get("epochs", 100))),
            "batch_size": tk.StringVar(value=str(self.config_data.get("training", {}).get("batch_size", 16))),
            "imgsz": tk.StringVar(value=str(self.config_data.get("training", {}).get("imgsz", 640))),
            "device": tk.StringVar(value=self.config_data.get("training", {}).get("device", "0")),
            "project": tk.StringVar(value=self.config_data.get("training", {}).get("project", "runs/train")),
            "name": tk.StringVar(value=self.config_data.get("training", {}).get("name", "exp"))
        }

        for key, label in [("epochs", get_text("LABEL_EPOCHS")), ("batch_size", get_text("LABEL_BATCH_SIZE")), ("imgsz", get_text("LABEL_IMGSZ")), ("device", get_text("LABEL_DEVICE")), ("project", get_text("LABEL_PROJECT")), ("name", get_text("LABEL_NAME"))]:
            card = tk.Frame(page, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
            card.pack(fill="x", pady=6)
            tk.Label(card, text=label, bg=self.bg_card, fg=self.text_main, font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
            row = tk.Frame(card, bg=self.bg_card)
            row.pack(fill="x", padx=12, pady=(0, 12))
            entry = tk.Entry(row, textvariable=self.training_vars[key], bg="#1b2028", fg=self.text_main, insertbackground=self.text_main, relief="flat", font=("Consolas", 10))
            entry.pack(side="left", fill="x", expand=True, ipady=6)
        return page

    def _build_behavior_page(self):
        page = tk.Frame(self.content_frame, bg=self.bg_right)
        page.page_name = "behavior"
        self._page_title(page, get_text("TITLE_BEHAVIOR"), get_text("SUBTITLE_BEHAVIOR"))

        self.auto_save_var = tk.BooleanVar(value=self.config_data["behavior"].get("auto_save", True))
        self.auto_save_nav_var = tk.BooleanVar(value=self.config_data["behavior"].get("auto_save_on_navigate", True))

        card = tk.Frame(page, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        card.pack(fill="x", pady=6)

        check1 = tk.Checkbutton(card, text=get_text("CHECK_AUTO_SAVE"), variable=self.auto_save_var, bg=self.bg_card, fg=self.text_main, activebackground=self.bg_card, activeforeground=self.text_main, selectcolor="#1b2028", font=("Microsoft YaHei", 10))
        check1.pack(anchor="w", padx=12, pady=(12, 8))
        check2 = tk.Checkbutton(card, text=get_text("CHECK_AUTO_SAVE_NAV"), variable=self.auto_save_nav_var, bg=self.bg_card, fg=self.text_main, activebackground=self.bg_card, activeforeground=self.text_main, selectcolor="#1b2028", font=("Microsoft YaHei", 10))
        check2.pack(anchor="w", padx=12, pady=(0, 12))
        
        # 存储复选框引用用于语言刷新
        if "behavior" not in self.label_refs:
            self.label_refs["behavior"] = []
        self.label_refs["behavior"].append((check1, "CHECK_AUTO_SAVE"))
        self.label_refs["behavior"].append((check2, "CHECK_AUTO_SAVE_NAV"))
        
        return page

    def _build_inference_page(self):
        page = tk.Frame(self.content_frame, bg=self.bg_right)
        self._page_title(page, get_text("TITLE_INFERENCE"), get_text("SUBTITLE_INFERENCE"))

        self.auto_infer_var = tk.BooleanVar(value=self.config_data.get("inference", {}).get("auto_infer_on_open", False))
        self.enable_openclaw_var = tk.BooleanVar(value=self.config_data.get("inference", {}).get("enable_openclaw", True))

        card = tk.Frame(page, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        card.pack(fill="x", pady=6)

        tk.Checkbutton(card, text=get_text("CHECK_AUTO_INFER"), variable=self.auto_infer_var, bg=self.bg_card, fg=self.text_main, activebackground=self.bg_card, activeforeground=self.text_main, selectcolor="#1b2028", font=("Microsoft YaHei", 10)).pack(anchor="w", padx=12, pady=(12, 8))
        tk.Checkbutton(card, text=get_text("CHECK_ENABLE_OPENCLAW"), variable=self.enable_openclaw_var, bg=self.bg_card, fg=self.text_main, activebackground=self.bg_card, activeforeground=self.text_main, selectcolor="#1b2028", font=("Microsoft YaHei", 10)).pack(anchor="w", padx=12, pady=(0, 12))
        return page

    def _build_appearance_page(self):
        page = tk.Frame(self.content_frame, bg=self.bg_right)
        page.page_name = "appearance"
        self._page_title(page, get_text("TITLE_APPEARANCE"), get_text("SUBTITLE_APPEARANCE"))

        self.alpha_var = tk.DoubleVar(value=self.config_data.get("ui", {}).get("alpha", 0.96))

        card = tk.Frame(page, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        card.pack(fill="x", pady=6)

        label_opacity = tk.Label(card, text=get_text("LABEL_OPACITY"), bg=self.bg_card, fg=self.text_main, font=("Microsoft YaHei", 10, "bold"))
        label_opacity.pack(anchor="w", padx=12, pady=(12, 6))

        self.alpha_value_label = tk.Label(card, text=f"{int(self.alpha_var.get() * 100)}%", bg=self.bg_card, fg=self.text_sub, font=("Microsoft YaHei", 9))
        self.alpha_value_label.pack(anchor="w", padx=12, pady=(0, 4))

        scale = tk.Scale(card, from_=85, to=100, orient="horizontal", bg=self.bg_card, fg=self.text_sub, troughcolor="#151922", highlightthickness=0, bd=0, activebackground="#6ea8fe", command=self._on_alpha_change)
        scale.set(int(self.alpha_var.get() * 100))
        scale.pack(fill="x", padx=12, pady=(0, 12))
        
        # 存储标签引用用于语言刷新
        if "appearance" not in self.label_refs:
            self.label_refs["appearance"] = []
        self.label_refs["appearance"].append((label_opacity, "LABEL_OPACITY"))
        
        # ==================== UI风格选择卡片 ====================
        style_card = tk.Frame(page, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        style_card.pack(fill="x", pady=(12, 6))
        
        label_style = tk.Label(style_card, text=get_text("LABEL_UI_STYLE"), bg=self.bg_card, fg=self.text_main, font=("Microsoft YaHei", 10, "bold"))
        label_style.pack(anchor="w", padx=12, pady=(12, 6))
        
        # 获取可用风格列表
        available_styles = self.style_manager.get_available_styles()
        style_display_names = [style["display_name"] for style in available_styles]
        style_values = [style["value"] for style in available_styles]
        
        # 当前风格
        current_style = self.style_manager.current_style.value
        current_index = style_values.index(current_style) if current_style in style_values else 0
        
        self.style_var = tk.StringVar(value=style_display_names[current_index])
        
        style_combo = ttk.Combobox(style_card, textvariable=self.style_var, values=style_display_names, state="readonly", width=20)
        style_combo.pack(anchor="w", padx=12, pady=(0, 8))
        style_combo.bind("<<ComboboxSelected>>", self._on_style_changed)
        
        # 风格描述
        style_desc_label = tk.Label(style_card, text=available_styles[current_index]["description"], bg=self.bg_card, fg=self.text_sub, font=("Microsoft YaHei", 9), wraplength=300, justify="left")
        style_desc_label.pack(anchor="w", padx=12, pady=(0, 12))
        
        # 存储引用用于语言刷新和风格刷新
        self.style_desc_label = style_desc_label
        self.label_refs["appearance"].append((label_style, "LABEL_UI_STYLE"))
        
        return page

    def _on_alpha_change(self, value):
        alpha = float(value) / 100
        self.alpha_var.set(alpha)
        self.alpha_value_label.config(text=f"{int(alpha * 100)}%")

    def _on_style_changed(self, event):
        """处理UI风格切换"""
        selected_display = self.style_var.get()
        
        # 获取可用风格列表
        available_styles = self.style_manager.get_available_styles()
        style_display_names = [style["display_name"] for style in available_styles]
        style_values = [style["value"] for style in available_styles]
        
        # 找到对应的风格值
        if selected_display in style_display_names:
            index = style_display_names.index(selected_display)
            style_value = style_values[index]
            
            # 设置新风格
            if style_value == "win11":
                self.style_manager.set_style(self.style_manager.UIStyle.WIN11)
            elif style_value == "apple":
                self.style_manager.set_style(self.style_manager.UIStyle.APPLE)
            elif style_value == "chatgpt":
                self.style_manager.set_style(self.style_manager.UIStyle.CHATGPT)
            
            # 更新描述文本
            if hasattr(self, 'style_desc_label'):
                self.style_desc_label.config(text=available_styles[index]["description"])

    def _build_language_page(self):
        page = tk.Frame(self.content_frame, bg=self.bg_right)
        page.page_name = "language"
        self._page_title(page, get_text("TITLE_LANGUAGE"), get_text("SUBTITLE_LANGUAGE"))

        lang_map_display = {"zh_CN": "简体中文", "en_US": "English"}
        lang_map_value = {"简体中文": "zh_CN", "English": "en_US"}
        self._lang_map_value = lang_map_value

        current_lang = self.config_data.get("ui", {}).get("language", "zh_CN")
        display_value = lang_map_display.get(current_lang, "简体中文")

        self.language_var = tk.StringVar(value=display_value)

        card = tk.Frame(page, bg=self.bg_card, highlightthickness=1, highlightbackground=self.border)
        card.pack(fill="x", pady=6)

        label_language = tk.Label(card, text=get_text("LABEL_UI_LANGUAGE"), bg=self.bg_card, fg=self.text_main, font=("Microsoft YaHei", 10, "bold"))
        label_language.pack(anchor="w", padx=12, pady=(12, 6))

        combo = ttk.Combobox(card, textvariable=self.language_var, values=["简体中文", "English"], state="readonly", width=20)
        combo.pack(anchor="w", padx=12, pady=(0, 12))
        
        # 存储标签引用用于语言刷新
        if "language" not in self.label_refs:
            self.label_refs["language"] = []
        self.label_refs["language"].append((label_language, "LABEL_UI_LANGUAGE"))
        
        return page

    def save_settings(self):
        try:
            self.config_data["paths"]["image_dir"] = self.path_vars["image_dir"].get().strip()
            self.config_data["paths"]["label_dir"] = self.path_vars["label_dir"].get().strip()
            self.config_data["paths"]["model_path"] = self.path_vars["model_path"].get().strip()
            self.config_data["paths"]["output_dataset_dir"] = self.path_vars["output_dataset_dir"].get().strip()
            self.config_data["paths"]["bad_cases_dir"] = self.path_vars["bad_cases_dir"].get().strip()

            self.config_data["behavior"]["auto_save"] = self.auto_save_var.get()
            self.config_data["behavior"]["auto_save_on_navigate"] = self.auto_save_nav_var.get()

            if "inference" not in self.config_data:
                self.config_data["inference"] = {}
            self.config_data["inference"]["auto_infer_on_open"] = self.auto_infer_var.get()
            self.config_data["inference"]["enable_openclaw"] = self.enable_openclaw_var.get()

            if "training" not in self.config_data:
                self.config_data["training"] = {}
            self.config_data["training"]["epochs"] = int(self.training_vars["epochs"].get() or 100)
            self.config_data["training"]["batch_size"] = int(self.training_vars["batch_size"].get() or 16)
            self.config_data["training"]["imgsz"] = int(self.training_vars["imgsz"].get() or 640)
            self.config_data["training"]["device"] = self.training_vars["device"].get().strip() or "0"
            self.config_data["training"]["project"] = self.training_vars["project"].get().strip() or "runs/train"
            self.config_data["training"]["name"] = self.training_vars["name"].get().strip() or "exp"

            if "ui" not in self.config_data:
                self.config_data["ui"] = {}
            self.config_data["ui"]["alpha"] = round(self.alpha_var.get(), 2)
            self.config_data["ui"]["language"] = self._lang_map_value.get(self.language_var.get(), "zh_CN")
            # 保存UI风格
            self.config_data["ui"]["style"] = self.style_manager.current_style.value

            save_config(self.config_data)

            if self.on_saved_callback:
                self.on_saved_callback(self.config_data)

            messagebox.showinfo(get_text("MSG_SUCCESS"), get_text("MSG_SETTINGS_SAVED"))
            self.destroy()
        except Exception as e:
            messagebox.showerror(get_text("MSG_ERROR"), f"{get_text('MSG_SETTINGS_SAVE_ERROR')}：\n{e}")
