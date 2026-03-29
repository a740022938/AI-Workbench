"""
批量操作对话框 - 用于对选中的训练结果进行批量操作
支持批量加标签、批量收藏/取消收藏、批量标重要/取消重要、批量归档/取消归档、批量导出
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional


def get_text(key):
    """根据当前语言配置获取文本"""
    # 与 training_history_window.py 保持一致
    texts = {
        "TITLE_BATCH_OPERATIONS": "批量操作",
        "LABEL_SELECTED_COUNT": "已选中实验数量",
        "LABEL_OPERATION_TYPE": "操作类型",
        "OPERATION_ADD_TAGS": "添加标签",
        "OPERATION_SET_FAVORITE": "设为收藏",
        "OPERATION_UNSET_FAVORITE": "取消收藏",
        "OPERATION_SET_IMPORTANT": "标为重要",
        "OPERATION_UNSET_IMPORTANT": "取消重要",
        "OPERATION_ARCHIVE": "归档（隐藏）",
        "OPERATION_UNARCHIVE": "取消归档（恢复显示）",
        "OPERATION_EXPORT": "导出实验摘要",
        "LABEL_TAGS_TO_ADD": "要添加的标签",
        "LABEL_TAGS_HINT": "多个标签用逗号分隔",
        "LABEL_EXPORT_FORMAT": "导出格式",
        "FORMAT_TXT": "文本文件 (.txt)",
        "FORMAT_JSON": "JSON文件 (.json)",
        "FORMAT_CSV": "CSV文件 (.csv)",
        "LABEL_EXPORT_PATH": "导出路径",
        "BTN_BROWSE": "浏览",
        "BTN_APPLY": "执行操作",
        "BTN_CANCEL": "取消",
        "MSG_OPERATION_SUCCESS": "批量操作成功",
        "MSG_OPERATION_ERROR": "批量操作失败",
        "MSG_EXPORT_SUCCESS": "导出成功",
        "MSG_EXPORT_ERROR": "导出失败",
        "MSG_NO_TAGS": "请输入要添加的标签",
        "MSG_NO_EXPORT_PATH": "请选择导出路径",
        "MSG_CONFIRM_ARCHIVE": "归档后实验将从主列表隐藏，但文件不会被删除。确认归档？",
        "MSG_CONFIRM_UNARCHIVE": "取消归档后实验将恢复在主列表显示。确认取消归档？",
        "STATUS_READY": "准备执行",
        "STATUS_EXECUTING": "执行中...",
        "STATUS_COMPLETED": "操作完成",
        "STATUS_ERROR": "执行出错",
    }
    return texts.get(key, key)


class BatchOperationsDialog(tk.Toplevel):
    """批量操作对话框"""
    
    def __init__(self, master, selected_indices: List[int], results: List[Dict[str, Any]], 
                 on_success: Optional[Callable] = None):
        """
        初始化批量操作对话框
        
        Args:
            master: 父窗口
            selected_indices: 选中的索引列表
            results: 结果列表
            on_success: 操作成功后的回调函数
        """
        super().__init__(master)
        self.master = master
        self.selected_indices = selected_indices
        self.results = results
        self.on_success = on_success
        
        self.title(get_text("TITLE_BATCH_OPERATIONS"))
        self.geometry("650x500")
        self.minsize(600, 450)
        self.configure(bg="#16181d")
        self.transient(master)
        self.grab_set()
        
        # 样式（与训练历史窗口保持一致）
        self.bg_main = "#16181d"
        self.bg_card = "#252a33"
        self.text_main = "#f5f7fa"
        self.text_sub = "#aeb6c2"
        self.border = "#2d3440"
        self.accent_green = "#67d39a"
        self.accent_yellow = "#ff9d57"
        self.accent_red = "#ff6b6b"
        self.accent_blue = "#4da3ff"
        
        # 状态
        self.selected_count = len(selected_indices)
        self.selected_paths = []
        
        # 获取选中的文件路径
        for index in selected_indices:
            if 0 <= index < len(results):
                result = results[index]
                self.selected_paths.append(result["path"])
        
        # 构建UI
        self._build_ui()
    
    def _build_ui(self):
        """构建UI界面"""
        # 主容器
        main_container = tk.Frame(self, bg=self.bg_main)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 标题
        tk.Label(main_container, text="批量操作", bg=self.bg_main, fg=self.text_main,
                font=("Microsoft YaHei", 14, "bold")).pack(anchor="w", pady=(0, 10))
        
        # 选中的实验数量
        count_frame = tk.Frame(main_container, bg=self.bg_card, highlightthickness=1,
                              highlightbackground=self.border)
        count_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(count_frame, text=get_text("LABEL_SELECTED_COUNT"), bg=self.bg_card, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=15, pady=(12, 5))
        
        tk.Label(count_frame, text=f" {self.selected_count} 个实验", bg=self.bg_card, fg=self.accent_blue,
                font=("Microsoft YaHei", 12, "bold")).pack(anchor="w", padx=15, pady=(0, 12))
        
        # 操作类型选择
        operation_frame = tk.Frame(main_container, bg=self.bg_card, highlightthickness=1,
                                  highlightbackground=self.border)
        operation_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(operation_frame, text=get_text("LABEL_OPERATION_TYPE"), bg=self.bg_card, fg=self.text_main,
                font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=15, pady=(12, 10))
        
        # 操作类型选项
        self.operation_var = tk.StringVar(value="add_tags")
        operations = [
            ("add_tags", get_text("OPERATION_ADD_TAGS")),
            ("set_favorite", get_text("OPERATION_SET_FAVORITE")),
            ("unset_favorite", get_text("OPERATION_UNSET_FAVORITE")),
            ("set_important", get_text("OPERATION_SET_IMPORTANT")),
            ("unset_important", get_text("OPERATION_UNSET_IMPORTANT")),
            ("archive", get_text("OPERATION_ARCHIVE")),
            ("unarchive", get_text("OPERATION_UNARCHIVE")),
            ("export", get_text("OPERATION_EXPORT")),
        ]
        
        for value, text in operations:
            rb = tk.Radiobutton(operation_frame, text=text, variable=self.operation_var, value=value,
                              bg=self.bg_card, fg=self.text_main, selectcolor=self.bg_card,
                              activebackground=self.bg_card, font=("Microsoft YaHei", 10))
            rb.pack(anchor="w", padx=30, pady=2)
        
        # 操作详情区域（动态显示）
        self.details_container = tk.Frame(main_container, bg=self.bg_main)
        self.details_container.pack(fill="x", pady=(0, 15))
        
        # 绑定操作类型变更事件
        self.operation_var.trace("w", lambda *args: self._update_details_area())
        
        # 初始更新详情区域
        self._update_details_area()
        
        # 状态显示
        status_frame = tk.Frame(main_container, bg=self.bg_main)
        status_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(status_frame, text="状态:", bg=self.bg_main, fg=self.text_sub,
                font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 10))
        
        self.status_var = tk.StringVar(value=get_text("STATUS_READY"))
        status_label = tk.Label(status_frame, textvariable=self.status_var, bg=self.bg_main, fg=self.accent_green,
                               font=("Microsoft YaHei", 10, "bold"))
        status_label.pack(side="left")
        
        # 按钮栏
        button_frame = tk.Frame(main_container, bg=self.bg_main)
        button_frame.pack(fill="x", pady=(10, 0))
        
        cancel_btn = tk.Button(button_frame, text=get_text("BTN_CANCEL"), bg=self.border, fg=self.text_main,
                              font=("Microsoft YaHei", 10), relief="flat", padx=20, pady=8,
                              command=self.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))
        
        apply_btn = tk.Button(button_frame, text=get_text("BTN_APPLY"), bg=self.accent_green, fg="white",
                             font=("Microsoft YaHei", 10, "bold"), relief="flat", padx=25, pady=8,
                             command=self._apply_operation)
        apply_btn.pack(side="right")
    
    def _update_details_area(self):
        """根据操作类型更新详情区域"""
        # 清空详情区域
        for widget in self.details_container.winfo_children():
            widget.destroy()
        
        operation_type = self.operation_var.get()
        
        if operation_type == "add_tags":
            # 添加标签详情
            details_frame = tk.Frame(self.details_container, bg=self.bg_card, highlightthickness=1,
                                    highlightbackground=self.border)
            details_frame.pack(fill="x")
            
            tk.Label(details_frame, text=get_text("LABEL_TAGS_TO_ADD"), bg=self.bg_card, fg=self.text_main,
                    font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", padx=15, pady=(12, 5))
            
            self.tags_var = tk.StringVar()
            tags_entry = tk.Entry(details_frame, textvariable=self.tags_var, bg="#1b2028", fg=self.text_main,
                                 relief="flat", font=("Microsoft YaHei", 10), width=50)
            tags_entry.pack(fill="x", padx=15, pady=(0, 8))
            
            tk.Label(details_frame, text=get_text("LABEL_TAGS_HINT"), bg=self.bg_card, fg=self.text_sub,
                    font=("Microsoft YaHei", 9)).pack(anchor="w", padx=15, pady=(0, 12))
            
        elif operation_type == "export":
            # 导出详情
            details_frame = tk.Frame(self.details_container, bg=self.bg_card, highlightthickness=1,
                                    highlightbackground=self.border)
            details_frame.pack(fill="x")
            
            # 导出格式选择
            format_frame = tk.Frame(details_frame, bg=self.bg_card)
            format_frame.pack(fill="x", padx=15, pady=(12, 8))
            
            tk.Label(format_frame, text=get_text("LABEL_EXPORT_FORMAT"), bg=self.bg_card, fg=self.text_main,
                    font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", pady=(0, 5))
            
            self.export_format_var = tk.StringVar(value="txt")
            formats = [("txt", get_text("FORMAT_TXT")), 
                      ("json", get_text("FORMAT_JSON")), 
                      ("csv", get_text("FORMAT_CSV"))]
            
            for value, text in formats:
                rb = tk.Radiobutton(format_frame, text=text, variable=self.export_format_var, value=value,
                                  bg=self.bg_card, fg=self.text_main, selectcolor=self.bg_card,
                                  activebackground=self.bg_card, font=("Microsoft YaHei", 10))
                rb.pack(anchor="w", padx=10, pady=2)
            
            # 导出路径选择
            path_frame = tk.Frame(details_frame, bg=self.bg_card)
            path_frame.pack(fill="x", padx=15, pady=(0, 12))
            
            tk.Label(path_frame, text=get_text("LABEL_EXPORT_PATH"), bg=self.bg_card, fg=self.text_main,
                    font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", pady=(0, 5))
            
            path_input_frame = tk.Frame(path_frame, bg=self.bg_card)
            path_input_frame.pack(fill="x")
            
            self.export_path_var = tk.StringVar()
            path_entry = tk.Entry(path_input_frame, textvariable=self.export_path_var, bg="#1b2028", fg=self.text_main,
                                 relief="flat", font=("Microsoft YaHei", 10), width=40)
            path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            browse_btn = tk.Button(path_input_frame, text=get_text("BTN_BROWSE"), bg=self.border, fg=self.text_main,
                                  font=("Microsoft YaHei", 9), relief="flat", padx=12, pady=4,
                                  command=self._browse_export_path)
            browse_btn.pack(side="right")
        
        elif operation_type in ["archive", "unarchive"]:
            # 归档/取消归档详情
            details_frame = tk.Frame(self.details_container, bg=self.bg_card, highlightthickness=1,
                                    highlightbackground=self.border)
            details_frame.pack(fill="x")
            
            warning_text = get_text("MSG_CONFIRM_ARCHIVE") if operation_type == "archive" else get_text("MSG_CONFIRM_UNARCHIVE")
            
            tk.Label(details_frame, text="⚠️ 注意", bg=self.bg_card, fg=self.accent_yellow,
                    font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", padx=15, pady=(12, 5))
            
            tk.Label(details_frame, text=warning_text, bg=self.bg_card, fg=self.text_main,
                    font=("Microsoft YaHei", 10), wraplength=550, justify="left").pack(anchor="w", padx=15, pady=(0, 12))
    
    def _browse_export_path(self):
        """浏览导出路径"""
        operation_type = self.operation_var.get()
        if operation_type != "export":
            return
        
        format_map = {"txt": ".txt", "json": ".json", "csv": ".csv"}
        extension = format_map.get(self.export_format_var.get(), ".txt")
        
        # 生成默认文件名
        default_name = f"训练实验批量导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}"
        
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="选择导出文件路径",
            defaultextension=extension,
            initialfile=default_name,
            filetypes=[(f"{extension.upper()}文件", f"*{extension}"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.export_path_var.set(file_path)
    
    def _apply_operation(self):
        """执行批量操作"""
        operation_type = self.operation_var.get()
        
        try:
            # 导入分析器
            from core.training_result_analyzer import get_result_analyzer
            analyzer = get_result_analyzer()
            
            # 更新状态
            self.status_var.set(get_text("STATUS_EXECUTING"))
            self.update()
            
            success_count = 0
            failure_count = 0
            
            if operation_type == "add_tags":
                # 批量添加标签
                tags_input = self.tags_var.get().strip()
                if not tags_input:
                    messagebox.showwarning("提示", get_text("MSG_NO_TAGS"))
                    self.status_var.set(get_text("STATUS_ERROR"))
                    return
                
                # 解析标签（逗号分隔）
                tags_to_add = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
                
                success_count, failure_count = analyzer.batch_add_tags(self.selected_paths, tags_to_add)
                
                if success_count > 0:
                    messagebox.showinfo("成功", f"{get_text('MSG_OPERATION_SUCCESS')}\n成功: {success_count}, 失败: {failure_count}")
            
            elif operation_type == "set_favorite":
                # 批量设为收藏
                success_count, failure_count = analyzer.batch_set_favorite(self.selected_paths, True)
                
                if success_count > 0:
                    messagebox.showinfo("成功", f"{get_text('MSG_OPERATION_SUCCESS')}\n成功: {success_count}, 失败: {failure_count}")
            
            elif operation_type == "unset_favorite":
                # 批量取消收藏
                success_count, failure_count = analyzer.batch_set_favorite(self.selected_paths, False)
                
                if success_count > 0:
                    messagebox.showinfo("成功", f"{get_text('MSG_OPERATION_SUCCESS')}\n成功: {success_count}, 失败: {failure_count}")
            
            elif operation_type == "set_important":
                # 批量标为重要
                success_count, failure_count = analyzer.batch_set_important(self.selected_paths, True)
                
                if success_count > 0:
                    messagebox.showinfo("成功", f"{get_text('MSG_OPERATION_SUCCESS')}\n成功: {success_count}, 失败: {failure_count}")
            
            elif operation_type == "unset_important":
                # 批量取消重要
                success_count, failure_count = analyzer.batch_set_important(self.selected_paths, False)
                
                if success_count > 0:
                    messagebox.showinfo("成功", f"{get_text('MSG_OPERATION_SUCCESS')}\n成功: {success_count}, 失败: {failure_count}")
            
            elif operation_type == "archive":
                # 批量归档
                success_count, failure_count = analyzer.batch_set_archived(self.selected_paths, True)
                
                if success_count > 0:
                    messagebox.showinfo("成功", f"归档成功\n成功: {success_count}, 失败: {failure_count}")
            
            elif operation_type == "unarchive":
                # 批量取消归档
                success_count, failure_count = analyzer.batch_set_archived(self.selected_paths, False)
                
                if success_count > 0:
                    messagebox.showinfo("成功", f"取消归档成功\n成功: {success_count}, 失败: {failure_count}")
            
            elif operation_type == "export":
                # 批量导出
                export_path = self.export_path_var.get().strip()
                if not export_path:
                    messagebox.showwarning("提示", get_text("MSG_NO_EXPORT_PATH"))
                    self.status_var.set(get_text("STATUS_ERROR"))
                    return
                
                export_format = self.export_format_var.get()
                
                success = analyzer.export_results_summary(self.selected_paths, export_path, export_format)
                
                if success:
                    messagebox.showinfo("成功", f"{get_text('MSG_EXPORT_SUCCESS')}\n文件已保存到:\n{export_path}")
                    self.status_var.set(get_text("STATUS_COMPLETED"))
                else:
                    messagebox.showerror("错误", get_text("MSG_EXPORT_ERROR"))
                    self.status_var.set(get_text("STATUS_ERROR"))
                    
                # 导出完成，可以关闭对话框
                if success:
                    self.destroy()
                    return
            
            # 更新状态
            if failure_count == 0:
                self.status_var.set(get_text("STATUS_COMPLETED"))
            elif success_count > 0:
                self.status_var.set(f"部分完成 (成功: {success_count}, 失败: {failure_count})")
            else:
                self.status_var.set(get_text("STATUS_ERROR"))
            
            # 执行成功回调
            if success_count > 0 and self.on_success:
                self.on_success()
            
            # 如果不是导出操作，保持对话框打开
            if operation_type != "export":
                self.update()
        
        except Exception as e:
            messagebox.showerror("错误", f"{get_text('MSG_OPERATION_ERROR')}: {str(e)}")
            self.status_var.set(get_text("STATUS_ERROR"))
            import traceback
            traceback.print_exc()


def open_batch_operations_dialog(master, selected_indices: List[int], results: List[Dict[str, Any]], 
                                on_success: Optional[Callable] = None):
    """打开批量操作对话框（工厂函数）"""
    dialog = BatchOperationsDialog(master, selected_indices, results, on_success)
    return dialog