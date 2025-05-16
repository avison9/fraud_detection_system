# logger_config.py

import os
import logging
from logging.handlers import TimedRotatingFileHandler

class ConsumerLogger:
    def __init__(self, log_name=None):
        if log_name is None:
            log_name = os.path.basename(__file__)
            log_name =  os.path.splitext(file_name)[0]

        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_dir = os.path.join(parent_dir, "logs")
        os.makedirs(self.log_dir, exist_ok=True)

        log_file = os.path.join(self.log_dir, f"{log_name}.log")

        # Create a time-based rotating file handler (daily rotation)
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when='midnight',           
            interval=1,                
            backupCount=7,             
            encoding='utf-8',
            utc=True                   
        )
        file_handler.suffix = "%Y-%m-%d"  

        # Set formatter
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        file_handler.setFormatter(formatter)

        # Create logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        # Avoid duplicate handlers if this is re-initialized
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(logging.StreamHandler())

    def get_logger(self):
        return self.logger

