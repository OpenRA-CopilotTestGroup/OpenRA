import os
import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QLabel, QPushButton, QHBoxLayout, QSpinBox, QFileDialog, QScrollArea
from PyQt5.QtCore import QTimer

class RatingManager:

    def __init__(self, prompt_dir, jsonl_path):
        self.prompt_dir = prompt_dir
        self.jsonl_path = jsonl_path
        self.ratings = self._load_ratings()

    def _load_ratings(self):

        if not os.path.exists(self.jsonl_path):
            return []
        with open(self.jsonl_path, "r", encoding="utf-8") as file:
            return [json.loads(line) for line in file]

    def _save_ratings(self):

        with open(self.jsonl_path, "w", encoding="utf-8") as file:
            for record in self.ratings:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_prompt_status(self):

        prompt_files = [
            f for f in os.listdir(self.prompt_dir) if f.endswith(".json")
            and not f.endswith("ratings.jsonl")
        ]
        rated_files = {record["prompt_file_name"] for record in self.ratings}

        rated = []
        for record in self.ratings:
            if record["prompt_file_name"] in prompt_files:
                rated.append({
                    "name": record["prompt_file_name"],
                    "score": record.get("rate", 0)
                })
        unrated = [f for f in prompt_files if f not in rated_files]

        return rated, unrated

    def update_rating(self, prompt_file, score):

        for record in self.ratings:
            if record["prompt_file_name"] == prompt_file:
                record["rate"] = score
                break
        else:
            self.ratings.append({"prompt_file_name": prompt_file, "rate": score})
        self._save_ratings()

    def clean_invalid_entries(self):

        prompt_files = [
            f for f in os.listdir(self.prompt_dir) if f.endswith(".json")
            and not f.endswith("ratings.jsonl")
        ]
        self.ratings = [
            record for record in self.ratings if record["prompt_file_name"] in prompt_files
        ]
        self._save_ratings()

    def get_prompt_content(self, prompt_file):

        file_path = os.path.join(self.prompt_dir, prompt_file)
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return f"玩家输入: {data['player_input']}\n\n模型输出: {data['model_answer']}"


class RatingWindow(QDialog):

    def __init__(self, rating_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prompt 评分")
        self.setGeometry(200, 200, 600, 900)  # 初始窗口尺寸

        self.rating_manager = rating_manager

        self.select_dir_button = QPushButton("选择 Prompt 目录")
        self.select_dir_button.clicked.connect(self.select_directory)

        self.prompt_list = QListWidget()
        self.prompt_content = QLabel()
        self.prompt_content.setWordWrap(True)
        self.load_prompt_list()

        # 设置列表高度
        self.prompt_list.setFixedHeight(300)

        # 滚动区域设置
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.prompt_content)
        scroll_area.setFixedHeight(450)  # 内容显示区高度

        layout = QVBoxLayout()
        layout.addWidget(self.select_dir_button)
        layout.addWidget(QLabel("选择一个 Prompt 并进行评分："))
        layout.addWidget(self.prompt_list)
        layout.addWidget(scroll_area)

        score_layout = QHBoxLayout()
        self.score_spinbox = QSpinBox()
        self.score_spinbox.setRange(1, 5)
        score_layout.addWidget(QLabel("评分："))
        score_layout.addWidget(self.score_spinbox)
        layout.addLayout(score_layout)

        self.save_button = QPushButton("保存评分")
        self.save_button.clicked.connect(self.save_rating)
        layout.addWidget(self.save_button)

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_prompt_list)
        layout.addWidget(self.refresh_button)

        # 定时器：每 10 秒自动刷新
        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.refresh_prompt_list)
        # self.timer.start(10000)

        # 固定窗口总高度
        # self.setFixedHeight(800)  # 300+450+其他控件≈800

        self.setLayout(layout)

    def load_prompt_list(self):
        self.prompt_list.clear()
        rated, unrated = self.rating_manager.get_prompt_status()

        # 创建有序字典保持文件名顺序
        all_prompts = sorted(
            [f for f in unrated] + [item["name"] for item in rated],
            key=lambda x: x.lower()
        )

        for prompt in all_prompts:
            # 判断是否已评分
            rated_item = next((item for item in rated if item["name"] == prompt), None)
            if rated_item:
                star = "★" * rated_item["score"] + "☆" * (5 - rated_item["score"])
                self.prompt_list.addItem(f"[已评分 {star}] {prompt}")
            else:
                self.prompt_list.addItem(f"[未评分] {prompt}")

        # Connect selection change event
        self.prompt_list.itemSelectionChanged.connect(self.on_item_selected)

    def refresh_prompt_list(self):

        self.rating_manager.clean_invalid_entries()
        self.load_prompt_list()
        self.prompt_content.clear()  # Clear content when refreshing list

    def save_rating(self):

        current_item = self.prompt_list.currentItem()
        if not current_item:
            return

        prompt_name = current_item.text().split("] ")[1]
        score = self.score_spinbox.value()

        self.rating_manager.update_rating(prompt_name, score)
        self.refresh_prompt_list()

    def select_directory(self):

        selected_dir = QFileDialog.getExistingDirectory(self, "选择 Prompt 目录", "prompt/")
        if not selected_dir:
            return

        jsonl_path = os.path.join(selected_dir, "ratings.jsonl")

        # 重新创建 RatingManager 以更新目录
        self.rating_manager = RatingManager(selected_dir, jsonl_path)
        self.refresh_prompt_list()

    def on_item_selected(self):
        current_item = self.prompt_list.currentItem()
        if current_item:
            prompt_name = current_item.text().split("] ")[1]
            content = self.rating_manager.get_prompt_content(prompt_name)
            self.prompt_content.setText(content)

