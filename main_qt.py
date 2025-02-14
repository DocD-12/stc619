import sys
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsRectItem, QGraphicsView, QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        scene = QGraphicsScene()
        scene.addText("Hello, world!")
        scene.addPixmap(QPixmap("Worldmap_grid.png"))

        view = QGraphicsView(scene)

        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout()
        l.addWidget(view)
        w.setLayout(l)

        self.setCentralWidget(w)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
