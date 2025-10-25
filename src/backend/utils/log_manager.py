import logging
import os


class LoggingManager:
    def __init__(self, log_file_name="main.log"):
        self.logger = None
        file_path_base = "./data/logs"
        os.makedirs(file_path_base, exist_ok=True)
        self.log_file_path = os.path.join(file_path_base, log_file_name)
        self.debug_file_overwrite = False
        if any(os.path.exists(f"./data/DEBUG{ext}") for ext in ["", ".txt", ".log"]):
            self.debug_file_overwrite = True
            print("Debug file overwrite is enabled")

        self.setup_logging()

    def setup_logging(self):
        # Create a logger
        self.logger = logging.getLogger("central_logger")
        self.logger.setLevel(logging.INFO)
        if self.debug_file_overwrite:
            self.logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(self.log_file_path)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)

        self.logger.addHandler(fh)

    def log(self, message, level=logging.INFO, print_message=True):
        if not self.logger:
            print("Logger not initialized")

        if level == logging.DEBUG:
            self.logger.debug(message)
        elif level == logging.INFO:
            self.logger.info(message)
        elif level == logging.WARNING:
            self.logger.warning(message)
        elif level == logging.ERROR:
            self.logger.error(message)
        elif level == logging.CRITICAL:
            self.logger.critical(message)

        if print_message:
            print(message)

    def set_log_level(self, log_level):
        if self.debug_file_overwrite:
            self.log("Debug file overwrite is enabled, ignoring log level change")
            return
        self.logger.setLevel(log_level)
