from core.training_backends.yolo_backend import YoloTrainingBackend


class TrainingRunner:
    def __init__(self):
        self.backend = YoloTrainingBackend()

    def start(self, training_config, monitor_window=None):
        return self.backend.start(training_config, monitor_window)

    def stop(self, monitor_window=None):
        return self.backend.stop(monitor_window)

    def resume(self, training_config, monitor_window=None):
        return self.backend.resume(training_config, monitor_window)

    def get_status(self):
        return self.backend.get_status()
