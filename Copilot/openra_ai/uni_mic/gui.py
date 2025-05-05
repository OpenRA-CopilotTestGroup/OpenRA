import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QLineEdit, QFrame, QListWidget, QListWidgetItem, QGridLayout
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
import pyttsx3
import threading
import pyaudio
import dashscope
import uuid
from dashscope.audio.tts_v2 import *
import os
import atexit
import edge_tts
import asyncio
import pyaudio
from playsound import playsound
import tempfile
import queue
import time
from .tts_manager import TTSManager
from typing import Optional
from .error_handler import ErrorHandlerManager


class AIAssistantUI(QWidget):
    player_dialog_signal = pyqtSignal(object, str)
    ui_exit_signal = pyqtSignal(object)
    qt_tick_signal = pyqtSignal(object)
    mic_state_signal = pyqtSignal(bool)
    
    def closeEvent(self, event):
        try:
            self.ui_exit_signal.emit(self)
            if hasattr(self, 'tts') and self.tts:
                self.tts.stop()
            ErrorHandlerManager().stop_all()
        except Exception as e:
            print(f"Error during closeEvent: {e}")
        event.accept()

    def __init__(self):
        super().__init__()

        self.tts = TTSManager()
        
        self.setWindowTitle("AI 副官")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        self.memory_label = QLabel("记忆内容")
        self.memory_text = QTextEdit()
        self.memory_text.setPlaceholderText("显示AI副官的记忆...")
        self.memory_text.setReadOnly(True)
        self.memory_text.setCursor(Qt.ArrowCursor)
        self.memory_text.setStyleSheet(
            "QTextEdit { background-color: #f0f0f0; }")
        left_layout.addWidget(self.memory_label)
        left_layout.addWidget(self.memory_text)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        left_layout.addWidget(line)

        self.plan_label = QLabel("当前计划")
        self.plan_list = QListWidget()
        left_layout.addWidget(self.plan_label)
        left_layout.addWidget(self.plan_list)

        right_layout = QVBoxLayout()

        self.dialog_label = QLabel("对话")
        self.dialog_text = QTextEdit()
        self.dialog_text.setPlaceholderText("显示玩家与AI副官的对话...")
        self.dialog_text.setReadOnly(True)
        self.dialog_text.setCursor(Qt.ArrowCursor)
        self.dialog_text.setStyleSheet(
            "QTextEdit { background-color: #f0f0f0; }")
        right_layout.addWidget(self.dialog_label)
        right_layout.addWidget(self.dialog_text)

        self.mic_button = QPushButton("当前麦克风状态: 开启")
        self.mic_button.clicked.connect(self.toggle_mic)
        right_layout.addWidget(self.mic_button)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入您的指令...")
        self.input_field.returnPressed.connect(self.handle_send)
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.handle_send)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        right_layout.addLayout(input_layout)

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 3)

        self.setLayout(main_layout)

        self.mic_enabled = True

        tick_timer = QTimer(self)
        tick_timer.timeout.connect(lambda: self.qt_tick_signal.emit(self))
        tick_timer.start(100)

        self.plan_items = {}

    def handle_send(self):
        user_input = self.input_field.text()

        if user_input:
            self.player_dialog_signal.emit(self, user_input)
            self.add_player_dialog(user_input)
            self.input_field.clear()

    def add_player_dialog(self, text):
        self.__append_dialog_safe(text + " :玩家", True, QColor("blue"))

    def add_ai_dialog(self, text, need_tts: bool = True):
        self.__append_dialog_safe("AI副官: " + text, False, QColor("green"))
        if need_tts:
            self.speak_text(text)

    def add_plan_item(self, plan_name: str, status: str = "未开始") -> QLabel:
        return self.__add_plan_item_safe(plan_name, status)

    def update_plan_item_status(self, status_label: QLabel, status: str):
        self.__update_plan_status_safe(status_label, status)

    def set_memory_content(self, content: str):
        self.__set_memory_content_safe(content)

    def speak_text(self, text):
        self.tts.play(text)

    def set_status_label_color(self, label, status):
        if status == "进行中":
            label.setStyleSheet("color: green;")
        elif status == "失败":
            label.setStyleSheet("color: red;")
        elif status == "已完成":
            label.setStyleSheet("color: gray;")
        else:
            label.setStyleSheet("color: black;")

    def get_memory_content(self):
        return self.memory_text.toPlainText()

    def toggle_mic(self):
        self.mic_enabled = not self.mic_enabled
        self.mic_button.setText(
            "当前麦克风状态: 开启" if self.mic_enabled else "当前麦克风状态: 关闭")
        self.mic_state_signal.emit(self.mic_enabled)
        self.add_ai_dialog("麦克风已{}。".format(
            "开启" if self.mic_enabled else "关闭"), False)

    def get_all_plans(self):
        return [
            {
                'name': plan_name,
                'status': item['status'],
                'timestamp': item['timestamp']
            }
            for plan_name, item in self.plan_items.items()
        ]

    def __append_dialog_safe(self, text, align_right, color):
        cursor = self.dialog_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        char_format = QTextCharFormat()
        char_format.setForeground(color)

        if align_right:
            block_format = cursor.blockFormat()
            block_format.setAlignment(Qt.AlignRight)
            cursor.setBlockFormat(block_format)
        else:
            block_format = cursor.blockFormat()
            block_format.setAlignment(Qt.AlignLeft)
            cursor.setBlockFormat(block_format)

        cursor.insertText(text, char_format)
        cursor.insertBlock()

        self.dialog_text.setTextCursor(cursor)
        self.dialog_text.ensureCursorVisible()

    def __add_plan_item_safe(self, plan_name: str, status: str) -> QLabel:
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        plan_label = QLabel(plan_name)
        plan_label.setWordWrap(True)
        plan_label.setStyleSheet("color: black;")
        layout.addWidget(plan_label)

        status_label = QLabel(status)
        status_label.setFixedWidth(80)
        status_label.setAlignment(Qt.AlignCenter)
        self.set_status_label_color(status_label, status)
        layout.addWidget(status_label)

        self.plan_items[plan_name] = {
            'label': status_label,
            'status': status,
            'timestamp': time.time()
        }

        widget.setLayout(layout)
        widget.setStyleSheet("border: 1px solid black; padding: 5px;")

        item = QListWidgetItem()
        self.plan_list.insertItem(0, item)
        item.setSizeHint(widget.sizeHint())
        
        self.plan_list.setItemWidget(item, widget) 
        
        self.plan_list.scrollToBottom()
        return status_label

    def __update_plan_status_safe(self, status_label: QLabel, status: str):
        status_label.setText(status)
        self.set_status_label_color(status_label, status)
        for plan_name, item_data in self.plan_items.items():
            if item_data['label'] == status_label:
                item_data['status'] = status
                break

    def __set_memory_content_safe(self, content: str):
        self.memory_text.setText(content)

    def __append_dialog_safe_wrapper_player(self, text):
        self.add_player_dialog(text)


