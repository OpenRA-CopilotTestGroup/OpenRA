from typing import Dict, Any, Optional
import threading
from .log_manager import LogManager
import time
import uuid
import traceback
from .ui_manager import UIManager


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

    def stop_all(self):
        """通知所有错误处理器终止"""
        for handler in self.error_handlers.values():
            handler.stop()

class ErrorHandler:
    """错误处理器"""
    def __init__(self, ai_assistant):
        self.handler_id = str(uuid.uuid4())
        if ai_assistant is None:
             raise ValueError("ai_assistant cannot be None for ErrorHandler")
        self.ai_assistant = ai_assistant
        self.is_handling = False
        self.handling_thread = None
        self.created_at = time.time()
        self.response_id = None  # 只保存当前错误的response_id
        self.retry_count = 0  # 当前错误的重试次数
        self._stop_event = threading.Event()  # 新增

    def stop(self):
        """外部调用，通知线程终止"""
        self._stop_event.set()

    def handle_error(self, error_info: Dict[Any, Any], ui_manager: Optional[UIManager] = None, initial_response_id: Optional[str] = None):
        """处理错误"""
        if not getattr(self.ai_assistant.config, 'retry_when_failed', False) or self.is_handling:
            logger.warning(f"错误处理已跳过。重试已启用: {getattr(self.ai_assistant.config, 'retry_when_failed', False)}, 正在处理中: {self.is_handling}")
            return

        self.response_id = initial_response_id
        self.retry_count = 0
        self.is_handling = True

        logger.info(f"开始异步错误处理 (Handler ID: {self.handler_id})")
        self.handling_thread = threading.Thread(
            target=self._handle_error_async,
            args=(error_info, ui_manager),
            name=f"ErrorHandler-{self.handler_id[:10]}"
        )
        self.handling_thread.start()

    def _handle_error_async(self, error_info: Dict[Any, Any], ui_manager: Optional[UIManager]):
        """异步处理错误"""
        try:
            max_retries = getattr(self.ai_assistant.config, 'max_retry_times', 1)
            while self.retry_count < max_retries and not self._stop_event.is_set():
                self.retry_count += 1
                logger.info(f"第 {self.retry_count}/{max_retries} 次尝试修复...")

                try:
                    if ui_manager:
                        ui_manager.post_ai_dialog(f"正在尝试修复错误 (尝试 {self.retry_count})...", False)
                except Exception as e:
                    logger.error(f"UI更新失败: {e}")

                try:
                    success, new_response_id = self.ai_assistant.handle_error_with_llm(
                        error_info, 
                        self.response_id
                    )
                    if success:
                        logger.info("找到解决方案并已执行")
                        break
                    else:
                        logger.info("未找到解决方案，继续尝试...")
                        self.response_id = new_response_id
                except Exception as e:
                    logger.error(f"错误处理失败: {e}\n{traceback.format_exc()}")
                    break

                if self._stop_event.is_set():
                    logger.info("收到终止信号，修复线程即将退出。")
                    break

            if self.retry_count >= max_retries:
                logger.warning(f"达到最大重试次数 ({max_retries})，无法修复。")
                if ui_manager:
                    ui_manager.post_ai_dialog("已达到最大重试次数，无法修复错误。", False)
                    ui_manager.post_ai_dialog(f"对不起，我未能修复错误。")
        except Exception as e:
            logger.error(f"错误处理线程发生未捕获异常: {e}\n{traceback.format_exc()}")
        finally:
            self.is_handling = False 