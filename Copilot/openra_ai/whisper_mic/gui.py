import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QLineEdit, QFrame, QListWidget, QListWidgetItem, QGridLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
import pyttsx3


class AIAssistantUI(QWidget):
    player_dialog_signal = pyqtSignal(object, str)
    ui_exit_signal = pyqtSignal(object)

    def closeEvent(self, event):
        self.ui_exit_signal.emit(self)

    def __init__(self):
        super().__init__()

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
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.9)

    def handle_send(self):
        user_input = self.input_field.text()

        if user_input:
            self.add_player_dialog(user_input)
            self.input_field.clear()

            ai_reply = "好的，正在执行..."
            self.add_ai_dialog(ai_reply)

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
        # 回调
        self.player_dialog_signal.emit(self, text)

    def add_ai_dialog(self, text):
        self.append_dialog("AI副官: " + text, align_right=False,
                           color=QColor("green"))
        self.speak_text(text)

    def speak_text(self, text):
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

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

        widget.setLayout(layout)
        widget.setStyleSheet("border: 1px solid black; padding: 5px;")

        item = QListWidgetItem(self.plan_list)
        item.setSizeHint(widget.sizeHint())
        self.plan_list.addItem(item)
        self.plan_list.setItemWidget(item, widget)

        return item, status_label

    def update_plan_item_status(self, item, status_label, status):
        status_label.setText(status)
        self.set_status_label_color(status_label, status)

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


def create_ai_assistant_ui_instance():
    app = QApplication(sys.argv)
    window = AIAssistantUI()
    window.show()
    return app, window


if __name__ == "__main__":
    app, window = create_ai_assistant_ui_instance()

    def example_callback(this, player_input):
        print(f"Player said: {player_input} from instance: {this}")

    window.player_dialog_signal.connect(example_callback)

    window.add_plan_item("优先攻击火箭兵", "进行中")
    window.add_plan_item("建造三个步兵，两个坦克", "失败")
    window.add_plan_item("工程师占领油田", "已完成")
    window.add_plan_item("两路夹击地方基地，如果打不过就折返", "未开始")
    sys.exit(app.exec_())
