import sys

from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtGui import QDoubleValidator
from skyfield.api import load
from skyfield.toposlib import wgs84
from datetime import timedelta
from pytz import timezone
from skyfield.units import Angle


class MainGraphicView(QtWidgets.QGraphicsView):
    base_coords_out_signal = QtCore.pyqtSignal(float, float)

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
        self.reset_view(int(self.SCALE_FACTOR ** self.zoom_value))
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
        self.x180 = 2446
        self.pix_height = self.y1 - self.y0
        self.ppgh = self.pix_height / 180
        self.width = self.x1 - self.x0
        self.ppgw = (self.xsq1 - self.xsq0) / 30

        self.pic_size = 60
        self.pic_size_2 = self.pic_size // 2
        self.pic_sat = QtWidgets.QGraphicsPixmapItem()
        self.pic_sat.setPixmap(QtGui.QPixmap('sat.png').scaled(self.pic_size, self.pic_size))
        # self.pic_sat.setPixmap(QtGui.QPixmap('sat.png').scaled(self.pic_size, self.pic_size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        self.scene.addItem(self.pic_sat)
        self.pic_base = QtWidgets.QGraphicsPixmapItem()
        self.pic_base.setPixmap(QtGui.QPixmap('base.png').scaled(self.pic_size, self.pic_size, ))
        self.scene.addItem(self.pic_base)

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
                    self.base_coords_out_signal.emit(geocoo[0], geocoo[1])
                    # print(f'mouse is on pixmap at coordinates {geocoo}')
                    self.pic_base.setPos(map.x() - self.pic_size_2, map.y() - self.pic_size_2)

        return super().eventFilter(source, event)

    def move_base_to(self, lat, lon):
        self.pic_base.setPos(lat - self.pic_size_2, lon - self.pic_size_2)

    def move_sat_to(self, lat, lon):
        satx, saty = self.geo_to_pix(lat, lon)
        satx -= self.pic_size_2
        saty -= self.pic_size_2
        self.pic_sat.setPos(satx, saty)

    def geo_to_pix(self, lat, lon):
        y = lat * self.ppgh
        y = self.ymid + self.y0 - y
        x = lon * self.ppgw
        x = self.xsq0 + x
        if x < self.x0:
            # print(x, y)
            # self.scene.addEllipse(x, y, 10, 10)
            x = (180 + lon) * self.ppgw
            x = self.x180 + x
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


class ComCenterWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.lat = ''
        self.lon = ''
        main_layout = QtWidgets.QVBoxLayout()
        title_label = QtWidgets.QLabel("Наземный Пункт Управления")

        lat_layout = QtWidgets.QHBoxLayout()
        self.lat_label = QtWidgets.QLabel("LAT: ")
        self.lat_title_hms_label = QtWidgets.QLabel("HMS: ")
        self.lat_line_edit = QtWidgets.QLineEdit(self.lat)
        lat_validator = QDoubleValidator(-90, 90, 15)
        lat_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        lat_validator.setLocale(QtCore.QLocale("en_US"))
        self.lat_line_edit.setValidator(lat_validator)
        self.lat_hms_label = QtWidgets.QLabel(f"{self.lat}")

        lon_layout = QtWidgets.QHBoxLayout()
        self.lon_label = QtWidgets.QLabel("LON: ")
        self.lon_title_hms_label = QtWidgets.QLabel("HMS: ")
        self.lon_line_edit = QtWidgets.QLineEdit(self.lon)
        lon_validator = QDoubleValidator(-180, 180, 15)
        lon_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        lon_validator.setLocale(QtCore.QLocale("en_US"))
        self.lon_line_edit.setValidator(lon_validator)
        self.lon_hms_label = QtWidgets.QLabel(f"{self.lon}")

        main_layout.addWidget(title_label)

        main_layout.addLayout(lat_layout)
        lat_layout.addWidget(self.lat_label)
        lat_layout.addWidget(self.lat_line_edit)
        lat_layout.addWidget(self.lat_title_hms_label)
        lat_layout.addWidget(self.lat_hms_label)

        main_layout.addLayout(lon_layout)
        lon_layout.addWidget(self.lon_label)
        lon_layout.addWidget(self.lon_line_edit)
        lon_layout.addWidget(self.lon_title_hms_label)
        lon_layout.addWidget(self.lon_hms_label)

        self.setLayout(main_layout)


    def show_coords(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.lat_line_edit.setText(f'{lat}')
        self.lat_hms_label.setText(f'{Angle(degrees= lat)}')
        self.lon_line_edit.setText(f'{lon}')
        self.lon_hms_label.setText(f'{Angle(degrees= lon)}')

    def get_coords(self):
        return self.lat, self.lon


class ParametersWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QtWidgets.QVBoxLayout()

        title_label = QtWidgets.QLabel("Параметры сеанса связи")

        time_layout = QtWidgets.QHBoxLayout()
        self.time_line = QtWidgets.QLineEdit()
        self.time_line.setInputMask("999")
        self.time_line.setText("7")
        self.time_label = QtWidgets.QLabel("Дни: ")
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.time_line)

        degree_layout = QtWidgets.QHBoxLayout()
        self.degree_line = QtWidgets.QLineEdit()
        self.degree_line.setInputMask("99")
        self.degree_line.setText("30")
        self.degree_label = QtWidgets.QLabel("Минимальный угол места, град: ")
        degree_layout.addWidget(self.degree_label)
        degree_layout.addWidget(self.degree_line)

        self.start_button = QtWidgets.QPushButton("Рассчитать")

        main_layout.addWidget(title_label)
        main_layout.addLayout(time_layout)
        main_layout.addLayout(degree_layout)
        main_layout.addWidget(self.start_button)

        self.setLayout(main_layout)


class ListWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QtWidgets.QVBoxLayout()
        title_label = QtWidgets.QLabel("Список сеансов")
        self.sessions_list = QtWidgets.QListWidget()
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.sessions_list)
        # self.sessions_list.addItem("ITEM")
        self.setLayout(main_layout)


class SpacecraftWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QtWidgets.QVBoxLayout()
        title_label = QtWidgets.QLabel("Космический аппарат")

        lat_layout = QtWidgets.QHBoxLayout()
        lat_deg_label = QtWidgets.QHBoxLayout()
        lat_hms_label = QtWidgets.QHBoxLayout()
        self.lat_deg_label = QtWidgets.QLabel("LAT: ")
        self.lat_hms_label = QtWidgets.QLabel("HMS: ")

        lon_layout = QtWidgets.QHBoxLayout()
        self.lon_deg_label = QtWidgets.QLabel("LON: ")
        self.lon_hms_label = QtWidgets.QLabel("HMS: ")


        main_layout.addWidget(title_label)

        main_layout.addLayout(lat_layout)
        lat_layout.addWidget(self.lat_deg_label)
        lat_layout.addWidget(self.lat_hms_label)

        main_layout.addLayout(lon_layout)
        lon_layout.addWidget(self.lon_deg_label)
        lon_layout.addWidget(self.lon_hms_label)
        self.setLayout(main_layout)

    def show_coords(self, lat, lon):
        self.lat_deg_label.setText("LAT: " + f'{lat}')
        self.lat_hms_label.setText("HMS: " + f'{Angle(degrees= lat)}')
        self.lon_deg_label.setText("LON: " + f'{lon}')
        self.lon_hms_label.setText("HMS: " + f'{Angle(degrees= lon)}')



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Школа 619")
        self.satellite = None
        self.time = None
        self.g_viewer = MainGraphicView()
        self.g_viewer.base_coords_out_signal.connect(self.base_coords_handler)
        self.com_center_w = ComCenterWidget()
        self.spacecraft_w = SpacecraftWidget()
        self.parameters_w = ParametersWidget()
        self.parameters_w.start_button.clicked.connect(self.start_button_clicked)
        self.com_center_w.lat_line_edit.editingFinished.connect(self.base_show)
        self.com_center_w.lon_line_edit.editingFinished.connect(self.base_show)
        self.list_w = ListWidget()
        window_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout()
        list_layout = QtWidgets.QVBoxLayout()
        big_layout = QtWidgets.QVBoxLayout()
        info_layout = QtWidgets.QHBoxLayout()
        mgv_layout = QtWidgets.QHBoxLayout()

        info_layout.addWidget(self.com_center_w, 1)
        info_layout.addWidget(self.spacecraft_w, 1)
        info_layout.addWidget(self.parameters_w, 1)
        mgv_layout.addWidget(self.g_viewer)
        big_layout.addLayout(mgv_layout)
        big_layout.addLayout(info_layout)

        list_layout.addWidget(self.list_w)
        main_layout.addLayout(big_layout, 3)
        main_layout.addLayout(list_layout, 1)
        window_widget.setLayout(main_layout)

        self.setCentralWidget(window_widget)

        self.sat_show()

    @QtCore.pyqtSlot()
    def start_button_clicked(self):
        if self.com_center_w.lat == None:
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowTitle("Расположите Наземеного Пункта Связи")
            dlg.exec()
        elif self.parameters_w.time_line.text() == '' \
                or self.parameters_w.degree_line.text() == '':
                dlg = QtWidgets.QDialog(self)
                dlg.setWindowTitle("Дни и Градусы")
                dlg.exec()
        else:
            td = int(self.parameters_w.time_line.text())
            degrees = int(self.parameters_w.degree_line.text())
            t0 = self.time
            t1 = self.time + timedelta(days=td)
            stp = wgs84.latlon(self.com_center_w.lat, self.com_center_w.lon)
            dif = self.satellite - stp
            te, ev = self.satellite.find_events(stp, t0, t1, altitude_degrees=degrees)
            start_t, finish_t, top = None, None, None
            for ti, event in zip(te, ev):
                if event == 0:
                    start_t = ti.astimezone(timezone('Europe/Moscow'))
                    start_t_str = start_t.strftime('%H:%M:%S')
                if event == 1:
                    peak_t = ti.astimezone(timezone('Europe/Moscow')).strftime('%Y %b %d %H:%M:%S')
                    top = dif.at(ti)
                if event == 2:
                    finish_t = ti.astimezone(timezone('Europe/Moscow'))
                    finish_t_str = finish_t.strftime('%H:%M:%S')
                    alt, az, dist = top.altaz()
                    dif_t_str = (finish_t - start_t)
                    #        alt, az = alt.degrees, az.degrees
                    str = (f'Время (UTC+3): {peak_t}\n'
                           f'\tАзимут:\t{az}\n'
                           f'\tМаксимальный угол места:\t{alt}\n'                           
                           f'\tНачало:\t{start_t_str}\n'
                           f'\tКонец:\t{finish_t_str}\n'
                           f'\tДлит.:\t{dif_t_str}')
                    # print(str)
                    self.list_w.sessions_list.addItem(str)


    def base_coords_handler(self, lat, lon):
        self.com_center_w.show_coords(lat, lon)
        # print(lat, lon)

    def base_show(self):
        if self.com_center_w.lat_line_edit.text() == '':
            lat = 0
        else:
            lat = float(self.com_center_w.lat_line_edit.text())
        if self.com_center_w.lon_line_edit.text() == '':
            lon = 0
        else:
            lon = float(self.com_center_w.lon_line_edit.text())
        pix_lat, pix_lon = self.g_viewer.geo_to_pix(lat, lon)
        print(pix_lat, pix_lon)
        self.g_viewer.move_base_to(pix_lat, pix_lon)


    def sat_show(self):
        coords = self.get_satellite_coordinates()
        self.spacecraft_w.show_coords(coords[0], coords[1])
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
                if b_sat >= 255:
                    b_sat = 255
            self.g_viewer.draw_dot_by_geo(i[0], i[1], QtGui.QColor(r_sat, g_sat, b_sat))


    def get_satellite_coordinates(self, number=57191):
        ts = load.timescale()
        t = ts.now()
        self.time = t
        satellites_url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
        satellites = load.tle_file(satellites_url)
        # print('Loaded', len(satellites), 'satellites')
        by_number = {sat.model.satnum: sat for sat in satellites}
        satellite = by_number[number]
        # by_name = {sat.name: sat for sat in satellites}
        # satellite = by_name['POLYTECH-UNIVERSE 3 (R*)']
        self.satellite = satellite
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
    window.showMaximized()
    app.exec()
