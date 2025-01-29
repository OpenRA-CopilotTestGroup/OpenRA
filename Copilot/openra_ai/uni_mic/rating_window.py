import os
import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QLabel, QPushButton, QHBoxLayout, QSpinBox, QFileDialog
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
            f for f in os.listdir(self.prompt_dir) if f.endswith("_player_prompt.txt")
        ]
        rated_files = {record["prompt_file_name"] for record in self.ratings}

        rated = [f for f in prompt_files if f in rated_files]
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
            f for f in os.listdir(self.prompt_dir) if f.endswith("_player_prompt.txt")
        ]
        self.ratings = [
            record for record in self.ratings if record["prompt_file_name"] in prompt_files
        ]
        self._save_ratings()


class RatingWindow(QDialog):

    def __init__(self, rating_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prompt 评分")
        self.setGeometry(200, 200, 600, 400)

        self.rating_manager = rating_manager

        self.select_dir_button = QPushButton("选择 Prompt 目录")
        self.select_dir_button.clicked.connect(self.select_directory)

        self.prompt_list = QListWidget()
        self.load_prompt_list()

        layout = QVBoxLayout()
        layout.addWidget(self.select_dir_button)
        layout.addWidget(QLabel("选择一个 Prompt 并进行评分："))
        layout.addWidget(self.prompt_list)

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
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_prompt_list)
        self.timer.start(10000)

        self.setLayout(layout)

    def load_prompt_list(self):

        self.prompt_list.clear()
        rated, unrated = self.rating_manager.get_prompt_status()

        for prompt in unrated:
            self.prompt_list.addItem(f"[未评分] {prompt}")
        for prompt in rated:
            self.prompt_list.addItem(f"[已评分] {prompt}")

    def refresh_prompt_list(self):

        self.rating_manager.clean_invalid_entries()
        self.load_prompt_list()

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