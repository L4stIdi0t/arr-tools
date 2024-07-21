import logging
import os


class LoggingManager:
    def __init__(self, log_file_name="main.log"):
        self.logger = None
        file_path_base = "./data/logs"
        os.makedirs(file_path_base, exist_ok=True)
        self.log_file_path = os.path.join(file_path_base, log_file_name)
        self.setup_logging()

    def setup_logging(self):
        # Create a logger
        self.logger = logging.getLogger('central_logger')
        self.logger.setLevel(logging.DEBUG)

        # Create a file handler
        fh = logging.FileHandler(self.log_file_path)
        fh.setLevel(logging.DEBUG)

        # Create a formatter and set the formatter for the handler
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)

        # Add the handler to the logger
        self.logger.addHandler(fh)

    def log(self, message, level=logging.INFO, print_message=True):
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
