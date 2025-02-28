import sys
from PyQt6 import QtCore, QtWidgets, QtGui

class MainGraphicView(QtWidgets.QGraphicsView):
    def __init__(self):
        super().__init__()
        self.SCALE_FACTOR = 1.25
        self.scene = QtWidgets.QGraphicsScene()
        self.img = QtWidgets.QGraphicsPixmapItem()
        self.img.setPixmap(QtGui.QPixmap("Worldmap_grid.png"))
        self.scene.addItem(self.img)
        self.setScene(self.scene)

        # self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.zoom_value = 0
        self.resetView(self.SCALE_FACTOR ** float(self.zoom_value))

        self.x0 = 39
        self.x1 = 2520
        self.y0 = 19
        self.y1 = 1263
        self.ymid = (self.y1 - self.y0) / 2
        self.xsq0 = 1200
        self.xsq1 = 1408
        self.pix_height = self.y1 - self.y0
        self.ppgh = self.pix_height / 180
        self.width = self.x1 - self.x0
        self.ppgw = (self.xsq1 - self.xsq0) / 30

        self.pic_sat = QtWidgets.QGraphicsPixmapItem()
        self.pic_sat.setPixmap(QtGui.QPixmap('sat.png').scaled(50, 50))
        self.scene.addItem(self.pic_sat)
        satx, saty = self.geotoPix(-71, 65)
        satx -= 25
        saty -= 25
        self.pic_sat.setPos(satx, saty)
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
                # print(f'mouse is on pixmap at coordinates {geocoo}')
                self.pic_base.setPos(map.x() - 25, map.y() - 25)

        return super().eventFilter(source, event)

    def moveSatto(self, lon, lat):
        pass

    def geotoPix(self, lon, lat):
        y = lon * self.ppgh
        y = self.ymid + self.y0 - y
        x = lat * self.ppgw
        x = self.xsq0 - x
        return x, y


    def pixtoGeo(self, x, y):
        print(f'pixmap at coordinates x:{x} y:{y}')

        y = y - self.y0
        pixy = 90 - (y / self.ppgh)
        print(pixy)

        pixx = - (x - self.xsq0) / self.ppgw
        print(pixx)

        return x, y

    def resetView(self, scale=1):
        rect = QtCore.QRectF(self.img.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if (scale := max(1, scale)) == 1:
                self.zoom_value = 0
            unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
            self.scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.viewport().rect()
            scenerect = self.transform().mapRect(rect)
            factor = min(viewrect.width() / scenerect.width(),
                         viewrect.height() / scenerect.height()) * scale
            self.scale(factor, factor)
            # self.updateCoordinates()

    def zoom(self, step):
        zoom = max(0, self.zoom_value + (step := int(step)))
        if zoom != self.zoom_value:
            self._zoom = zoom
            if self._zoom > 0:
                if step > 0:
                    factor = self.SCALE_FACTOR ** step
                else:
                    factor = 1 / self.SCALE_FACTOR ** abs(step)
                self.scale(factor, factor)
            else:
                self.resetView()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.zoom(delta and delta // abs(delta))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resetView()


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
