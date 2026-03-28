import tkinter as tk
from tkinter import ttk
import time
import re


class TrainingMonitorWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("训练监控")
        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.configure(bg="#111318")

        self.current_page = tk.StringVar(value="训练任务")
        self._timer_running = False
        self._start_time = None
        self._timer_job = None
        self.on_stop_callback = None
        self.on_resume_callback = None
        self.total_epochs = 100
        self.best_epoch = None
        self.best_map = None

        self._build_root_layout()
        self._build_topbar()
        self._build_body()
        self.show_page("训练任务")

    def _build_root_layout(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _build_topbar(self):
        topbar = tk.Frame(self, bg="#161A22", height=56)
        topbar.grid(row=0, column=0, sticky="nsew")
        topbar.grid_propagate(False)
        topbar.grid_columnconfigure(0, weight=1)

        left_wrap = tk.Frame(topbar, bg="#161A22")
        left_wrap.grid(row=0, column=0, sticky="w", padx=16)

        tk.Label(
            left_wrap,
            text="训练监控",
            font=("Microsoft YaHei UI", 16, "bold"),
            fg="#F3F6FB",
            bg="#161A22"
        ).pack(side="left", padx=(0, 12))

        tk.Label(
            left_wrap,
            text="训练任务管理器",
            font=("Microsoft YaHei UI", 10),
            fg="#9AA4B2",
            bg="#161A22"
        ).pack(side="left")

        right_wrap = tk.Frame(topbar, bg="#161A22")
        right_wrap.grid(row=0, column=1, sticky="e", padx=16)

        ttk.Button(right_wrap, text="刷新", command=self.refresh_monitor_view).pack(side="left", padx=4)
        ttk.Button(right_wrap, text="加载训练状态", command=self.load_training_state).pack(side="left", padx=4)
        ttk.Button(right_wrap, text="打开输出目录", command=self.open_output_dir).pack(side="left", padx=4)
        self.resume_btn = ttk.Button(right_wrap, text="继续训练", command=self._handle_resume_clicked)
        self.resume_btn.pack(side="left", padx=4)
        self.stop_btn = ttk.Button(right_wrap, text="停止训练", command=self._handle_stop_clicked)
        self.stop_btn.pack(side="left", padx=4)
        ttk.Button(right_wrap, text="关闭", command=self.destroy).pack(side="left", padx=4)

    def _handle_stop_clicked(self):
        try:
            self.append_log("[训练] 用户点击 停止训练")
            if callable(self.on_stop_callback):
                self.on_stop_callback()
            else:
                self.append_log("[训练] 当前未绑定停止回调")
        except Exception as e:
            self.append_log(f"[训练] 停止按钮执行失败: {e}")

    def _handle_resume_clicked(self):
        try:
            self.append_log("[训练] 用户点击 继续训练")
            if callable(self.on_resume_callback):
                self.on_resume_callback()
            else:
                self.append_log("[训练] 当前未绑定继续训练回调")
        except Exception as e:
            self.append_log(f"[训练] 继续训练按钮执行失败: {e}")

    def set_stop_callback(self, callback):
        self.on_stop_callback = callback

    def set_resume_callback(self, callback):
        self.on_resume_callback = callback

    def _build_body(self):
        body = tk.Frame(self, bg="#111318")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self._build_sidebar(body)
        self._build_pages_area(body)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg="#151922", width=220)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        tk.Label(
            sidebar,
            text="导航",
            font=("Microsoft YaHei UI", 11, "bold"),
            fg="#C8D1DC",
            bg="#151922"
        ).pack(anchor="w", padx=16, pady=(16, 10))

        self.nav_buttons = {}

        for page_name in ["训练任务", "CPU", "内存", "GPU"]:
            btn = tk.Button(
                sidebar,
                text=page_name,
                font=("Microsoft YaHei UI", 11),
                fg="#D9E1EA",
                bg="#1C2230",
                activebackground="#263042",
                activeforeground="#FFFFFF",
                relief="flat",
                bd=0,
                height=2,
                anchor="w",
                command=lambda n=page_name: self.show_page(n)
            )
            btn.pack(fill="x", padx=12, pady=6)
            self.nav_buttons[page_name] = btn

    def _build_pages_area(self, parent):
        container = tk.Frame(parent, bg="#111318")
        container.grid(row=0, column=1, sticky="nsew", padx=(10, 14), pady=14)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.pages = {}
        self.pages["训练任务"] = self._build_training_task_page(container)
        self.pages["CPU"] = self._build_metric_page(container, "CPU 监控", "CPU 当前占用", "#4DA3FF")
        self.pages["内存"] = self._build_metric_page(container, "内存监控", "内存当前占用", "#67D39A")
        self.pages["GPU"] = self._build_gpu_page(container)

        for frame in self.pages.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def _build_card(self, parent, title):
        card = tk.Frame(parent, bg="#181D27", highlightthickness=1, highlightbackground="#232A36")
        tk.Label(
            card,
            text=title,
            font=("Microsoft YaHei UI", 11, "bold"),
            fg="#F3F6FB",
            bg="#181D27"
        ).pack(anchor="w", padx=14, pady=(12, 8))
        return card

    def _build_training_task_page(self, parent):
        page = tk.Frame(parent, bg="#111318")
        page.grid_rowconfigure(2, weight=1)
        page.grid_columnconfigure(0, weight=1)

        overview = tk.Frame(page, bg="#111318")
        overview.grid(row=0, column=0, sticky="ew")
        for i in range(5):
            overview.grid_columnconfigure(i, weight=1)

        fields = [
            ("当前状态", "未开始", "status_value_label"),
            ("当前轮次", "0 / 100", "epoch_value_label"),
            ("已运行时间", "00:00:00", "runtime_value_label"),
            ("预计剩余", "--:--:--", "eta_value_label"),
            ("当前模型", "yolov8n.pt", "model_value_label"),
        ]

        for idx, (k, v, attr_name) in enumerate(fields):
            card = self._build_card(overview, k)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 8, 0), pady=0)
            value_label = tk.Label(
                card,
                text=v,
                font=("Microsoft YaHei UI", 13, "bold"),
                fg="#DCE7F3",
                bg="#181D27"
            )
            value_label.pack(anchor="w", padx=14, pady=(0, 14))
            setattr(self, attr_name, value_label)

        middle = tk.Frame(page, bg="#111318")
        middle.grid(row=1, column=0, sticky="ew", pady=12)
        middle.grid_columnconfigure(0, weight=3)
        middle.grid_columnconfigure(1, weight=2)

        left_card = self._build_card(middle, "训练进度与核心指标")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(
            left_card,
            text="训练进度",
            font=("Microsoft YaHei UI", 10),
            fg="#9FB0C3",
            bg="#181D27"
        ).pack(anchor="w", padx=14, pady=(0, 6))

        self.progress = ttk.Progressbar(left_card, mode="determinate", maximum=100, value=0)
        self.progress.pack(fill="x", padx=14, pady=(0, 12))

        metrics_wrap = tk.Frame(left_card, bg="#181D27")
        metrics_wrap.pack(fill="x", padx=14, pady=(0, 12))
        metrics_wrap.grid_columnconfigure(0, weight=1)
        metrics_wrap.grid_columnconfigure(1, weight=1)

        self.loss_value_label = tk.Label(metrics_wrap, text="当前 loss  0.0000", font=("Microsoft YaHei UI", 11), fg="#FF9D57", bg="#181D27")
        self.loss_value_label.grid(row=0, column=0, sticky="w", pady=4)

        self.map_value_label = tk.Label(metrics_wrap, text="当前 mAP  0.0000", font=("Microsoft YaHei UI", 11), fg="#67D39A", bg="#181D27")
        self.map_value_label.grid(row=0, column=1, sticky="w", pady=4)

        self.data_value_label = tk.Label(metrics_wrap, text="当前数据集  dataset.yaml", font=("Microsoft YaHei UI", 11), fg="#DCE7F3", bg="#181D27")
        self.data_value_label.grid(row=1, column=0, sticky="w", pady=4)

        self.output_value_label = tk.Label(metrics_wrap, text="输出目录  runs/train/exp", font=("Microsoft YaHei UI", 11), fg="#DCE7F3", bg="#181D27")
        self.output_value_label.grid(row=1, column=1, sticky="w", pady=4)

        right_card = self._build_card(middle, "训练完成结果")
        right_card.grid(row=0, column=1, sticky="nsew")

        self.best_path_label = tk.Label(right_card, text="best.pt 路径  --", font=("Microsoft YaHei UI", 10), fg="#C9D4DF", bg="#181D27", anchor="w")
        self.best_path_label.pack(fill="x", padx=14, pady=4)

        self.last_path_label = tk.Label(right_card, text="last.pt 路径  --", font=("Microsoft YaHei UI", 10), fg="#C9D4DF", bg="#181D27", anchor="w")
        self.last_path_label.pack(fill="x", padx=14, pady=4)

        self.best_epoch_label = tk.Label(right_card, text="最佳轮次  --", font=("Microsoft YaHei UI", 10), fg="#C9D4DF", bg="#181D27", anchor="w")
        self.best_epoch_label.pack(fill="x", padx=14, pady=4)

        self.final_loss_label = tk.Label(right_card, text="最终 loss  --", font=("Microsoft YaHei UI", 10), fg="#C9D4DF", bg="#181D27", anchor="w")
        self.final_loss_label.pack(fill="x", padx=14, pady=4)

        self.final_map_label = tk.Label(right_card, text="最终 mAP  --", font=("Microsoft YaHei UI", 10), fg="#C9D4DF", bg="#181D27", anchor="w")
        self.final_map_label.pack(fill="x", padx=14, pady=4)

        self.total_time_label = tk.Label(right_card, text="总耗时  --", font=("Microsoft YaHei UI", 10), fg="#C9D4DF", bg="#181D27", anchor="w")
        self.total_time_label.pack(fill="x", padx=14, pady=4)

        log_card = self._build_card(page, "实时训练日志")
        log_card.grid(row=2, column=0, sticky="nsew")
        log_card.pack_propagate(False)

        self.log_text = tk.Text(
            log_card,
            bg="#10141C",
            fg="#D8E0EA",
            insertbackground="#FFFFFF",
            relief="flat",
            bd=0,
            font=("Consolas", 10),
            height=18
        )
        self.log_text.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.log_text.insert("end", "训练监控窗口已启动\n等待训练任务接入...\n")

        return page

    def _build_metric_page(self, parent, title, usage_text, accent):
        page = tk.Frame(parent, bg="#111318")
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)

        top_card = self._build_card(page, title)
        top_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        tk.Label(
            top_card,
            text=f"{usage_text}  0%",
            font=("Microsoft YaHei UI", 16, "bold"),
            fg=accent,
            bg="#181D27"
        ).pack(anchor="w", padx=14, pady=(0, 12))

        chart_card = self._build_card(page, "动态曲线区域")
        chart_card.grid(row=1, column=0, sticky="nsew")

        tk.Label(
            chart_card,
            text="这里后续接入实时曲线图",
            font=("Microsoft YaHei UI", 14),
            fg="#7F8B99",
            bg="#181D27"
        ).pack(expand=True)

        return page

    def _build_gpu_page(self, parent):
        page = tk.Frame(parent, bg="#111318")
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)

        top = tk.Frame(page, bg="#111318")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=1)

        gpu_card = self._build_card(top, "GPU 当前占用")
        gpu_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(gpu_card, text="0%", font=("Microsoft YaHei UI", 18, "bold"), fg="#A97CFF", bg="#181D27").pack(anchor="w", padx=14, pady=(0, 14))

        vram_card = self._build_card(top, "显存占用")
        vram_card.grid(row=0, column=1, sticky="nsew")
        tk.Label(vram_card, text="0 MB / 0 MB", font=("Microsoft YaHei UI", 18, "bold"), fg="#55D6D6", bg="#181D27").pack(anchor="w", padx=14, pady=(0, 14))

        charts = tk.Frame(page, bg="#111318")
        charts.grid(row=1, column=0, sticky="nsew")
        charts.grid_columnconfigure(0, weight=1)
        charts.grid_columnconfigure(1, weight=1)
        charts.grid_rowconfigure(0, weight=1)

        card1 = self._build_card(charts, "GPU 曲线图区域")
        card1.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(card1, text="后续接入 GPU 实时曲线", font=("Microsoft YaHei UI", 13), fg="#7F8B99", bg="#181D27").pack(expand=True)

        card2 = self._build_card(charts, "显存曲线图区域")
        card2.grid(row=0, column=1, sticky="nsew")
        tk.Label(card2, text="后续接入显存实时曲线", font=("Microsoft YaHei UI", 13), fg="#7F8B99", bg="#181D27").pack(expand=True)

        return page

    def load_training_state(self):
        try:
            import os
            import csv

            output_text = self.output_value_label.cget("text").replace("输出目录  ", "").strip()
            output_dir = output_text.replace("/", "\\")

            if not output_dir or not os.path.exists(output_dir):
                self.append_log(f"[训练] 输出目录不存在 无法加载训练状态: {output_dir}")
                return

            self.append_log(f"[训练] 开始加载训练状态: {output_dir}")

            args_path = os.path.join(output_dir, "args.yaml")
            results_path = os.path.join(output_dir, "results.csv")
            best_path = os.path.join(output_dir, "weights", "best.pt")
            last_path = os.path.join(output_dir, "weights", "last.pt")

            if os.path.exists(best_path) or os.path.exists(last_path):
                self.set_result_paths(
                    best_path=best_path if os.path.exists(best_path) else None,
                    last_path=last_path if os.path.exists(last_path) else None
                )

            if os.path.exists(results_path):
                with open(results_path, "r", encoding="utf-8", newline="") as f:
                    reader = list(csv.DictReader(f))

                if reader:
                    last_row = reader[-1]

                    epoch_value = None
                    for k in last_row.keys():
                        if "epoch" in k.lower():
                            epoch_value = last_row[k]
                            break

                    if epoch_value is not None:
                        try:
                            epoch_num = int(float(epoch_value)) + 1
                            self.set_current_epoch(epoch_num, self.total_epochs)
                        except:
                            pass

                    map_value = None
                    for key in [
                        "metrics/mAP50(B)",
                        "metrics/mAP50-95(B)",
                        "metrics/mAP50",
                        "metrics/mAP50-95"
                    ]:
                        if key in last_row and str(last_row[key]).strip():
                            map_value = str(last_row[key]).strip()
                            break

                    loss_parts = []
                    for key in ["train/box_loss", "train/cls_loss", "train/dfl_loss"]:
                        if key in last_row and str(last_row[key]).strip():
                            loss_parts.append(str(last_row[key]).strip())

                    loss_value = "/".join(loss_parts) if loss_parts else None
                    self.set_loss_map(loss_value, map_value)

                    self.append_log("[训练] 已从 results.csv 恢复训练状态")
                else:
                    self.append_log("[训练] results.csv 存在 但没有可读取内容")
            else:
                self.append_log("[训练] 未找到 results.csv")

            if os.path.exists(args_path):
                self.append_log(f"[训练] 已检测到 args.yaml: {args_path}")
            else:
                self.append_log("[训练] 未找到 args.yaml")

        except Exception as e:
            self.append_log(f"[训练] 加载训练状态失败: {e}")

    def refresh_monitor_view(self):
        try:
            import os

            self.append_log("[训练] 手动刷新训练监控")

            output_text = self.output_value_label.cget("text").replace("输出目录  ", "").strip()
            best_text = self.best_path_label.cget("text").replace("best.pt 路径  ", "").strip()
            last_text = self.last_path_label.cget("text").replace("last.pt 路径  ", "").strip()

            if output_text:
                if os.path.exists(output_text.replace("/", "\\")):
                    self.append_log(f"[训练] 输出目录存在: {output_text}")
                else:
                    self.append_log(f"[训练] 输出目录不存在: {output_text}")

            if best_text and best_text != "--":
                if os.path.exists(best_text.replace("/", "\\")):
                    self.append_log(f"[训练] best.pt 已存在: {best_text}")
                else:
                    self.append_log(f"[训练] best.pt 暂不存在: {best_text}")

            if last_text and last_text != "--":
                if os.path.exists(last_text.replace("/", "\\")):
                    self.append_log(f"[训练] last.pt 已存在: {last_text}")
                else:
                    self.append_log(f"[训练] last.pt 暂不存在: {last_text}")
        except Exception as e:
            self.append_log(f"[训练] 刷新失败: {e}")

    def open_output_dir(self):
        try:
            import os
            import subprocess

            text = self.output_value_label.cget("text")
            output_dir = text.replace("输出目录  ", "").strip()

            if not output_dir:
                self.append_log("[训练] 输出目录为空")
                return

            output_dir = output_dir.replace("/", "\\")
            if not os.path.exists(output_dir):
                self.append_log(f"[训练] 输出目录不存在: {output_dir}")
                return

            os.startfile(output_dir)
            self.append_log(f"[训练] 已打开输出目录: {output_dir}")
        except Exception as e:
            self.append_log(f"[训练] 打开输出目录失败: {e}")

    def _format_seconds(self, seconds):
        seconds = max(0, int(seconds))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _tick_runtime(self):
        try:
            if not self._timer_running or self._start_time is None:
                return

            elapsed = time.time() - self._start_time
            text = self._format_seconds(elapsed)
            self.runtime_value_label.config(text=text)
            self.total_time_label.config(text=f"总耗时  {text}")

            self._timer_job = self.after(1000, self._tick_runtime)
        except:
            pass

    def start_runtime(self):
        def _start():
            try:
                self._timer_running = False
                if self._timer_job is not None:
                    try:
                        self.after_cancel(self._timer_job)
                    except:
                        pass
                    self._timer_job = None

                self._start_time = time.time()
                self.runtime_value_label.config(text="00:00:00")
                self.total_time_label.config(text="总耗时  00:00:00")
                self._timer_running = True
                self._tick_runtime()
            except:
                pass

        try:
            self.after(0, _start)
        except:
            pass

    def stop_runtime(self):
        def _stop():
            try:
                if self._start_time is not None:
                    elapsed = time.time() - self._start_time
                    text = self._format_seconds(elapsed)
                    self.runtime_value_label.config(text=text); self.update_idletasks()
                    self.total_time_label.config(text=f"总耗时  {text}")
                self._timer_running = False
                if self._timer_job is not None:
                    self.after_cancel(self._timer_job)
                    self._timer_job = None
            except:
                pass

        try:
            self.after(0, _stop)
        except:
            pass

    def set_training_info(self, config):
        def _update():
            try:
                cfg = dict(config or {})
                model_text = str(cfg.get("model") or cfg.get("weights") or "未配置")
                epochs = int(cfg.get("epochs", 100))
                data_text = str(cfg.get("data") or cfg.get("data_yaml") or cfg.get("dataset") or "未配置")
                project_text = str(cfg.get("project", "runs/train"))
                name_text = str(cfg.get("name", "exp"))
                output_text = f"{project_text}/{name_text}"

                self.total_epochs = epochs
                self.model_value_label.config(text=model_text)
                self.epoch_value_label.config(text=f"0 / {epochs}")
                self.data_value_label.config(text=f"当前数据集  {data_text}")
                self.output_value_label.config(text=f"输出目录  {output_text}")
            except:
                pass

        try:
            self.after(0, _update)
        except:
            pass

    def refresh_result_summary(self):
        try:
            self.total_time_label.config(text=f"总耗时  {self.runtime_value_label.cget('text')}")
        except:
            pass

    def set_result_paths(self, best_path=None, last_path=None):
        def _update():
            try:
                if best_path:
                    self.best_path_label.config(text=f"best.pt 路径  {best_path}")
                if last_path:
                    self.last_path_label.config(text=f"last.pt 路径  {last_path}")
            except:
                pass

        try:
            self.after(0, _update)
        except:
            pass

    def set_current_epoch(self, current_epoch, total_epochs=None):
        def _update():
            try:
                total = total_epochs if total_epochs is not None else self.total_epochs
                current = int(current_epoch)
                total = int(total)
                self.epoch_value_label.config(text=f"{current} / {total}")

                progress_value = 0
                if total > 0:
                    progress_value = max(0, min(100, int(current * 100 / total)))
                self.progress["value"] = progress_value
            except:
                pass

        try:
            self.after(0, _update)
        except:
            pass

    def set_loss_map(self, loss_value=None, map_value=None):
        def _update():
            try:
                if loss_value is not None:
                    self.loss_value_label.config(text=f"当前 loss  {loss_value}")
                    self.final_loss_label.config(text=f"最终 loss  {loss_value}"); self.refresh_result_summary()
                if map_value is not None:
                    self.map_value_label.config(text=f"当前 mAP  {map_value}")
                    self.final_map_label.config(text=f"最终 mAP  {map_value}"); self.refresh_result_summary()

                    map_float = float(map_value)
                    if self.best_map is None or map_float > self.best_map:
                        self.best_map = map_float
                        self.best_epoch_label.config(text="最佳轮次  " + self.epoch_value_label.cget("text")); self.refresh_result_summary()
            except:
                pass

        try:
            self.after(0, _update)
        except:
            pass

    def _parse_epoch_from_text(self, text):
        try:
            clean = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', str(text))
            clean = clean.replace('\r', ' ').replace('\n', ' ').strip()

            m = re.search(r'^\s*(\d+)\s*/\s*(\d+)', clean)
            if m:
                return int(m.group(1)), int(m.group(2))

            patterns = [
                r'epoch\s*[:=]?\s*(\d+)\s*/\s*(\d+)',
                r'(\d+)\s*/\s*(\d+)\s+.*epoch',
                r'epoch\s+(\d+)\s+of\s+(\d+)',
            ]

            lower_text = clean.lower()
            for pattern in patterns:
                m = re.search(pattern, lower_text)
                if m:
                    return int(m.group(1)), int(m.group(2))

            m = re.search(r'epoch\s*[:=]?\s*(\d+)', lower_text)
            if m:
                return int(m.group(1)), None
        except:
            pass
        return None, None

    def _parse_metrics_from_text(self, text):
        loss_value = None
        map_value = None

        try:
            clean = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', str(text))
            clean = clean.replace('\r', ' ').replace('\n', ' ').strip()

            m = re.search(r'^\s*\d+\s*/\s*\d+\s+([0-9.]+G)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)', clean)
            if m:
                box_loss = m.group(2)
                cls_loss = m.group(3)
                dfl_loss = m.group(4)
                loss_value = f"{box_loss}/{cls_loss}/{dfl_loss}"

            m_table = re.search(r'^\s*all\s+\d+\s+\d+\s+([0-9]*\.?[0-9]+)\s+([0-9]*\.?[0-9]+)\s+([0-9]*\.?[0-9]+)\s+([0-9]*\.?[0-9]+)\s*$', clean, flags=re.IGNORECASE)
            if m_table:
                map_value = m_table.group(3)

            patterns_loss = [
                r'loss\s*[:=]?\s*([0-9]*\.?[0-9]+)',
                r'box_loss\s*[:=]?\s*([0-9]*\.?[0-9]+)',
                r'train/box_loss\s*[:=]?\s*([0-9]*\.?[0-9]+)',
            ]

            patterns_map = [
                r'metrics/mAP50-95\(B\)\s*[:=]?\s*([0-9]*\.?[0-9]+)',
                r'metrics/mAP50\(B\)\s*[:=]?\s*([0-9]*\.?[0-9]+)',
                r'map50-95\s*[:=]?\s*([0-9]*\.?[0-9]+)',
                r'map50\s*[:=]?\s*([0-9]*\.?[0-9]+)',
                r'\bmAP\b\s*[:=]?\s*([0-9]*\.?[0-9]+)',
            ]

            if loss_value is None:
                for pattern in patterns_loss:
                    m = re.search(pattern, clean, flags=re.IGNORECASE)
                    if m:
                        loss_value = m.group(1)
                        break

            for pattern in patterns_map:
                m = re.search(pattern, clean, flags=re.IGNORECASE)
                if m:
                    map_value = m.group(1)
                    break
        except:
            pass

        return loss_value, map_value

    def set_status(self, text):
        def _update():
            try:
                status_text = str(text)
                self.status_value_label.config(text=status_text)

                if status_text == "训练中":
                    if not self._timer_running:
                        self.start_runtime()
                elif status_text in ["已完成", "启动失败", "已停止"]:
                    self.stop_runtime()
            except:
                pass

        try:
            self.after(0, _update)
        except:
            pass

    def append_log(self, message):
        def _write():
            try:
                if message is None:
                    return

                text = str(message).rstrip()
                if not text:
                    return

                current_epoch, total_epoch = self._parse_epoch_from_text(text)
                if current_epoch is not None:
                    self.set_current_epoch(current_epoch, total_epoch)

                loss_value, map_value = self._parse_metrics_from_text(text)
                if loss_value is not None or map_value is not None:
                    self.set_loss_map(loss_value, map_value)

                self.log_text.insert("end", text + "\n")
                self.log_text.see("end")
                self.update_idletasks()
            except:
                pass

        try:
            self.after(0, _write)
        except:
            pass

    def clear_log(self):
        def _clear():
            try:
                self.log_text.delete("1.0", "end")
            except:
                pass

        try:
            self.after(0, _clear)
        except:
            pass

    def show_page(self, page_name):
        self.current_page.set(page_name)

        for name, frame in self.pages.items():
            if name == page_name:
                frame.tkraise()

        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(bg="#2A3550", fg="#FFFFFF")
            else:
                btn.configure(bg="#1C2230", fg="#D9E1EA")


def open_training_monitor(master=None):
    if master is not None and hasattr(master, "_training_monitor_window"):
        win = getattr(master, "_training_monitor_window")
        try:
            if win is not None and win.winfo_exists():
                win.deiconify()
                win.lift()
                win.focus_force()
                return win
        except:
            pass

    win = TrainingMonitorWindow(master)

    if master is not None:
        try:
            master._training_monitor_window = win

            def _clear_ref():
                try:
                    if hasattr(master, "_training_monitor_window"):
                        master._training_monitor_window = None
                except:
                    pass

            win.protocol("WM_DELETE_WINDOW", lambda: (_clear_ref(), win.destroy()))
        except:
            pass

    return win


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    win = TrainingMonitorWindow(root)
    win.mainloop()













