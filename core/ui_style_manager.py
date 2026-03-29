#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ui_style_manager.py - UI风格管理器

功能：
1. 管理三种预设风格：Win11, Apple, ChatGPT
2. 管理主题模式：light/dark
3. 管理窗口透明度
4. 提供统一的样式定义和获取接口
5. UI配置持久化
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field, asdict


class UIStyle(Enum):
    """UI风格枚举"""
    WIN11 = "win11"
    APPLE = "apple"
    CHATGPT = "chatgpt"
    
    @classmethod
    def from_string(cls, value: str) -> 'UIStyle':
        """从字符串转换为枚举"""
        value_lower = value.lower()
        for style in cls:
            if style.value == value_lower:
                return style
        return cls.WIN11  # 默认风格


class UITheme(Enum):
    """主题模式枚举"""
    LIGHT = "light"
    DARK = "dark"
    
    @classmethod
    def from_string(cls, value: str) -> 'UITheme':
        """从字符串转换为枚举"""
        value_lower = value.lower()
        for theme in cls:
            if theme.value == value_lower:
                return theme
        return cls.DARK  # 默认暗色主题


@dataclass
class UIStyleDefinition:
    """UI风格定义"""
    name: str
    display_name: str
    description: str
    
    # 颜色定义
    colors: Dict[str, str]
    
    # 字体定义
    fonts: Dict[str, str]
    
    # 间距定义
    spacing: Dict[str, int]
    
    # 圆角定义
    borderRadius: Dict[str, int]
    
    # 其他样式属性
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIThemeDefinition:
    """UI主题定义（基于风格）"""
    style: UIStyle
    theme: UITheme
    
    # 具体样式值（合并风格和主题）
    colors: Dict[str, str]
    fonts: Dict[str, str]
    spacing: Dict[str, int]
    borderRadius: Dict[str, int]
    
    # 透明度
    opacity: float = 1.0
    
    # 其他属性
    extra: Dict[str, Any] = field(default_factory=dict)


