#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
base_window.py - UI基础窗口类

功能：
1. 提供统一的样式管理
2. 提供统一的语言管理
3. 提供窗口基础配置
4. 为所有子窗口提供通用功能
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Any

from core.ui_style_manager import get_style_manager, UIStyle, UITheme
from core.language_manager import get_language_manager, t, Language


class BaseWindow(tk.Toplevel):
    """基础窗口类"""
    
    def __init__(self, master, title_key: str = None, **kwargs):
        """
        初始化基础窗口
        
        Args:
            master: 父窗口
            title_key: 窗口标题的文案键
            **kwargs: 传递给Toplevel的其他参数
        """
        super().__init__(master, **kwargs)
        self.master = master
        
        # UI管理器
        self.style_manager = get_style_manager()
        self.language_manager = get_language_manager()
        
        # 当前主题定义
        self.theme = self.style_manager.get_current_theme_definition()
        
        # 窗口标题
        if title_key:
            self.title(t(title_key))
        
        # 默认窗口配置
        self.geometry("1000x700")
        self.minsize(800, 500)
        
        # 设置背景色
        self.configure(bg=self.get_color("background"))
        
        # 设置窗口图标（如果有）
        self._set_window_icon()
        
        # 样式缓存
        self._style_cache = {}
        
        # 使窗口模态化
        self.transient(master)
        self.grab_set()
    
    def _set_window_icon(self):
        """设置窗口图标（子类可重写）"""
        # 预留图标设置
        pass
    
    def get_color(self, color_name: str) -> str:
        """获取颜色值"""
        return self.style_manager.get_color(color_name)
    
    def get_font(self, font_name: str) -> str:
        """获取字体值（返回字体元组或字符串）"""
        font_str = self.style_manager.get_font(font_name)
        # 简单解析字体字符串（实际应该更复杂）
        if "Microsoft YaHei" in font_str:
            return ("Microsoft YaHei", 10)
        elif "Segoe UI" in font_str:
            return ("Segoe UI", 10)
        else:
            return ("TkDefaultFont", 10)
    
    def get_spacing(self, spacing_name: str) -> int:
        """获取间距值"""
        return self.style_manager.get_spacing(spacing_name)
    
    def get_border_radius(self, radius_name: str) -> int:
        """获取圆角值"""
        return self.style_manager.get_border_radius(radius_name)
    
    def create_button(self, parent, text_key: str, command=None, 
                     style: str = "primary", **kwargs) -> tk.Button:
        """
        创建标准化按钮
        
        Args:
            parent: 父容器
            text_key: 按钮文本的文案键
            command: 点击命令
            style: 按钮样式（primary, secondary, danger, success）
            **kwargs: 传递给Button的其他参数
        
        Returns:
            创建的按钮
        """
        # 样式映射
        style_colors = {
            "primary": self.get_color("primary"),
            "secondary": self.get_color("secondary"),
            "danger": self.get_color("error"),
            "success": self.get_color("success"),
            "warning": self.get_color("warning"),
        }
        
        bg_color = style_colors.get(style, self.get_color("primary"))
        fg_color = "white"  # 简化处理
        
        # 默认样式
        default_kwargs = {
            "bg": bg_color,
            "fg": fg_color,
            "font": self.get_font("family_primary"),
            "relief": "flat",
            "padx": self.get_spacing("md"),
            "pady": self.get_spacing("sm"),
            "cursor": "hand2",
        }
        
        # 更新用户参数
        default_kwargs.update(kwargs)
        
        # 创建按钮
        btn = tk.Button(
            parent,
            text=t(text_key),
            command=command,
            **default_kwargs
        )
        
        # 绑定悬停效果
        self._bind_button_hover(btn, bg_color)
        
        return btn
    
    def _bind_button_hover(self, button: tk.Button, normal_bg: str):
        """绑定按钮悬停效果"""
        hover_bg = self.get_color("hover")
        active_bg = self.get_color("active")
        
        def on_enter(e):
            if button["state"] == "normal":
                button.config(bg=hover_bg)
        
        def on_leave(e):
            if button["state"] == "normal":
                button.config(bg=normal_bg)
        
        def on_press(e):
            if button["state"] == "normal":
                button.config(bg=active_bg)
        
        def on_release(e):
            if button["state"] == "normal":
                button.config(bg=hover_bg)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<ButtonPress-1>", on_press)
        button.bind("<ButtonRelease-1>", on_release)
    
    def create_label(self, parent, text_key: str, style: str = "normal", **kwargs) -> tk.Label:
        """
        创建标准化标签
        
        Args:
            parent: 父容器
            text_key: 标签文本的文案键
            style: 标签样式（normal, title, subtitle, muted）
            **kwargs: 传递给Label的其他参数
        """
        # 样式映射
        style_configs = {
            "normal": {
                "fg": self.get_color("text_primary"),
                "font": self.get_font("family_primary"),
            },
            "title": {
                "fg": self.get_color("text_primary"),
                "font": (self.get_font("family_primary")[0], 14, "bold"),
            },
            "subtitle": {
                "fg": self.get_color("text_primary"),
                "font": (self.get_font("family_primary")[0], 12, "bold"),
            },
            "muted": {
                "fg": self.get_color("text_secondary"),
                "font": self.get_font("family_primary"),
            },
        }
        
        default_kwargs = style_configs.get(style, style_configs["normal"])
        default_kwargs.update(kwargs)
        
        return tk.Label(
            parent,
            text=t(text_key),
            bg=parent.cget("bg") if "bg" not in kwargs else kwargs["bg"],
            **default_kwargs
        )
    
    def create_frame(self, parent, style: str = "card", **kwargs) -> tk.Frame:
        """
        创建标准化框架
        
        Args:
            parent: 父容器
            style: 框架样式（card, panel, transparent）
            **kwargs: 传递给Frame的其他参数
        """
        # 样式映射
        style_colors = {
            "card": self.get_color("surface"),
            "panel": self.get_color("background"),
            "transparent": parent.cget("bg"),
        }
        
        bg_color = style_colors.get(style, self.get_color("surface"))
        
        default_kwargs = {
            "bg": bg_color,
            "highlightthickness": 1 if style == "card" else 0,
            "highlightbackground": self.get_color("border") if style == "card" else "",
        }
        default_kwargs.update(kwargs)
        
        return tk.Frame(parent, **default_kwargs)
    
    def create_entry(self, parent, **kwargs) -> tk.Entry:
        """
        创建标准化输入框
        """
        default_kwargs = {
            "bg": self.get_color("surface"),
            "fg": self.get_color("text_primary"),
            "font": self.get_font("family_primary"),
            "relief": "flat",
            "highlightthickness": 1,
            "highlightbackground": self.get_color("border"),
            "highlightcolor": self.get_color("primary"),
            "insertbackground": self.get_color("primary"),
            "selectbackground": self.get_color("primary"),
            "selectforeground": "white",
        }
        default_kwargs.update(kwargs)
        
        return tk.Entry(parent, **default_kwargs)
    
    def create_text(self, parent, **kwargs) -> tk.Text:
        """
        创建标准化文本框
        """
        default_kwargs = {
            "bg": self.get_color("surface"),
            "fg": self.get_color("text_primary"),
            "font": self.get_font("family_primary"),
            "relief": "flat",
            "highlightthickness": 1,
            "highlightbackground": self.get_color("border"),
            "selectbackground": self.get_color("primary"),
            "selectforeground": "white",
            "wrap": "word",
        }
        default_kwargs.update(kwargs)
        
        return tk.Text(parent, **default_kwargs)
    
    def create_scrolledtext(self, parent, **kwargs) -> tk.scrolledtext.ScrolledText:
        """
        创建标准化滚动文本框
        """
        import tkinter.scrolledtext as scrolledtext
        
        default_kwargs = {
            "bg": self.get_color("surface"),
            "fg": self.get_color("text_primary"),
            "font": self.get_font("family_primary"),
            "relief": "flat",
            "highlightthickness": 1,
            "highlightbackground": self.get_color("border"),
            "selectbackground": self.get_color("primary"),
            "selectforeground": "white",
            "wrap": "word",
        }
        default_kwargs.update(kwargs)
        
        return scrolledtext.ScrolledText(parent, **default_kwargs)
    
    def show_message(self, title_key: str, message_key: str, 
                    message_type: str = "info"):
        """
        显示标准化消息框
        
        Args:
            title_key: 标题文案键
            message_key: 消息文案键
            message_type: 消息类型（info, warning, error, question）
        """
        import tkinter.messagebox as messagebox
        
        title = t(title_key)
        message = t(message_key)
        
        if message_type == "info":
            messagebox.showinfo(title, message)
        elif message_type == "warning":
            messagebox.showwarning(title, message)
        elif message_type == "error":
            messagebox.showerror(title, message)
        elif message_type == "question":
            return messagebox.askyesno(title, message)
        
        return None
    
    def refresh_ui(self):
        """刷新UI（语言或样式变更后调用）"""
        # 更新窗口标题
        if hasattr(self, 'title_key'):
            self.title(t(self.title_key))
        
        # 重新配置窗口背景
        self.configure(bg=self.get_color("background"))
        
        # 通知子类更新
        self._on_refresh_ui()
    
    def _on_refresh_ui(self):
        """子类可重写的UI刷新钩子"""
        pass
    
    def apply_style_to_widget(self, widget, widget_type: str = None):
        """
        应用样式到小部件
        
        Args:
            widget: 小部件实例
            widget_type: 小部件类型（自动检测）
        """
        # 根据小部件类型应用样式
        if isinstance(widget, tk.Button):
            # 按钮样式
            pass
        elif isinstance(widget, tk.Label):
            # 标签样式
            pass
        # 其他小部件...
    
    def set_window_opacity(self, opacity: float):
        """设置窗口透明度"""
        self.style_manager.set_opacity(opacity)
        self.attributes("-alpha", opacity)