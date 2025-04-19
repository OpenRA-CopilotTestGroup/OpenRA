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


class TTSPlayer(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.q = queue.Queue()
        self._stop = threading.Event()
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._main_loop())

    async def _main_loop(self):
        while not self._stop.is_set():
            try:
                text = self.q.get(timeout=0.5)
                await self._play_tts(text)
            except queue.Empty:
                continue

    async def _play_tts(self, text):
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        path = os.path.join(tempfile.gettempdir(), filename)

        tts = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural")
        await tts.save(path)
        playsound(path)
        os.remove(path)

    def play(self, text):
        self.q.put(text)

    def stop(self):
        self._stop.set()

usenormalTTS = False

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

if not dashscope.api_key:
    print("Environment variable 'DASHSCOPE_API_KEY' is not set!")
    usenormalTTS = True
model = "cosyvoice-v1"
voice = "longxiaoxia"


class Callback(ResultCallback):
    _player = None
    _stream = None

    def on_open(self):
        self._player = pyaudio.PyAudio()
        self._stream = self._player.open(
            format=pyaudio.paInt16, channels=1, rate=22050, output=True, frames_per_buffer=22050
        )

    def on_close(self):
        self._stream.stop_stream()
        self._stream.close()
        self._player.terminate()

    def on_data(self, data: bytes) -> None:
        print("audio result length:", len(data))
        self._stream.write(data)


def synthesizer_with_llm(text):
    callback = Callback()
    synthesizer = SpeechSynthesizer(
        model=model,
        voice=voice,
        format=AudioFormat.PCM_22050HZ_MONO_16BIT,
        callback=callback,
    )

    synthesizer.streaming_call(text)
    synthesizer.streaming_complete()
    print('requestId: ', synthesizer.get_last_request_id())



class AIAssistantUI(QWidget):
    player_dialog_signal = pyqtSignal(object, str)
    ui_exit_signal = pyqtSignal(object)
    qt_tick_signal = pyqtSignal(object)
    mic_state_signal = pyqtSignal(bool)
    ai_dialog_signal = pyqtSignal(str, bool)  # (text, need_tts)
    plan_status_signal = pyqtSignal(object, str)  # (status_label, status)

    def closeEvent(self, event):
        try:
            self.ui_exit_signal.emit(self)
            self.tts.stop()
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

        # TTS
        #self.tts_engine = pyttsx3.init(driverName='espeak')
        # self.tts_engine = pyttsx3.init()
        
        # self.tts_engine.setProperty('rate', 150)
        # self.tts_engine.setProperty('volume', 0.9)

        # self.tts_lock = threading.Lock()

        self.mic_enabled = True  # Initial mic state

        tick_timer = QTimer(self)
        tick_timer.timeout.connect(lambda: self.qt_tick_signal.emit(self))
        tick_timer.start(100)

        self.plan_items = {}  # 存储计划项和状态标签的映射

        # 连接信号到槽
        self.ai_dialog_signal.connect(self._add_ai_dialog_safe)
        self.plan_status_signal.connect(self._update_plan_status_safe)

    def handle_send(self):
        user_input = self.input_field.text()

        if user_input:
            self.player_dialog_signal.emit(self, user_input)
            self.add_player_dialog(user_input)
            self.input_field.clear()

            # ai_reply = "好的，正在执行..."
            # self.add_ai_dialog(ai_reply)

    def append_dialog(self, text, align_right=False, color=QColor("black")):
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

    def add_player_dialog(self, text):
        self.append_dialog(text + " :玩家", align_right=True,
                           color=QColor("blue"))

    def add_ai_dialog(self, text, need_tts: bool = True):
        """线程安全的添加AI对话"""
        self.ai_dialog_signal.emit(text, need_tts)

    def _add_ai_dialog_safe(self, text, need_tts):
        """在主线程中实际执行添加对话的操作"""
        self.append_dialog("AI副官: " + text, align_right=False,
                          color=QColor("green"))
        if need_tts:
            self.speak_text(text)

    def speak_text(self, text):
        self.tts.play(text)

    def add_plan_item(self, plan_name: str, status: str = "未开始"):
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

        item = QListWidgetItem(self.plan_list)
        item.setSizeHint(widget.sizeHint())
        self.plan_list.insertItem(0, item)
        self.plan_list.setItemWidget(item, widget)
        self.plan_list.scrollToBottom()
        return status_label

    def update_plan_item_status(self, status_label, status):
        """线程安全的更新计划状态"""
        self.plan_status_signal.emit(status_label, status)

    def _update_plan_status_safe(self, status_label, status):
        """在主线程中实际执行更新状态的操作"""
        status_label.setText(status)
        self.set_status_label_color(status_label, status)
        for plan_name, item in self.plan_items.items():
            if item['label'] == status_label:
                item['status'] = status
                break

    def set_status_label_color(self, label, status):
        if status == "进行中":
            label.setStyleSheet("color: green;")
        elif status == "失败":
            label.setStyleSheet("color: red;")
        elif status == "已完成":
            label.setStyleSheet("color: gray;")
        else:
            label.setStyleSheet("color: black;")

    def set_memory_content(self, content):
        self.memory_text.setText(content)

    def get_memory_content(self):
        return self.memory_text.toPlainText()

    def toggle_mic(self):
        self.mic_enabled = not self.mic_enabled
        self.mic_button.setText(
            "当前麦克风状态: 开启" if self.mic_enabled else "当前麦克风状态: 关闭")
        # Emit signal for state change
        self.mic_state_signal.emit(self.mic_enabled)
        self.add_ai_dialog("麦克风已{}。".format(
            "开启" if self.mic_enabled else "关闭"), False)

    def get_all_plans(self):
        """获取所有计划及其状态"""
        return [
            {
                'name': plan_name,
                'status': item['status'],
                'timestamp': item['timestamp']
            }
            for plan_name, item in self.plan_items.items()
        ]


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