def create_ai_assistant_ui_instance():
    app = QApplication(sys.argv)
    window = AIAssistantUI()
    window.show()
    return app, window

import traceback
def handle_exception(exc_type, exc_value, exc_traceback):
    print("捕获到异常:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    sys.exit(1)

def on_exit():
    print("程序正在退出...")
    print("".join(traceback.format_stack()))
    
atexit.register(on_exit)


if __name__ == "__main__":
    app, window = create_ai_assistant_ui_instance()

    def example_callback(this, player_input):
        print(f"Player said: {player_input} from instance: {this}")
        this.add_ai_dialog(player_input)

    window.player_dialog_signal.connect(example_callback)

    window.add_plan_item("长度测试长度测试长度测试长度测试长度测试长度测试长度测试长度测试", "未开始")
    window.add_plan_item("优先攻击火箭兵", "进行中")
    window.add_plan_item("建造三个步兵，两个坦克", "失败")
    window.add_plan_item("工程师占领油田", "已完成")
    window.add_plan_item("两路夹击地方基地，如果打不过就折返", "未开始")

    b = window.add_plan_item("长度测试长度测试长度测试长度测试长度测试长度测试长度测试长度测试", "未开始")
    window.update_plan_item_status(b, "已完成")
    
    window.add_player_dialog("两路夹击地方基地") 
    window.add_ai_dialog("已经派遣步兵和防空车，从上下两路进攻敌方基地")
    
    sys.exit(app.exec_())
