#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
language_manager.py - 语言管理器

功能：
1. 管理多语言文案资源
2. 支持中英文切换
3. 提供统一的文案获取接口
4. 语言配置持久化
"""

import os
import json
from typing import Dict, Any, List, Optional
from enum import Enum


class Language(Enum):
    """语言枚举"""
    ZH_CN = "zh_CN"  # 简体中文
    EN_US = "en_US"  # 英文（美国）

    @classmethod
    def from_string(cls, value: str) -> 'Language':
        """从字符串转换为枚举"""
        value_lower = value.lower().replace('-', '_')
        for lang in cls:
            if lang.value.lower() == value_lower:
                return lang
        return cls.ZH_CN  # 默认中文

    def get_display_name(self) -> str:
        """获取显示名称"""
        return {
            Language.ZH_CN: "简体中文",
            Language.EN_US: "English"
        }[self]


class LanguageManager:
    """语言管理器"""

    def __init__(self, config_dir: str = None):
        """
        初始化语言管理器

        Args:
            config_dir: 配置目录，如果为None则使用默认目录
        """
        if config_dir is None:
            # 默认目录在当前工作目录下
            config_dir = os.path.join(os.getcwd(), "config", "ui")

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "language_config.json")

        # 创建目录
        os.makedirs(config_dir, exist_ok=True)

        # 当前语言
        self.current_language: Language = Language.ZH_CN

        # 语言切换回调
        self._callbacks = []

        # 文案资源
        self._resources: Dict[Language, Dict[str, str]] = {
            Language.ZH_CN: {},
            Language.EN_US: {}
        }

        # 初始化文案资源
        self._init_resources()

        # 加载配置
        self.load_config()

    def _init_resources(self):
        """初始化文案资源"""
        # 基础文案（通用）
        self._resources[Language.ZH_CN].update({
            # 通用按钮
            "BTN_OK": "确定",
            "BTN_CANCEL": "取消",
            "BTN_CLOSE": "关闭",
            "BTN_SAVE": "保存",
            "BTN_EXPORT": "导出",
            "BTN_IMPORT": "导入",
            "BTN_ADD": "添加",
            "BTN_DELETE": "删除",
            "BTN_EDIT": "编辑",
            "BTN_BROWSE": "浏览",
            "BTN_REFRESH": "刷新",
            "BTN_RUN": "运行",
            "BTN_STOP": "停止",
            "BTN_HELP": "帮助",
            "BTN_SETTINGS": "设置",
            "BTN_OPEN_PROJECT": "打开项目",
            "BTN_AUTO_DETECT": "自动检测",
            "BTN_FIT_WINDOW": "适应窗口",
            "BTN_ORIGINAL_SCALE": "原始尺寸",
            "BTN_AI_ANALYSIS": "AI分析",
            "BTN_APPLY_FINE_TUNE": "应用微调",
            "BTN_BACKUP": "备份",
            "BTN_BATCH_RENAME": "批量重命名",
            "BTN_DELETE_CURRENT_BOX": "删除当前框",
            "BTN_DELETE_SELECTED": "删除选中",
            "BTN_NEXT_IMAGE": "下一张",
            "BTN_OPEN_EDIT_WINDOW": "打开编辑窗口",
            "BTN_PREV_IMAGE": "上一张",
            "BTN_RESTORE": "恢复",
            "BTN_SAVE_LABELS": "保存标签",
            "BTN_START_TRAINING": "开始训练",

            # 通用标签
            "LABEL_NAME": "名称",
            "LABEL_TYPE": "类型",
            "LABEL_STATUS": "状态",
            "LABEL_DESCRIPTION": "描述",
            "LABEL_PATH": "路径",
            "LABEL_SIZE": "大小",
            "LABEL_TIME": "时间",
            "LABEL_COUNT": "数量",
            "LABEL_PROGRESS": "进度",
            "LABEL_RESULT": "结果",
            "LABEL_IMAGE_WORKSPACE": "图像工作区",
            "LABEL_CONTROL_PANEL": "控制面板",
            "LABEL_CURRENT_PROJECT": "当前项目",
            "LABEL_NO_BOX_SELECTED": "未选中标注框",
            "LABEL_SELECTED_BOX": "选中标注框",
            "LABEL_SELECTED_BOX_LIST": "选中框列表",
            "LABEL_SELECTED_CLASS": "选中类别",
            "LABEL_SHORTCUT_OPS": "快捷键操作",
            "LABEL_CLASS_SETTINGS": "类别设置",
            "LABEL_IMAGE_DIR": "图片目录",
            "LABEL_LABEL_DIR": "标签目录",
            "LABEL_MODEL_PATH": "模型路径",
            "LABEL_OUTPUT_DIR": "输出数据集目录",
            "LABEL_BAD_CASE_DIR": "坏样本目录",

            # 通用消息
            "MSG_SUCCESS": "成功",
            "MSG_ERROR": "错误",
            "MSG_WARNING": "警告",
            "MSG_INFO": "信息",
            "MSG_CONFIRM": "确认",
            "MSG_LOADING": "加载中...",
            "MSG_PROCESSING": "处理中...",
            "MSG_COMPLETED": "已完成",
            "MSG_FAILED": "失败",
            "MSG_UNKNOWN": "未知",
            "STATUS_WAITING_LOAD": "等待加载图片",
            "STATUS_IMAGE_DIR_UPDATED": "状态：图片目录已更新",
            "STATUS_CLASS_NAMES_UPDATED": "状态：类别名称已更新",
            "STATUS_WAITING_PROJECT_INFO": "等待接入图片目录与数据状态显示",
            "STATUS_MAIN_LOADED": "已加载主项目",

            # 通用提示
            "TIPS_SELECT_FILE": "请选择文件",
            "TIPS_SELECT_DIR": "请选择目录",
            "TIPS_INPUT_REQUIRED": "请输入内容",
            "TIPS_INVALID_INPUT": "输入无效",
            "TIPS_OPERATION_SUCCESS": "操作成功",
            "TIPS_OPERATION_FAILED": "操作失败",
            "TIPS_SHORTCUT_OPS": "空白处拖拽=画新框\n框内部点击=选中/移动\n框角落拖拽=调整\n右键框=编辑框\nDelete=删除选中框\nCtrl+S=保存标签",
            "TIPS_LABEL_DIR_NOT_SET": "标签目录未设置",
            "STATUS_YOLO_AUTO_DETECT_FAILED": "状态：YOLO 自动识别失败",

            # 窗口标题
            "TITLE_MAIN_WINDOW": "AI视觉数据与训练工作台",
            "TITLE_TRAINING_CENTER": "训练中心",
            "TITLE_DATA_HEALTH": "数据集健康检查",
            "TITLE_DATASET_EXPORT": "数据集制作中心",
            "TITLE_CLOSED_LOOP": "闭环修正中心",
            "TITLE_SETTINGS": "设置",
            "TITLE_ABOUT": "关于",
            "TITLE_PATHS": "路径设置",
            "SUBTITLE_PATHS": "配置图片目录、标签目录、模型路径等",
            "TITLE_BEHAVIOR": "行为设置",
            "TITLE_INFERENCE": "推理设置",
            "TITLE_TRAINING": "训练设置",
            "TITLE_APPEARANCE": "外观设置",
            "TITLE_LANGUAGE": "语言设置",
            "APP_TITLE": "AI视觉数据与训练工作台",
            "APP_SUBTITLE": "专业AI数据标注与模型训练一体化平台",

            # 主窗口菜单
            "MENU_FILE": "文件",
            "MENU_EDIT": "编辑",
            "MENU_VIEW": "视图",
            "MENU_TOOLS": "工具",
            "MENU_HELP": "帮助",
            "MENU_SETTINGS": "设置",
            "MENU_DELETE_CURRENT_BOX": "删除当前标注框",
            "MENU_EDIT_CURRENT_BOX": "编辑当前标注框",
            "MENU_MARK_BAD_CASE": "标记为坏样本",
            "MENU_MARK_DUPLICATE": "标记为重复框",
            "MENU_RESTORE_DUPLICATE": "恢复重复框",

            # 主窗口工具栏
            "TOOL_OPEN_IMAGE": "打开图片",
            "TOOL_SAVE_LABELS": "保存标签",
            "TOOL_PREV_IMAGE": "上一张",
            "TOOL_NEXT_IMAGE": "下一张",
            "TOOL_ZOOM_IN": "放大",
            "TOOL_ZOOM_OUT": "缩小",
            "TOOL_RESET_VIEW": "重置视图",
            "TOOL_TRAINING_MONITOR": "训练监控",
            "TOOL_TRAINING_CENTER": "训练中心",
            "TOOL_IMPORT_TRAINING_CONFIG": "导入训练配置",
            "TOOL_IMPORT_CLASS_CONFIG": "导入类别配置",
            "TOOL_DATA_HEALTH_CHECK": "数据健康检查",
            "TOOL_CLOSED_LOOP": "闭环修正中心",

            # 设置导航
            "NAV_PATHS": "路径设置",
            "NAV_BEHAVIOR": "行为设置",
            "NAV_INFERENCE": "推理设置",
            "NAV_TRAINING": "训练设置",
            "NAV_APPEARANCE": "外观设置",
            "NAV_LANGUAGE": "语言设置",
            "BTN_SAVE_SETTINGS": "保存设置",

            # 训练中心文案
            "TRAINING_TITLE": "训练中心",
            "TRAINING_BTN_START": "开始训练",
            "TRAINING_BTN_STOP": "停止训练",
            "TRAINING_BTN_SAVE_CONFIG": "保存配置",
            "TRAINING_BTN_LOAD_CONFIG": "加载配置",
            "TRAINING_LABEL_MODEL": "模型",
            "TRAINING_LABEL_DATA_DIR": "数据目录",
            "TRAINING_LABEL_EPOCHS": "训练轮数",
            "TRAINING_LABEL_BATCH_SIZE": "批次大小",
            "TRAINING_LABEL_LEARNING_RATE": "学习率",
            "TRAINING_MSG_TRAINING": "训练中...",
            "TRAINING_MSG_COMPLETED": "训练完成",
            "TRAINING_MSG_FAILED": "训练失败",

            # 质检中心文案
            "QC_TITLE": "数据集健康检查",
            "QC_BTN_RUN_CHECK": "运行检查",
            "QC_BTN_FIX_SELECTED": "修复选中",
            "QC_BTN_FIX_ALL": "修复全部",
            "QC_LABEL_ISSUES": "问题",
            "QC_LABEL_SEVERITY": "严重程度",
            "QC_LABEL_FILE": "文件",
            "QC_LABEL_MESSAGE": "消息",
            "QC_LABEL_SUGGESTION": "建议",
            "QC_MSG_NO_ISSUES": "未发现问题",
            "QC_MSG_FIX_SUCCESS": "修复成功",
            "QC_MSG_FIX_FAILED": "修复失败",

            # 数据集制作中心文案
            "DATASET_TITLE": "数据集制作中心",
            "DATASET_BTN_RUN_PRECHECK": "运行预检查",
            "DATASET_BTN_EXPORT": "导出数据集",
            "DATASET_LABEL_TRAIN_RATIO": "训练集比例",
            "DATASET_LABEL_VAL_RATIO": "验证集比例",
            "DATASET_LABEL_TEST_RATIO": "测试集比例",
            "DATASET_LABEL_EXPORT_DIR": "导出目录",
            "DATASET_MSG_PRECHECK_PASS": "预检查通过",
            "DATASET_MSG_PRECHECK_FAIL": "预检查失败",
            "DATASET_MSG_EXPORT_SUCCESS": "导出成功",
            "DATASET_MSG_EXPORT_FAILED": "导出失败",

            # 闭环修正中心文案
            "CLOSED_LOOP_TITLE": "闭环修正中心",
            "CLOSED_LOOP_BTN_ADD": "添加问题",
            "CLOSED_LOOP_BTN_RESOLVE": "标记解决",
            "CLOSED_LOOP_BTN_EXPORT_REPORT": "导出报告",
            "CLOSED_LOOP_LABEL_ISSUE_TYPE": "问题类型",
            "CLOSED_LOOP_LABEL_STATUS": "状态",
            "CLOSED_LOOP_LABEL_PRIORITY": "优先级",
            "CLOSED_LOOP_MSG_ADDED": "已添加",
            "CLOSED_LOOP_MSG_RESOLVED": "已解决",

            # 设置文案
            "SETTINGS_TITLE": "设置",
            "SETTINGS_TAB_GENERAL": "通用",
            "SETTINGS_TAB_UI": "界面",
            "SETTINGS_TAB_LANGUAGE": "语言",
            "SETTINGS_LABEL_STYLE": "风格",
            "SETTINGS_LABEL_THEME": "主题",
            "SETTINGS_LABEL_LANGUAGE": "语言",
            "SETTINGS_LABEL_OPACITY": "透明度",
            "LABEL_UI_STYLE": "UI风格",
            "SETTINGS_OPTION_LIGHT": "浅色",
            "LABEL_NO_BOX_SELECTED_DETAIL": "当前未选中任何框",
            "LABEL_BOX_INDEX": "框 #",
            "LABEL_CLASS_COLON": "类别：",
            "BTN_COPY_PREV_LABELS": "复制上一张标注",
            "LABEL_OPERATION_GUIDE": "操作说明",
            "BTN_SELECT": "选择",
            "CHECK_AUTO_SAVE": "自动保存当前标注",
            "CHECK_AUTO_SAVE_NAV": "切换图片时自动保存",
            "CHECK_AUTO_INFER": "打开图片时自动识别",
            "CHECK_ENABLE_OPENCLAW": "启用 OpenClaw 分析",
            "LABEL_IMGSZ": "图像尺寸",
            "LABEL_DEVICE": "设备",
            "LABEL_PROJECT": "项目目录",
            "MSG_SETTINGS_SAVED": "设置已保存",
            "MSG_SETTINGS_SAVE_ERROR": "设置保存失败",
            "SETTINGS_OPTION_DARK": "深色",
        })

        # 英文文案
        self._resources[Language.EN_US].update({
            # Common buttons
            "BTN_OK": "OK",
            "BTN_CANCEL": "Cancel",
            "BTN_CLOSE": "Close",
            "BTN_SAVE": "Save",
            "BTN_EXPORT": "Export",
            "BTN_IMPORT": "Import",
            "BTN_ADD": "Add",
            "BTN_DELETE": "Delete",
            "BTN_EDIT": "Edit",
            "BTN_BROWSE": "Browse",
            "BTN_REFRESH": "Refresh",
            "BTN_RUN": "Run",
            "BTN_STOP": "Stop",
            "BTN_HELP": "Help",
            "BTN_SETTINGS": "Settings",
            "BTN_OPEN_PROJECT": "Open Project",
            "BTN_AUTO_DETECT": "Auto Detect",
            "BTN_FIT_WINDOW": "Fit Window",
            "BTN_ORIGINAL_SCALE": "Original Scale",
            "BTN_AI_ANALYSIS": "AI Analysis",
            "BTN_APPLY_FINE_TUNE": "Apply Fine Tune",
            "BTN_BACKUP": "Backup",
            "BTN_BATCH_RENAME": "Batch Rename",
            "BTN_DELETE_CURRENT_BOX": "Delete Current Box",
            "BTN_DELETE_SELECTED": "Delete Selected",
            "BTN_NEXT_IMAGE": "Next Image",
            "BTN_OPEN_EDIT_WINDOW": "Open Edit Window",
            "BTN_PREV_IMAGE": "Previous Image",
            "BTN_RESTORE": "Restore",
            "BTN_SAVE_LABELS": "Save Labels",
            "BTN_START_TRAINING": "Start Training",

            # Common labels
            "LABEL_NAME": "Name",
            "LABEL_TYPE": "Type",
            "LABEL_STATUS": "Status",
            "LABEL_DESCRIPTION": "Description",
            "LABEL_PATH": "Path",
            "LABEL_SIZE": "Size",
            "LABEL_TIME": "Time",
            "LABEL_COUNT": "Count",
            "LABEL_PROGRESS": "Progress",
            "LABEL_RESULT": "Result",
            "LABEL_IMAGE_WORKSPACE": "Image Workspace",
            "LABEL_CONTROL_PANEL": "Control Panel",
            "LABEL_CURRENT_PROJECT": "Current Project",
            "LABEL_NO_BOX_SELECTED": "No Box Selected",
            "LABEL_SELECTED_BOX": "Selected Box",
            "LABEL_SELECTED_BOX_LIST": "Selected Box List",
            "LABEL_SELECTED_CLASS": "Selected Class",
            "LABEL_SHORTCUT_OPS": "Shortcut Operations",
            "LABEL_CLASS_SETTINGS": "Class Settings",

            # Common messages
            "MSG_SUCCESS": "Success",
            "MSG_ERROR": "Error",
            "MSG_WARNING": "Warning",
            "MSG_INFO": "Info",
            "MSG_CONFIRM": "Confirm",
            "MSG_LOADING": "Loading...",
            "MSG_PROCESSING": "Processing...",
            "MSG_COMPLETED": "Completed",
            "MSG_FAILED": "Failed",
            "MSG_UNKNOWN": "Unknown",
            "STATUS_WAITING_LOAD": "Waiting for image load",
            "STATUS_IMAGE_DIR_UPDATED": "Status: Image directory updated",
            "STATUS_CLASS_NAMES_UPDATED": "Status: Class names updated",
            "STATUS_WAITING_PROJECT_INFO": "Waiting for project directory and data status",
            "STATUS_MAIN_LOADED": "Main project loaded",

            # Common tips
            "TIPS_SELECT_FILE": "Please select a file",
            "TIPS_SELECT_DIR": "Please select a directory",
            "TIPS_INPUT_REQUIRED": "Input required",
            "TIPS_INVALID_INPUT": "Invalid input",
            "TIPS_OPERATION_SUCCESS": "Operation successful",
            "TIPS_OPERATION_FAILED": "Operation failed",
            "TIPS_SHORTCUT_OPS": "Drag on blank area = Draw new box\nClick inside box = Select/Move\nDrag corner = Resize\nRight-click box = Edit box\nDelete = Delete selected box\nCtrl+S = Save labels",
            "TIPS_LABEL_DIR_NOT_SET": "Label directory not set",
            "STATUS_YOLO_AUTO_DETECT_FAILED": "Status: YOLO auto detect failed",

            # Window titles
            "TITLE_MAIN_WINDOW": "AI Vision Data & Training Workbench",
            "TITLE_TRAINING_CENTER": "Training Center",
            "TITLE_DATA_HEALTH": "Data Health Check",
            "TITLE_DATASET_EXPORT": "Dataset Export Center",
            "TITLE_CLOSED_LOOP": "Closed Loop Correction Center",
            "TITLE_SETTINGS": "Settings",
            "TITLE_ABOUT": "About",
            "TITLE_PATHS": "Paths",
            "SUBTITLE_PATHS": "Configure image directory, label directory, model path, etc.",
            "TITLE_BEHAVIOR": "Behavior",
            "TITLE_INFERENCE": "Inference",
            "TITLE_TRAINING": "Training",
            "TITLE_APPEARANCE": "Appearance",
            "TITLE_LANGUAGE": "Language",
            "APP_TITLE": "AI Vision Data & Training Workbench",
            "APP_SUBTITLE": "Professional AI Data Annotation & Model Training Platform",

            # Main window menu
            "MENU_FILE": "File",
            "MENU_EDIT": "Edit",
            "MENU_VIEW": "View",
            "MENU_TOOLS": "Tools",
            "MENU_HELP": "Help",
            "MENU_SETTINGS": "Settings",
            "MENU_DELETE_CURRENT_BOX": "Delete Current Box",
            "MENU_EDIT_CURRENT_BOX": "Edit Current Box",
            "MENU_MARK_BAD_CASE": "Mark as Bad Case",
            "MENU_MARK_DUPLICATE": "Mark as Duplicate",
            "MENU_RESTORE_DUPLICATE": "Restore Duplicate",

            # Main window toolbar
            "TOOL_OPEN_IMAGE": "Open Image",
            "TOOL_SAVE_LABELS": "Save Labels",
            "TOOL_PREV_IMAGE": "Previous",
            "TOOL_NEXT_IMAGE": "Next",
            "TOOL_ZOOM_IN": "Zoom In",
            "TOOL_ZOOM_OUT": "Zoom Out",
            "TOOL_RESET_VIEW": "Reset View",
            "TOOL_TRAINING_MONITOR": "Training Monitor",
            "TOOL_TRAINING_CENTER": "Training Center",
            "TOOL_IMPORT_TRAINING_CONFIG": "Import Training Config",
            "TOOL_IMPORT_CLASS_CONFIG": "Import Class Config",
            "TOOL_DATA_HEALTH_CHECK": "Data Health Check",
            "TOOL_CLOSED_LOOP": "Closed Loop Center",

            # Settings navigation
            "NAV_PATHS": "Paths",
            "NAV_BEHAVIOR": "Behavior",
            "NAV_INFERENCE": "Inference",
            "NAV_TRAINING": "Training",
            "NAV_APPEARANCE": "Appearance",
            "NAV_LANGUAGE": "Language",
            "BTN_SAVE_SETTINGS": "Save Settings",

            # Training center texts
            "TRAINING_TITLE": "Training Center",
            "TRAINING_BTN_START": "Start Training",
            "TRAINING_BTN_STOP": "Stop Training",
            "TRAINING_BTN_SAVE_CONFIG": "Save Config",
            "TRAINING_BTN_LOAD_CONFIG": "Load Config",
            "TRAINING_LABEL_MODEL": "Model",
            "TRAINING_LABEL_DATA_DIR": "Data Directory",
            "TRAINING_LABEL_EPOCHS": "Epochs",
            "TRAINING_LABEL_BATCH_SIZE": "Batch Size",
            "TRAINING_LABEL_LEARNING_RATE": "Learning Rate",
            "TRAINING_MSG_TRAINING": "Training...",
            "TRAINING_MSG_COMPLETED": "Training completed",
            "TRAINING_MSG_FAILED": "Training failed",

            # Quality check center texts
            "QC_TITLE": "Data Health Check",
            "QC_BTN_RUN_CHECK": "Run Check",
            "QC_BTN_FIX_SELECTED": "Fix Selected",
            "QC_BTN_FIX_ALL": "Fix All",
            "QC_LABEL_ISSUES": "Issues",
            "QC_LABEL_SEVERITY": "Severity",
            "QC_LABEL_FILE": "File",
            "QC_LABEL_MESSAGE": "Message",
            "QC_LABEL_SUGGESTION": "Suggestion",
            "QC_MSG_NO_ISSUES": "No issues found",
            "QC_MSG_FIX_SUCCESS": "Fix successful",
            "QC_MSG_FIX_FAILED": "Fix failed",

            # Dataset export center texts
            "DATASET_TITLE": "Dataset Export Center",
            "DATASET_BTN_RUN_PRECHECK": "Run Pre-check",
            "DATASET_BTN_EXPORT": "Export Dataset",
            "DATASET_LABEL_TRAIN_RATIO": "Train Ratio",
            "DATASET_LABEL_VAL_RATIO": "Validation Ratio",
            "DATASET_LABEL_TEST_RATIO": "Test Ratio",
            "DATASET_LABEL_EXPORT_DIR": "Export Directory",
            "DATASET_MSG_PRECHECK_PASS": "Pre-check passed",
            "DATASET_MSG_PRECHECK_FAIL": "Pre-check failed",
            "DATASET_MSG_EXPORT_SUCCESS": "Export successful",
            "DATASET_MSG_EXPORT_FAILED": "Export failed",

            # Closed loop center texts
            "CLOSED_LOOP_TITLE": "Closed Loop Correction Center",
            "CLOSED_LOOP_BTN_ADD": "Add Issue",
            "CLOSED_LOOP_BTN_RESOLVE": "Mark Resolved",
            "CLOSED_LOOP_BTN_EXPORT_REPORT": "Export Report",
            "CLOSED_LOOP_LABEL_ISSUE_TYPE": "Issue Type",
            "CLOSED_LOOP_LABEL_STATUS": "Status",
            "CLOSED_LOOP_LABEL_PRIORITY": "Priority",
            "CLOSED_LOOP_MSG_ADDED": "Added",
            "CLOSED_LOOP_MSG_RESOLVED": "Resolved",

            # Settings texts
            "SETTINGS_TITLE": "Settings",
            "SETTINGS_TAB_GENERAL": "General",
            "SETTINGS_TAB_UI": "UI",
            "SETTINGS_TAB_LANGUAGE": "Language",
            "SETTINGS_LABEL_STYLE": "Style",
            "SETTINGS_LABEL_THEME": "Theme",
            "SETTINGS_LABEL_LANGUAGE": "Language",
            "SETTINGS_LABEL_OPACITY": "Opacity",
            "LABEL_UI_STYLE": "UI Style",
            "SETTINGS_OPTION_LIGHT": "Light",
            "LABEL_NO_BOX_SELECTED_DETAIL": "No box selected",
            "LABEL_BOX_INDEX": "Box #",
            "LABEL_CLASS_COLON": "Class: ",
            "BTN_COPY_PREV_LABELS": "Copy previous labels",
            "LABEL_OPERATION_GUIDE": "Operation guide",
            "BTN_SELECT": "Select",
            "CHECK_AUTO_SAVE": "Auto save current labels",
            "CHECK_AUTO_SAVE_NAV": "Auto save on navigation",
            "CHECK_AUTO_INFER": "Auto inference on image open",
            "CHECK_ENABLE_OPENCLAW": "Enable OpenClaw analysis",
            "LABEL_IMGSZ": "Image size",
            "LABEL_DEVICE": "Device",
            "LABEL_PROJECT": "Project directory",
            "MSG_SETTINGS_SAVED": "Settings saved",
            "MSG_SETTINGS_SAVE_ERROR": "Settings save failed",
            "SETTINGS_OPTION_DARK": "Dark",
        })

    def get_text(self, key: str, default: str = None) -> str:
        """
        获取文案

        Args:
            key: 文案键
            default: 默认值，如果未找到文案则返回此值

        Returns:
            当前语言下的文案
        """
        lang_resources = self._resources.get(self.current_language, {})
        result = lang_resources.get(key)

        if result is None and default is not None:
            return default

        # 如果当前语言没有，尝试从中文获取（作为后备）
        if result is None and self.current_language != Language.ZH_CN:
            zh_resources = self._resources.get(Language.ZH_CN, {})
            result = zh_resources.get(key)

        # 如果都没有，返回键本身
        return result if result is not None else key

    def set_language(self, language: Language):
        """设置语言"""
        if self.current_language == language:
            return

        self.current_language = language
        self.save_config()

        # 通知所有回调
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                print(f"语言切换回调执行失败: {e}")

    def register_callback(self, callback):
        """注册语言切换回调"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback):
        """取消注册语言切换回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_available_languages(self) -> List[Dict[str, str]]:
        """获取可用语言列表"""
        return [
            {
                "value": lang.value,
                "display_name": lang.get_display_name()
            }
            for lang in Language
        ]

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            "language": self.current_language.value,
            "version": "1.0"
        }

    def load_config(self):
        """加载配置"""
        if not os.path.exists(self.config_file):
            # 默认配置
            self.current_language = Language.ZH_CN
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 应用配置
            if "language" in config:
                self.current_language = Language.from_string(config["language"])

        except Exception as e:
            print(f"加载语言配置失败: {e}")
            # 使用默认配置
            self.current_language = Language.ZH_CN

    def save_config(self):
        """保存配置"""
        try:
            config = self.get_config()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存语言配置失败: {e}")


# 全局管理器实例
_language_manager = None

def get_language_manager() -> LanguageManager:
    """获取语言管理器实例"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager

def t(key: str, default: str = None) -> str:
    """快捷获取文案函数"""
    return get_language_manager().get_text(key, default)