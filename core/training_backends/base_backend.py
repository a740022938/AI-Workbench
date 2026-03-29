class BaseTrainingBackend:
    def __init__(self):
        self.process = None
        self.is_running = False

    def start(self, training_config, monitor_window=None):
        raise NotImplementedError

    def stop(self, monitor_window=None):
        raise NotImplementedError

    def resume(self, training_config, monitor_window=None):
        raise NotImplementedError

    def get_status(self):
        return {
            "is_running": self.is_running
        }
