import threading
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QLabel, QListWidgetItem, QWidget # Import necessary types for signals
from typing import TYPE_CHECKING, Optional

# Prevent circular imports for type hinting
if TYPE_CHECKING:
    from .gui import AIAssistantUI 

class UIManager(QObject):
    """处理所有与GUI交互的线程安全管理器"""

    # --- Signals to trigger GUI updates on the main thread ---
    _signal_add_player_dialog = pyqtSignal(str)
    _signal_add_ai_dialog = pyqtSignal(str, bool)
    _signal_add_plan_item = pyqtSignal(str, str)
    # Passing complex Qt objects like QLabel through signals requires registration
    # or careful handling. Passing the plan name might be safer for status updates.
    # Let's try passing QLabel reference carefully first.
    _signal_update_plan_status = pyqtSignal(QLabel, str) 
    _signal_set_memory_content = pyqtSignal(str)
    _signal_set_plan_item_widget = pyqtSignal(QListWidgetItem, QWidget) # Added for plan item widget setting

    def __init__(self, gui_instance: 'AIAssistantUI', parent=None):
        super().__init__(parent)
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("UIManager must be instantiated in the main GUI thread.")
        
        if gui_instance is None:
             raise ValueError("GUI instance cannot be None for UIManager")
        self.gui = gui_instance

        # --- Connect signals to the GUI's actual update methods ---
        # These GUI methods should now assume they are called *only* from the main thread.
        self._signal_add_player_dialog.connect(self.gui.add_player_dialog)
        self._signal_add_ai_dialog.connect(self.gui.add_ai_dialog)
        self._signal_add_plan_item.connect(self.gui.add_plan_item)
        self._signal_update_plan_status.connect(self.gui.update_plan_item_status)
        self._signal_set_memory_content.connect(self.gui.set_memory_content)
        # Connect the widget setting signal
        self._signal_set_plan_item_widget.connect(
            lambda item, widget: self.gui.plan_list.setItemWidget(item, widget)
        )

    # --- Public methods for business logic to call ---

    def post_player_dialog(self, text: str):
        """异步请求添加玩家对话"""
        self._signal_add_player_dialog.emit(text)

    def post_ai_dialog(self, text: str, need_tts: bool = True):
        """异步请求添加AI对话"""
        self._signal_add_ai_dialog.emit(text, need_tts)

    def post_plan_item(self, plan_name: str, status: str = "未开始"):
        """
        异步请求添加计划项。
        注意：此方法不直接返回QLabel，因为它是异步的。
        如果需要Label引用，需要更复杂的机制（例如回调或通过plan_name查找）。
        """
        self._signal_add_plan_item.emit(plan_name, status)

    def post_update_plan_status(self, status_label: QLabel, status: str):
        """异步请求更新计划状态"""
        if status_label: # Ensure label exists
            self._signal_update_plan_status.emit(status_label, status)
        # Else: log a warning? How to handle if label wasn't obtained?

    def post_set_memory_content(self, content: str):
        """异步请求设置记忆内容"""
        self._signal_set_memory_content.emit(content)
        
    def post_set_plan_item_widget(self, item: QListWidgetItem, widget: QWidget):
        """异步请求设置计划项的自定义Widget"""
        self._signal_set_plan_item_widget.emit(item, widget)

    def get_all_plans(self):
        """获取所有计划 (假设此操作可以安全地从任何线程读取，或需要同步)"""
        # Reading might be safe, but depends on how plan_items is modified.
        # For simplicity, assume read is safe. If not, needs locking or signal.
        return self.gui.get_all_plans() # Direct call, assuming read safety 