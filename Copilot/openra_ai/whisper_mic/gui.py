import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QLineEdit, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor


class AIAssistantUI(QWidget):
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
        self.plan_text = QTextEdit()
        self.plan_text.setPlaceholderText("显示当前任务或计划...")
        self.plan_text.setReadOnly(True)
        self.plan_text.setCursor(Qt.ArrowCursor)
        self.plan_text.setStyleSheet(
            "QTextEdit { background-color: #f0f0f0; }")
        left_layout.addWidget(self.plan_label)
        left_layout.addWidget(self.plan_text)

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
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.handle_send)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        right_layout.addLayout(input_layout)

        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 3)

        self.setLayout(main_layout)

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
        self.append_dialog(text + " :玩家", align_right=True, color=QColor("blue"))

    def add_ai_dialog(self, text):
        self.append_dialog("AI副官: " + text, align_right=False, color=QColor("green"))


def create_ai_assistant_ui_instance():
    app = QApplication(sys.argv)
    window = AIAssistantUI()
    window.show()
    return app, window


if __name__ == "__main__":
    app, window = create_ai_assistant_ui_instance()
    sys.exit(app.exec_())
