import sys
from PyQt6 import QtCore, QtWidgets, QtGui
from skyfield.api import load
from skyfield.toposlib import wgs84
from datetime import timedelta


class MainGraphicView(QtWidgets.QGraphicsView):
    def __init__(self):
        super().__init__()
        self.SCALE_FACTOR = 1.25
        self.scene = QtWidgets.QGraphicsScene()
        self.img = QtWidgets.QGraphicsPixmapItem()
        self.img.setPixmap(QtGui.QPixmap("Worldmap_grid.png"))
        self.scene.addItem(self.img)
        self.setScene(self.scene)

        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.zoom_value = 0
        self.reset_view(self.SCALE_FACTOR ** float(self.zoom_value))
        self.setTransformationAnchor(
            QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(
            QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

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

        self.pic_size = 30
        self.pic_size_2 = 30 // 2
        self.pic_sat = QtWidgets.QGraphicsPixmapItem()
        self.pic_sat.setPixmap(QtGui.QPixmap('sat.png').scaled(self.pic_size, self.pic_size))
        self.scene.addItem(self.pic_sat)
        self.pic_base = QtWidgets.QGraphicsPixmapItem()
        self.pic_base.setPixmap(QtGui.QPixmap('base.png').scaled(self.pic_size, self.pic_size))
        self.scene.addItem(self.pic_base)
        # self.scene.addEllipse(100, 100, 10, 10)

        self.scene.installEventFilter(self)
        self.setMouseTracking(True)

    def draw_dot_by_geo(self, lat, lon, color=QtGui.QColor('black'), size=5):
        pen = QtGui.QPen(color)
        brush = QtGui.QBrush()
        brush.setColor(color)
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        x, y = self.geo_to_pix(lat, lon)
        self.scene.addEllipse(x, y, size, size, pen, brush)

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.Type.GraphicsSceneMousePress:
            if event.button() == QtCore.Qt.MouseButton.RightButton:
                item = self.scene.itemAt(event.scenePos(), QtGui.QTransform())
                if isinstance(item, QtWidgets.QGraphicsPixmapItem):
                    # map the scene position to item coordinates
                    map = item.mapFromScene(event.scenePos())
                    # print(f'mouse is on pixmap at coordinates {map.x()}, {map.y()}')
                    geocoo = self.pix_to_geo(map.x(), map.y())
                    # print(f'mouse is on pixmap at coordinates {geocoo}')
                    self.pic_base.setPos(map.x() - self.pic_size_2, map.y() - self.pic_size_2)

        return super().eventFilter(source, event)

    def move_sat_to(self, lon, lat):
        satx, saty = self.geo_to_pix(lon, lat)
        satx -= self.pic_size_2
        saty -= self.pic_size_2
        self.pic_sat.setPos(satx, saty)

    def geo_to_pix(self, lon, lat):
        y = lon * self.ppgh
        y = self.ymid + self.y0 - y
        x = lat * self.ppgw
        x = self.xsq0 + x
        print(x, y)
        return x, y

    def pix_to_geo(self, x, y):
        # print(f'pixmap at coordinates x:{x} y:{y}')
        y = y - self.y0
        lat = 90 - (y / self.ppgh)
        lon = (x - self.xsq0) / self.ppgw
        return lat, lon

    def reset_view(self, scale=1):
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
            self.zoom_value = zoom
            if self.zoom_value > 0:
                if step > 0:
                    factor = self.SCALE_FACTOR ** step
                else:
                    factor = 1 / self.SCALE_FACTOR ** abs(step)
                self.scale(factor, factor)
            else:
                self.reset_view()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.zoom(delta and delta // abs(delta))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reset_view()

class com_center_widget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(QtWidgets.QLabel("ЦС"))
        main_layout.addWidget(QtWidgets.QLabel("LAT"))
        main_layout.addWidget(QtWidgets.QLabel("LON"))
        self.setLayout(main_layout)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.g_viewer = MainGraphicView()
        window_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout()
        list_layout = QtWidgets.QVBoxLayout()
        big_layout = QtWidgets.QVBoxLayout()
        info_layout = QtWidgets.QHBoxLayout()
        mgv_layout = QtWidgets.QHBoxLayout()

        info_layout.addWidget(com_center_widget())
        info_layout.addWidget(QtWidgets.QLabel("КА"))
        mgv_layout.addWidget(self.g_viewer)
        big_layout.addLayout(mgv_layout)
        big_layout.addLayout(info_layout)

        list_layout.addWidget(QtWidgets.QLabel("Список сеансов"))
        main_layout.addLayout(big_layout)
        main_layout.addLayout(list_layout)
        window_widget.setLayout(main_layout)

        self.setCentralWidget(window_widget)

        self.sat_show()


    def sat_show(self):
        coords = self.get_satellite_coordinates()
        self.g_viewer.move_sat_to(coords[0], coords[1])
        coords = self.get_satellite_path_coordinates()
        r_sat = 255
        g_sat = 0
        b_sat = 0
        step = 2
        for i in coords:
            if b_sat >= 255:
                b_sat = 255
                r_sat -= step
                if r_sat <= 0:
                    r_sat = 0
                    g_sat += step
                    if g_sat >= 255:
                        g_sat = 255
            else:
                b_sat += step
            self.g_viewer.draw_dot_by_geo(i[0], i[1],QtGui.QColor(r_sat, g_sat, b_sat))


    def get_satellite_coordinates(self, number=57191):
        ts = load.timescale()
        t = ts.now()

        stations_url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
        satellites = load.tle_file(stations_url)
        print('Loaded', len(satellites), 'satellites')
        by_number = {sat.model.satnum: sat for sat in satellites}
        satellite = by_number[number]
        # by_name = {sat.name: sat for sat in satellites}
        # satellite = by_name['POLYTECH-UNIVERSE 3 (R*)']

        geocentric = satellite.at(t)
        lat_satellite, lon_satellite = wgs84.latlon_of(geocentric)
        return lat_satellite.degrees, lon_satellite.degrees

    def get_satellite_path_coordinates(self, number=57191):
        ts = load.timescale()
        t1 = ts.now()
        # t1 = t + timedelta(minutes=5)
        stations_url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
        satellites = load.tle_file(stations_url)
        print('Loaded', len(satellites), 'satellites')
        by_number = {sat.model.satnum: sat for sat in satellites}
        satellite = by_number[number]
        # by_name = {sat.name: sat for sat in satellites}
        # satellite = by_name['POLYTECH-UNIVERSE 3 (R*)']
        clist = []
        for i in range(300):
            t1 += timedelta(minutes=1)
            geocentric = satellite.at(t1)
            lat_satellite, lon_satellite = wgs84.latlon_of(geocentric)
            clist.append([lat_satellite.degrees, lon_satellite.degrees])
        return clist

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    app.exec()
