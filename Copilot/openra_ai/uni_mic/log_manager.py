import logging
import os
from datetime import datetime
from typing import Optional

class LogManager:
    _instance = None
    
    def __new__(cls, log_level: str = "info", debug_mode: bool = False):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = logging.getLogger("AI_Assistant")
            cls._instance.logger.setLevel(logging.DEBUG)
            
            # 创建日志目录
            log_dir = "Logs"
            os.makedirs(log_dir, exist_ok=True)
            
            # 文件处理器
            file_handler = logging.FileHandler(
                filename=os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}.log"),
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_level = logging.DEBUG if debug_mode else logging.INFO
            console_handler.setLevel(console_level)
            
            # 格式化
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            cls._instance.logger.addHandler(file_handler)
            cls._instance.logger.addHandler(console_handler)
        return cls._instance

    @classmethod
    def get_logger(cls) -> logging.Logger:
        if cls._instance is None:
            # 如果未初始化，使用默认配置初始化
            cls("info", False)
        return cls._instance.logger