class UIStyleManager:
    """UI风格管理器"""
    
    def __init__(self, config_dir: str = None):
        """
        初始化风格管理器
        
        Args:
            config_dir: 配置目录，如果为None则使用默认目录
        """
        if config_dir is None:
            # 默认目录在当前工作目录下
            config_dir = os.path.join(os.getcwd(), "config", "ui")
        
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "ui_config.json")
        
        # 创建目录
        os.makedirs(config_dir, exist_ok=True)
        
        # 当前配置
        self.current_style: UIStyle = UIStyle.WIN11
        self.current_theme: UITheme = UITheme.DARK
        self.current_opacity: float = 1.0
        
        # 回调列表
        self._callbacks: List[callable] = []
        
        # 风格定义（预设）
        self._style_definitions: Dict[UIStyle, UIStyleDefinition] = {}
        self._theme_definitions: Dict[str, UIThemeDefinition] = {}  # key: f"{style.value}_{theme.value}"
        
        # 初始化风格定义
        self._init_style_definitions()
        
        # 加载配置
        self.load_config()
    
    def _init_style_definitions(self):
        """初始化风格定义"""
        # Win11 风格
        win11_style = UIStyleDefinition(
            name="win11",
            display_name="Windows 11",
            description="Windows 11 风格的现代UI",
            colors={
                "primary": "#0078d4",
                "secondary": "#605e5c",
                "success": "#107c10",
                "warning": "#ffb900",
                "error": "#d13438",
                "background": "#f3f2f1",
                "surface": "#ffffff",
                "text_primary": "#323130",
                "text_secondary": "#605e5c",
                "border": "#edebe9",
                "hover": "#f3f2f1",
                "active": "#edebe9",
            },
            fonts={
                "family_primary": "Segoe UI, Microsoft YaHei, sans-serif",
                "family_mono": "Consolas, Cascadia Mono, monospace",
                "size_small": "11px",
                "size_normal": "13px",
                "size_large": "15px",
                "size_title": "20px",
                "weight_normal": "400",
                "weight_bold": "600",
            },
            spacing={
                "xs": 4,
                "sm": 8,
                "md": 12,
                "lg": 16,
                "xl": 24,
                "xxl": 32,
            },
            borderRadius={
                "none": 0,
                "sm": 2,
                "md": 4,
                "lg": 8,
                "full": 9999,
            }
        )
        self._style_definitions[UIStyle.WIN11] = win11_style
        
        # Apple 风格
        apple_style = UIStyleDefinition(
            name="apple",
            display_name="Apple",
            description="macOS 风格的简洁UI",
            colors={
                "primary": "#007aff",
                "secondary": "#8e8e93",
                "success": "#34c759",
                "warning": "#ff9500",
                "error": "#ff3b30",
                "background": "#f2f2f7",
                "surface": "#ffffff",
                "text_primary": "#000000",
                "text_secondary": "#8e8e93",
                "border": "#c7c7cc",
                "hover": "#e5e5ea",
                "active": "#d1d1d6",
            },
            fonts={
                "family_primary": "-apple-system, BlinkMacSystemFont, 'SF Pro', Microsoft YaHei, sans-serif",
                "family_mono": "Menlo, Monaco, 'Cascadia Mono', monospace",
                "size_small": "12px",
                "size_normal": "14px",
                "size_large": "17px",
                "size_title": "22px",
                "weight_normal": "400",
                "weight_bold": "600",
            },
            spacing={
                "xs": 6,
                "sm": 12,
                "md": 16,
                "lg": 20,
                "xl": 28,
                "xxl": 36,
            },
            borderRadius={
                "none": 0,
                "sm": 6,
                "md": 10,
                "lg": 14,
                "full": 9999,
            }
        )
        self._style_definitions[UIStyle.APPLE] = apple_style
        
        # ChatGPT 风格
        chatgpt_style = UIStyleDefinition(
            name="chatgpt",
            display_name="ChatGPT",
            description="ChatGPT 风格的现代AI界面",
            colors={
                "primary": "#10a37f",
                "secondary": "#6b7280",
                "success": "#10a37f",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "background": "#ffffff",
                "surface": "#f9fafb",
                "text_primary": "#111827",
                "text_secondary": "#6b7280",
                "border": "#e5e7eb",
                "hover": "#f3f4f6",
                "active": "#e5e7eb",
            },
            fonts={
                "family_primary": "Inter, -apple-system, Microsoft YaHei, sans-serif",
                "family_mono": "JetBrains Mono, 'Cascadia Mono', monospace",
                "size_small": "12px",
                "size_normal": "14px",
                "size_large": "16px",
                "size_title": "18px",
                "weight_normal": "400",
                "weight_bold": "600",
            },
            spacing={
                "xs": 4,
                "sm": 8,
                "md": 12,
                "lg": 16,
                "xl": 20,
                "xxl": 24,
            },
            borderRadius={
                "none": 0,
                "sm": 4,
                "md": 8,
                "lg": 12,
                "full": 9999,
            }
        )
        self._style_definitions[UIStyle.CHATGPT] = chatgpt_style
        
        # 生成暗色主题变体
        self._generate_theme_definitions()
    
    def _generate_theme_definitions(self):
        """生成主题定义（明暗变体）"""
        for style_enum, style_def in self._style_definitions.items():
            # 亮色主题（直接使用风格定义）
            light_theme = UIThemeDefinition(
                style=style_enum,
                theme=UITheme.LIGHT,
                colors=style_def.colors.copy(),
                fonts=style_def.fonts.copy(),
                spacing=style_def.spacing.copy(),
                borderRadius=style_def.borderRadius.copy(),
            )
            self._theme_definitions[f"{style_enum.value}_light"] = light_theme
            
            # 暗色主题（反转颜色）
            dark_colors = self._invert_colors_for_dark(style_def.colors)
            dark_theme = UIThemeDefinition(
                style=style_enum,
                theme=UITheme.DARK,
                colors=dark_colors,
                fonts=style_def.fonts.copy(),
                spacing=style_def.spacing.copy(),
                borderRadius=style_def.borderRadius.copy(),
            )
            self._theme_definitions[f"{style_enum.value}_dark"] = dark_theme
    
    def _invert_colors_for_dark(self, light_colors: Dict[str, str]) -> Dict[str, str]:
        """为暗色主题反转颜色"""
        # 基础颜色映射（可根据需要调整）
        color_mapping = {
            # 背景相关
            "background": "#16181d",  # 深色背景
            "surface": "#252a33",     # 深色表面
            "border": "#2d3440",      # 深色边框
            
            # 文本相关
            "text_primary": "#f5f7fa",  # 浅色主文本
            "text_secondary": "#aeb6c2", # 浅色次文本
            
            # 交互状态
            "hover": "#2d3440",
            "active": "#343b47",
            
            # 语义颜色（保持原样或微调）
            "primary": "#4da3ff",      # 稍亮的蓝色
            "secondary": "#8e8e93",    # 保持
            "success": "#67d39a",      # 稍亮的绿色
            "warning": "#ff9d57",      # 稍亮的黄色
            "error": "#ff6b6b",        # 稍亮的红色
        }
        
        dark_colors = light_colors.copy()
        for key in dark_colors:
            if key in color_mapping:
                dark_colors[key] = color_mapping[key]
        
        return dark_colors
    
    def get_current_theme_definition(self) -> UIThemeDefinition:
        """获取当前主题定义"""
        key = f"{self.current_style.value}_{self.current_theme.value}"
        return self._theme_definitions.get(key, self._theme_definitions["win11_dark"])
    
    def get_color(self, color_name: str) -> str:
        """获取颜色值"""
        theme = self.get_current_theme_definition()
        return theme.colors.get(color_name, "#000000")
    
    def get_font(self, font_name: str) -> str:
        """获取字体值"""
        theme = self.get_current_theme_definition()
        return theme.fonts.get(font_name, "sans-serif")
    
    def get_spacing(self, spacing_name: str) -> int:
        """获取间距值"""
        theme = self.get_current_theme_definition()
        return theme.spacing.get(spacing_name, 8)
    
    def get_border_radius(self, radius_name: str) -> int:
        """获取圆角值"""
        theme = self.get_current_theme_definition()
        return theme.borderRadius.get(radius_name, 4)
    
    def register_callback(self, callback: Callable[[], None]):
        """注册风格切换回调"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[], None]):
        """取消注册风格切换回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self):
        """通知所有回调"""
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                print(f"风格切换回调执行失败: {e}")
    
    def set_style(self, style: UIStyle):
        """设置风格"""
        if self.current_style == style:
            return
        self.current_style = style
        self.save_config()
        self._notify_callbacks()
    
    def set_theme(self, theme: UITheme):
        """设置主题"""
        if self.current_theme == theme:
            return
        self.current_theme = theme
        self.save_config()
        self._notify_callbacks()
    
    def set_opacity(self, opacity: float):
        """设置透明度 (0.0-1.0)"""
        new_opacity = max(0.0, min(1.0, opacity))
        if abs(self.current_opacity - new_opacity) < 0.001:
            return
        self.current_opacity = new_opacity
        self.save_config()
        self._notify_callbacks()
    
    def get_available_styles(self) -> List[Dict[str, str]]:
        """获取可用风格列表"""
        return [
            {
                "value": style.value,
                "display_name": self._style_definitions[style].display_name,
                "description": self._style_definitions[style].description
            }
            for style in UIStyle
        ]
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "style": self.current_style.value,
            "theme": self.current_theme.value,
            "opacity": self.current_opacity,
            "version": "1.0"
        }
    
    def load_config(self):
        """加载配置"""
        if not os.path.exists(self.config_file):
            # 默认配置
            self.current_style = UIStyle.WIN11
            self.current_theme = UITheme.DARK
            self.current_opacity = 1.0
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 应用配置
            if "style" in config:
                self.current_style = UIStyle.from_string(config["style"])
            if "theme" in config:
                self.current_theme = UITheme.from_string(config["theme"])
            if "opacity" in config:
                self.current_opacity = float(config["opacity"])
                
        except Exception as e:
            print(f"加载UI配置失败: {e}")
            # 使用默认配置
            self.current_style = UIStyle.WIN11
            self.current_theme = UITheme.DARK
            self.current_opacity = 1.0
    
    def save_config(self):
        """保存配置"""
        try:
            config = self.get_config()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存UI配置失败: {e}")


# 全局管理器实例
_style_manager = None

def get_style_manager() -> UIStyleManager:
    """获取风格管理器实例"""
    global _style_manager
    if _style_manager is None:
        _style_manager = UIStyleManager()
    return _style_manager