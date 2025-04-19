from typing import Dict, Any, Optional
import threading
from .log_manager import LogManager
import time
import uuid

logger = LogManager.get_logger()

class ErrorHandlerManager:
    """错误处理管理器，管理所有错误处理实例"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorHandlerManager, cls).__new__(cls)
            cls._instance.error_handlers = {}
            cls._instance.cleanup_thread = None
            cls._instance._start_cleanup_thread()
        return cls._instance

    def _start_cleanup_thread(self):
        """启动清理线程"""
        def cleanup():
            while True:
                self._cleanup_old_handlers()
                time.sleep(300)  # 每5分钟清理一次
                
        self.cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        self.cleanup_thread.start()

    def _cleanup_old_handlers(self):
        """清理超时的错误处理器"""
        current_time = time.time()
        to_remove = []
        for handler_id, handler in self.error_handlers.items():
            if (current_time - handler.created_at) > 3600:  # 1小时后清理
                to_remove.append(handler_id)
        
        for handler_id in to_remove:
            self.error_handlers.pop(handler_id)

    def create_handler(self, ai_assistant) -> 'ErrorHandler':
        """创建新的错误处理器"""
        handler = ErrorHandler(ai_assistant)
        self.error_handlers[handler.handler_id] = handler
        return handler

    def get_handler(self, handler_id: str) -> Optional['ErrorHandler']:
        """获取错误处理器"""
        return self.error_handlers.get(handler_id)

class ErrorHandler:
    """错误处理器"""
    def __init__(self, ai_assistant):
        self.handler_id = str(uuid.uuid4())
        self.ai_assistant = ai_assistant
        self.is_handling = False
        self.handling_thread = None
        self.created_at = time.time()
        self.response_ids = {}  # Dict[error_id, response_id]
        self.retry_counts = {}  # Dict[error_id, retry_count]

    def handle_error(self, error_info: Dict[Any, Any], gui=None, initial_response_id: Optional[str] = None):
        """处理新的错误"""
        if not self.ai_assistant.config.retry_when_failed or self.is_handling:
            return

        error_id = f"{error_info['timestamp']}_{error_info['command']}"
        self.response_ids[error_id] = initial_response_id
        self.retry_counts[error_id] = 0

        self.is_handling = True
        self.handling_thread = threading.Thread(
            target=self._handle_error_async,
            args=(error_id, error_info, gui)
        )
        self.handling_thread.start()
        return error_id

    def _handle_error_async(self, error_id: str, error_info: Dict[Any, Any], gui):
        """异步处理错误"""
        try:
            while self.retry_counts[error_id] < self.ai_assistant.config.max_retry_times:
                current_try = self.retry_counts[error_id] + 1
                logger.info(f"尝试修复错误 {error_id}，第{current_try}次尝试")
                if gui:
                    gui.add_ai_dialog(f"正在尝试修复错误，第{current_try}次尝试...", False)

                # 调用错误处理并获取新的response id
                response, new_response_id = self.ai_assistant.handle_error_with_llm(
                    error_info, 
                    self.response_ids[error_id]
                )

                # 更新response id和重试次数
                if new_response_id:
                    self.response_ids[error_id] = new_response_id
                self.retry_counts[error_id] += 1

                if response and "没有解决方案" not in response:
                    if gui:
                        gui.add_ai_dialog("已找到可能的解决方案，正在尝试执行...", False)
                    # 执行修复后的代码
                    self.ai_assistant.handle_strategy_command(response, gui)
                    break

            if self.retry_counts[error_id] >= self.ai_assistant.config.max_retry_times:
                if gui:
                    gui.add_ai_dialog("已达到最大重试次数，无法修复错误。", False)
                # 清理数据
                self.response_ids.pop(error_id, None)
                self.retry_counts.pop(error_id, None)

        finally:
            self.is_handling = False

    def get_error_status(self, error_id: str) -> Optional[Dict[str, Any]]:
        """获取错误处理状态"""
        if error_id in self.retry_counts:
            return {
                "error_id": error_id,
                "retry_count": self.retry_counts[error_id],
                "response_id": self.response_ids.get(error_id),
                "is_handling": self.is_handling
            }
        return None 