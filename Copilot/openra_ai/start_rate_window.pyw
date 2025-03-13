import sys
import os
from PyQt5.QtWidgets import QApplication, QFileDialog
from uni_mic.rating_window import RatingWindow, RatingManager

def run_rating_window():
    app = QApplication(sys.argv)

    base_prompt_dir = "prompt/"
    selected_dir = QFileDialog.getExistingDirectory(None, "选择 Prompt 目录", base_prompt_dir)

    if not selected_dir:
        print("未选择目录，退出程序。")
        sys.exit(0)

    jsonl_path = os.path.join(selected_dir, "ratings.jsonl")

    rating_manager = RatingManager(selected_dir, jsonl_path)
    window = RatingWindow(rating_manager)
    window.exec_()

if __name__ == "__main__":
    run_rating_window()