import json
import os
import subprocess
import sys
import threading

from core.training_backends.base_backend import BaseTrainingBackend


class YoloTrainingBackend(BaseTrainingBackend):
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.last_project = None
        self.last_name = None
        self.last_run_dir = None
        self.last_weights_dir = None
        self.last_best_pt = None
        self.last_last_pt = None

    def _emit(self, monitor_window, message):
        try:
            if monitor_window is not None:
                monitor_window.append_log(message)
        except:
            pass

    def _set_status(self, monitor_window, text):
        try:
            if monitor_window is not None:
                monitor_window.set_status(text)
        except:
            pass

    def _set_result_paths(self, monitor_window):
        try:
            if monitor_window is not None:
                monitor_window.set_result_paths(
                    best_path=self.last_best_pt,
                    last_path=self.last_last_pt
                )
        except:
            pass

    def _update_run_paths(self, cfg):
        project = str(cfg.get("project", "runs/train"))
        name = str(cfg.get("name", "exp"))

        self.last_project = project
        self.last_name = name
        self.last_run_dir = os.path.join(project, name)
        self.last_weights_dir = os.path.join(self.last_run_dir, "weights")
        self.last_best_pt = os.path.join(self.last_weights_dir, "best.pt")
        self.last_last_pt = os.path.join(self.last_weights_dir, "last.pt")

    def _build_train_script(self):
        return r'''
import json
import sys
from ultralytics import YOLO

cfg = json.loads(sys.argv[1])

data_path = cfg.get("data") or cfg.get("data_yaml") or cfg.get("dataset")
model_path = cfg.get("model") or cfg.get("weights") or "yolov8n.pt"

epochs = int(cfg.get("epochs", 100))
batch = int(cfg.get("batch_size", cfg.get("batch", 16)))
imgsz = int(cfg.get("imgsz", 640))
device = str(cfg.get("device", "0"))
project = str(cfg.get("project", "runs/train"))
name = str(cfg.get("name", "exp"))
workers = int(cfg.get("workers", 4))
patience = int(cfg.get("patience", 50))
exist_ok = bool(cfg.get("exist_ok", True))
save = bool(cfg.get("save", True))
cache = cfg.get("cache", False)
resume = cfg.get("resume", False)

print("[训练] YOLO 训练启动")
print(f"[训练] model={model_path}")
print(f"[训练] data={data_path}")
print(f"[训练] epochs={epochs} batch={batch} imgsz={imgsz} device={device}")
print(f"[训练] project={project} name={name} resume={resume}")

if resume and isinstance(resume, str):
    model = YOLO(resume)
    model.train(resume=True)
else:
    model = YOLO(model_path)
    model.train(
        data=data_path,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=project,
        name=name,
        workers=workers,
        patience=patience,
        exist_ok=exist_ok,
        save=save,
        cache=cache,
        resume=bool(resume)
    )

print("[训练] 训练完成")
'''

    def _start_worker(self, training_config, monitor_window=None):
        try:
            cfg = dict(training_config or {})
            self._update_run_paths(cfg)
            self._set_result_paths(monitor_window)

            data_path = cfg.get("data") or cfg.get("data_yaml") or cfg.get("dataset")
            resume_value = cfg.get("resume", False)

            if not data_path and not resume_value:
                self._set_status(monitor_window, "启动失败")
                self._emit(monitor_window, "[训练] 未配置 data 或 data_yaml，无法启动训练")
                return

            self._set_status(monitor_window, "训练中")

            cmd = [
                sys.executable,
                "-u",
                "-c",
                self._build_train_script(),
                json.dumps(cfg, ensure_ascii=False),
            ]

            self._emit(monitor_window, "[训练] 正在启动训练进程...")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            if self.process.stdout is not None:
                for line in self.process.stdout:
                    self._emit(monitor_window, line.rstrip())

            return_code = self.process.wait()

            self._set_result_paths(monitor_window)

            if return_code == 0:
                self._set_status(monitor_window, "已完成")
            else:
                self._set_status(monitor_window, "启动失败")

            self._emit(monitor_window, f"[训练] 进程结束 返回码={return_code}")

        except Exception as e:
            self._set_status(monitor_window, "启动失败")
            self._emit(monitor_window, f"[训练] 启动失败: {e}")
        finally:
            self.is_running = False
            self.process = None

    def start(self, training_config, monitor_window=None):
        if self.is_running:
            self._set_status(monitor_window, "已有任务")
            self._emit(monitor_window, "[训练] 已有任务在运行中")
            return False

        self.is_running = True
        self._set_status(monitor_window, "准备启动")

        self.worker_thread = threading.Thread(
            target=self._start_worker,
            args=(training_config, monitor_window),
            daemon=True
        )
        self.worker_thread.start()
        return True

    def stop(self, monitor_window=None):
        try:
            if self.process is not None and self.is_running:
                self.process.terminate()
                self._set_status(monitor_window, "已停止")
                self._emit(monitor_window, "[训练] 已发送停止信号")
                return True
            self._emit(monitor_window, "[训练] 当前没有运行中的训练任务")
            return False
        except Exception as e:
            self._emit(monitor_window, f"[训练] 停止失败: {e}")
            return False

    def resume(self, training_config, monitor_window=None):
        cfg = dict(training_config or {})

        if self.last_last_pt:
            last_pt = self.last_last_pt
        else:
            project = str(cfg.get("project", "runs/train"))
            name = str(cfg.get("name", "exp"))
            last_pt = os.path.join(project, name, "weights", "last.pt")

        self._emit(monitor_window, f"[训练] 尝试继续训练: {last_pt}")

        if not os.path.exists(last_pt):
            self._set_status(monitor_window, "启动失败")
            self._emit(monitor_window, "[训练] 未找到 last.pt，无法继续训练")
            return False

        cfg["resume"] = last_pt
        self._update_run_paths(cfg)
        self._set_result_paths(monitor_window)
        self._emit(monitor_window, "[训练] 已找到 last.pt，准备断点续训")
        return self.start(cfg, monitor_window)
