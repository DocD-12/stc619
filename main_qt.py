import sys
from PyQt6 import QtCore, QtWidgets, QtGui


class MainGraphicView(QtWidgets.QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addPixmap(QtGui.QPixmap("Worldmap_grid.png"))
        self.setScene(self.scene)

        self.x0 = 39
        self.x1 = 2520
        self.y0 = 19
        self.y1 = 1263

        self.pic_sat = QtWidgets.QGraphicsPixmapItem()
        self.pic_sat.setPixmap(QtGui.QPixmap('sat.png').scaled(50, 50))
        self.scene.addItem(self.pic_sat)

        self.pic_base = QtWidgets.QGraphicsPixmapItem()
        self.pic_base.setPixmap(QtGui.QPixmap('base.png').scaled(50, 50))
        self.scene.addItem(self.pic_base)

        self.scene.installEventFilter(self)
        self.setMouseTracking(True)


    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.Type.GraphicsSceneMouseRelease:
            item = self.scene.itemAt(event.scenePos(), QtGui.QTransform())
            if isinstance(item, QtWidgets.QGraphicsPixmapItem):
                # map the scene position to item coordinates
                map = item.mapFromScene(event.scenePos())
                # print(f'mouse is on pixmap at coordinates {map.x()}, {map.y()}')
                geocoo = self.pixtoGeo(map.x(), map.y())
                print(f'mouse is on pixmap at coordinates {geocoo}')
                self.pic_base.setPos(map.x() - 25, map.y() - 25)

        return super().eventFilter(source, event)

    def moveSatto(self, lon, lat):
        pass

    def geotoPix(self, lon, lat):
        pass

    def pixtoGeo(self, x, y):
        return x, y


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        w = QtWidgets.QWidget()
        l = QtWidgets.QVBoxLayout()
        l.addWidget(MainGraphicView())
        w.setLayout(l)

        self.setCentralWidget(w)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
