# COPILOT_PROMPT_IGNORE
# 该代码对应指令为：装甲车去对面基地勾引一下，遇到敌人就回来点，然后把步兵和防空车压上去，等都到了就两路夹击地方基地
import OpenRA_Copilot_Library as OpenRA
from OpenRA_Copilot_Library import TargetsQueryParam
import time
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QApplication, QWidget

api = OpenRA.GameAPI("localhost")

# time.sleep(3)
tanks = api.query_actor(TargetsQueryParam(type=['防空车'], faction='己方'))
enger = api.query_actor(TargetsQueryParam(type=['工程师'], faction='己方'))

armored_car = api.query_actor(TargetsQueryParam(type=['装甲车'], faction='己方'))[0]
# enemy_base = api.query_actor(TargetsQueryParam(type=['基地'], faction='敌方'))[0]
# api.attack_target(tanks,enemy_base)
playerinfo = api.player_base_info_query()
mapinfo = api.map_query()
screeninfo = api.screen_info_query()
if screeninfo.IsMouseOnScreen:
    api.move_units_by_location(tanks, screeninfo.MousePosition)

print(playerinfo)
# print(mapinfo)
print(screeninfo.to_dict())


class BoolMatrixVisualizer(QWidget):
    def __init__(self, matrix, cell_size=10):
        super().__init__()
        self.matrix = matrix  # n * m bool matrix
        self.cell_size = cell_size
        self.setWindowTitle('Bool Matrix Visualization')
        self.setGeometry(100, 100, len(matrix) * cell_size,
                         len(matrix[0]) * cell_size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for row_idx, row in enumerate(self.matrix):
            for col_idx, val in enumerate(row):
                color = QColor(0, 255, 0) if val else QColor(
                    255, 0, 0)  # True=green, False=red
                painter.setBrush(color)
                painter.drawRect(row_idx * self.cell_size, col_idx *
                                 self.cell_size, self.cell_size, self.cell_size)

        painter.end()


if __name__ == '__main__':
    app = QApplication([])

    visualizer = BoolMatrixVisualizer(mapinfo.IsVisible)
    # visualizer = BoolMatrixVisualizer(mapinfo.IsExplored)
    visualizer.show()

    app.exec_()
