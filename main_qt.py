import sys

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QIntValidator
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtGui import QDoubleValidator
from skyfield.api import load
from skyfield.toposlib import wgs84
from datetime import timedelta
from pytz import timezone
from skyfield.units import Angle
from random import randint

def isfloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class MainGraphicView(QtWidgets.QGraphicsView):
    base_coords_out_signal = QtCore.pyqtSignal(float, float)
    base_change_signal = QtCore.pyqtSignal(int)

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

        self.start_lon = 30.31410
        self.start_lat = 59.93860

        self.pic_size = 60
        self.pic_size_2 = self.pic_size // 2
        self.pic_sat = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap('sat.png').scaled(self.pic_size, self.pic_size))
        # self.pic_sat.setPixmap(QtGui.QPixmap('sat.png').scaled(self.pic_size, self.pic_size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation))
        self.scene.addItem(self.pic_sat)
        self.pic_base = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap('base.png').scaled(self.pic_size, self.pic_size, ))
        # x, y = self.geo_to_pix(self.start_y, self.start_x)

        self.color_base_list = []
        self.pic_base_list = []
        self.index = 0
        self.add_base(randint(0, 255), randint(0, 255), randint(0, 255))

        self.scene.installEventFilter(self)
        self.setMouseTracking(True)

        self.list_dots = []

    def change_color(self, r: int, g: int, b: int):
        new_color = self.color_base_list[self.index]
        new_color.setColor(QtGui.QColor(r, g, b))
        self.color_base_list[self.index] = new_color

    def change_index(self, number):
        self.index = number

    def add_base(self, r: int, g: int, b: int):
        new_pic_base = self.pic_base.pixmap()
        self.pic_base_list.append(QtWidgets.QGraphicsPixmapItem(new_pic_base))
        self.index = len(self.pic_base_list) -1
        new_color = QtWidgets.QGraphicsColorizeEffect()
        new_color.setStrength(1.0)
        new_color.setColor(QtGui.QColor(r, g, b))
        self.color_base_list.append(new_color)
        self.pic_base_list[self.index].setGraphicsEffect(new_color)
        self.scene.addItem(self.pic_base_list[self.index])

    def del_base(self):
        self.scene.removeItem(self.pic_base_list[self.index])
        self.color_base_list.pop(self.index)
        self.pic_base_list.pop(self.index)

    def draw_dot_by_geo(self, lat, lon, color=QtGui.QColor('black'), size=5):
        pen = QtGui.QPen(color)
        brush = QtGui.QBrush()
        brush.setColor(color)
        brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
        x, y = self.geo_to_pix(lat, lon)
        self.list_dots.append(self.scene.addEllipse(x, y, size, size, pen, brush))

    def clear_dots(self):
        for i in self.list_dots:
            self.scene.removeItem(i)
        self.list_dots = []

    def eventFilter(self, source, event):
        if len(self.pic_base_list) != 0:
            if event.type() == QtCore.QEvent.Type.GraphicsSceneMousePress:
                item = self.scene.itemAt(event.scenePos(), QtGui.QTransform())
                if event.button() == QtCore.Qt.MouseButton.RightButton:
                    if isinstance(item, QtWidgets.QGraphicsPixmapItem) and (item == self.img or item == self.pic_base_list[self.index]):
                        # map_coords the scene position to item coordinates
                        map_coords = item.mapFromScene(event.scenePos())
                        if item == self.pic_base_list[self.index]:
                            gcoo = self.geo_to_pix(self.start_lat, self.start_lon)
                            map_coords = QPointF(gcoo[0], gcoo[1])
                        # print(f'mouse is on pixmap at coordinates {map_coords.x()}, {map_coords.y()}')
                        geocoo = self.pix_to_geo(map_coords.x(), map_coords.y())
                        self.base_coords_out_signal.emit(geocoo[0], geocoo[1])
                        # print(f'mouse is on pixmap at coordinates {geocoo}')
                        self.move_base_to(map_coords.x(), map_coords.y())
                if event.button() == QtCore.Qt.MouseButton.LeftButton:
                    if isinstance(item, QtWidgets.QGraphicsPixmapItem) and item != self.img:
                        index = self.pic_base_list.index(item)
                        self.change_index(index)
                        self.base_change_signal.emit(index)
        return super().eventFilter(source, event)

    def move_base_to(self, lat: float, lon: float):
        self.pic_base_list[self.index].setPos(lat - self.pic_size_2, lon - self.pic_size_2)

    def move_sat_to(self, lat: float, lon: float):
        satx, saty = self.geo_to_pix(lat, lon)
        satx -= self.pic_size_2
        saty -= self.pic_size_2
        self.pic_sat.setPos(satx, saty)

    def geo_to_pix(self, lat: float, lon: float):
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

    def pix_to_geo(self, x: int, y: int):
        # print(f'pixmap at coordinates x:{x} y:{y}')
        y = y - self.y0
        lat = 90 - (y / self.ppgh)
        lon = (x - self.xsq0) / self.ppgw
        return lat, lon

    def reset_view(self, scale = 1):
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
    def __init__(self, start_lon: float, start_lat: float):
        super().__init__()
        self.lat = float(start_lat)
        self.lon = float(start_lon)
        lat_dms = Angle(degrees=self.lat)
        lon_dms = Angle(degrees=self.lon)
        self.base_list = [[self.lat, self.lon]]

        main_layout = QtWidgets.QVBoxLayout()
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("Наземный Пункт Управления:")
        button_layout = QtWidgets.QHBoxLayout()
        self.base_box = QtWidgets.QComboBox()
        self.base_box.addItem("НПУ")
        self.color_base = QtWidgets.QPushButton()
        self.color_base.setStyleSheet(f"background-color: rgb({0, 0, 0});")
        self.add_button = QtWidgets.QPushButton("Добавить")
        self.delete_button = QtWidgets.QPushButton("Удалить")
        self.color_button = QtWidgets.QPushButton("Цвет")
        self.base_box.setEditable(True)
        self.base_box.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self.base_box.completer().setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)

        lat_layout = QtWidgets.QHBoxLayout()
        lat_deg_layout = QtWidgets.QHBoxLayout()
        lat_label = QtWidgets.QLabel("LAT: ")
        self.lat_line = QtWidgets.QLineEdit(f"{self.lat}")
        self.lat_deg_label = QtWidgets.QLabel(f"            {lat_dms}")
        lon_layout = QtWidgets.QHBoxLayout()
        lon_deg_layout = QtWidgets.QHBoxLayout()
        lon_label = QtWidgets.QLabel("LON: ")
        self.lon_line = QtWidgets.QLineEdit(f"{self.lon}")
        self.lon_deg_label = QtWidgets.QLabel(f"            {lon_dms}")

        lat_validator = QDoubleValidator(-99.99999, 99.99999, 5)
        lat_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        lat_validator.setLocale(QtCore.QLocale("en_US"))
        self.lat_line.setValidator(lat_validator)
        lon_validator = QDoubleValidator(-999.99999, 999.99999, 5)
        lon_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        lon_validator.setLocale(QtCore.QLocale("en_US"))
        self.lon_line.setValidator(lon_validator)

        main_layout.addLayout(title_layout)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(lat_layout)
        main_layout.addLayout(lat_deg_layout)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.base_box)
        title_layout.addWidget(self.color_base)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.color_button)
        lat_layout.addWidget(lat_label)
        lat_layout.addWidget(self.lat_line)
        lat_deg_layout.addWidget(self.lat_deg_label)
        main_layout.addLayout(lon_layout)
        main_layout.addLayout(lon_deg_layout)
        lon_layout.addWidget(lon_label)
        lon_layout.addWidget(self.lon_line)
        lon_deg_layout.addWidget(self.lon_deg_label)

        self.setLayout(main_layout)

    def change_color(self, r: int = 0, g: int = 0, b: int = 0):
        self.color_base.setStyleSheet(f"background-color: rgb({r}, {g}, {b});")

    def show_coords(self, lat: float, lon: float):
        self.base_list[self.base_box.currentIndex()] = [lat, lon]
        self.lat = f'{lat:.5f}'
        lat_deg = str(Angle(degrees=float(self.lat)))
        self.lon = f"{lon:.5f}"
        lon_deg = str(Angle(degrees= float(self.lon)))
        self.lat_line.setText(f"{self.lat.rstrip("0").rstrip(".")}")
        if lat < 0:
            self.lat_deg_label.setText(f"S        {lat_deg}")
        else:
            self.lat_deg_label.setText(f"N        {lat_deg}")
        self.lon_line.setText(f'{self.lon.rstrip("0").rstrip(".")}')
        if lon < 0:
            self.lon_deg_label.setText(f"W        {lon_deg}")
        else:
            self.lon_deg_label.setText(f"E        {lon_deg}")

    def get_coords(self):
        return self.lat, self.lon

    def remove_index(self, index):
        self.base_box.removeItem(index)

    def change_index(self, index):
        self.base_box.setCurrentIndex(index)

class ColorWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Цвет")
        color_layout = QtWidgets.QVBoxLayout()
        random_layout = QtWidgets.QHBoxLayout()
        red_layout = QtWidgets.QHBoxLayout()
        green_layout = QtWidgets.QHBoxLayout()
        blue_layout = QtWidgets.QHBoxLayout()
        red_label = QtWidgets.QLabel("r: ")
        green_label = QtWidgets.QLabel("g: ")
        blue_label = QtWidgets.QLabel("b: ")
        random_label = QtWidgets.QLabel("Случайно: ")
        self.finish_button = QtWidgets.QPushButton("Изменить")
        self.random_check = QtWidgets.QCheckBox()
        self.random_check.setCheckState(QtCore.Qt.CheckState.Checked)
        self.red_line = QtWidgets.QLineEdit("0")
        self.green_line = QtWidgets.QLineEdit("0")
        self.blue_line = QtWidgets.QLineEdit("0")

        color_line_validator = QIntValidator(0, 255)
        self.red_line.setValidator(color_line_validator)
        self.green_line.setValidator(color_line_validator)
        self.blue_line.setValidator(color_line_validator)

        color_layout.addLayout(red_layout)
        color_layout.addLayout(green_layout)
        color_layout.addLayout(blue_layout)
        color_layout.addLayout(random_layout)
        color_layout.addWidget(self.finish_button)
        red_layout.addWidget(red_label)
        red_layout.addWidget(self.red_line)
        green_layout.addWidget(green_label)
        green_layout.addWidget(self.green_line)
        blue_layout.addWidget(blue_label)
        blue_layout.addWidget(self.blue_line)
        random_layout.addWidget(random_label)
        random_layout.addWidget(self.random_check)

        self.setLayout(color_layout)

class ParametersWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QtWidgets.QVBoxLayout()
        button_layaot = QtWidgets.QHBoxLayout()

        title_label = QtWidgets.QLabel("Параметры сеанса связи")

        time_layout = QtWidgets.QHBoxLayout()
        self.time_line = QtWidgets.QLineEdit()
        time_line_validator = QIntValidator(0, 999)
        self.time_line.setText("7")
        self.time_line.setValidator(time_line_validator)
        self.time_label = QtWidgets.QLabel("Дни: ")
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.time_line)

        degree_layout = QtWidgets.QHBoxLayout()
        degree_line_validator = QDoubleValidator(0, 90, 2)
        degree_line_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        degree_line_validator.setLocale(QtCore.QLocale("en_US"))
        self.degree_line = QtWidgets.QLineEdit()
        self.degree_line.setText("30")
        self.degree_line.setValidator(degree_line_validator)
        self.degree_label = QtWidgets.QLabel("Минимальный угол места, град: ")
        degree_layout.addWidget(self.degree_label)
        degree_layout.addWidget(self.degree_line)

        self.start_button = QtWidgets.QPushButton("Рассчитать")
        self.clear_button = QtWidgets.QPushButton("Очистить")

        main_layout.addWidget(title_label)
        main_layout.addLayout(time_layout)
        main_layout.addLayout(degree_layout)
        main_layout.addLayout(button_layaot)
        button_layaot.addWidget(self.start_button)
        button_layaot.addWidget(self.clear_button)

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
        title_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("Космический аппарат")

        satellites_url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
        self.satellites_file = load.tle_file(satellites_url)
        with open('gp.php') as gp:
            lines = gp.readlines()
            self.satellites = []
            for i in range(0, len(lines), 3):
                self.satellites.append(lines[i].strip('\n').strip())
        self.satellites_box = QtWidgets.QComboBox()
        self.satellites.sort()
        self.satellites_box.addItems(self.satellites)
        self.satellites_box.setCurrentText('POLYTECH-UNIVERSE 3 (R*)')
        self.satellites_box.setEditable(True)
        self.satellites_box.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self.satellites_box.completer().setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
        self.button_update = QtWidgets.QPushButton('Обновить')

        self.lat_label = QtWidgets.QLabel("LAT: ")
        self.lat_deg_label = QtWidgets.QLabel("          ")
        self.lon_label = QtWidgets.QLabel("LON: ")
        self.lon_deg_label = QtWidgets.QLabel("          ")

        main_layout.addLayout(title_layout)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.satellites_box)
        title_layout.addWidget(self.button_update)
        main_layout.addWidget(self.lat_label)
        main_layout.addWidget(self.lat_deg_label)
        main_layout.addWidget(self.lon_label)
        main_layout.addWidget(self.lon_deg_label)
        self.setLayout(main_layout)

    def show_coords(self, lat, lon):
        lat = f'{lat:.5f}'
        lon = f'{lon:.5f}'
        self.lat_label.setText("LAT: " + f'{lat.rstrip("0").rstrip(".")}')
        self.lon_label.setText("LON: " + f'{lon.rstrip("0").rstrip(".")}')
        if float(lat) < 0:
            self.lat_deg_label.setText("S       " + f'{Angle(degrees= float(lat))}')
        else:
            self.lat_deg_label.setText("N       " + f'{Angle(degrees= float(lat))}')
        if float(lon) < 0:
            self.lon_deg_label.setText("W       " + f'{Angle(degrees= float(lon))}')
        else:
            self.lon_deg_label.setText("E       " + f'{Angle(degrees= float(lon))}')




class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Школа 619")
        self.satellite = None
        self.time = None
        self.g_viewer = MainGraphicView()
        self.g_viewer.base_coords_out_signal.connect(self.base_coords_handler)
        self.g_viewer.base_change_signal.connect(self.base_change_handler)
        self.com_center_w = ComCenterWidget(self.g_viewer.start_lon, self.g_viewer.start_lat)
        self.spacecraft_w = SpacecraftWidget()
        self.parameters_w = ParametersWidget()
        self.color_w = ColorWindow()
        self.com_center_w.base_box.currentIndexChanged.connect(self.change_base)
        self.com_center_w.add_button.clicked.connect(self.add_button_clicked)
        self.com_center_w.delete_button.clicked.connect(self.delete_button_clicked)
        self.com_center_w.color_button.clicked.connect(self.show_color_w)
        self.spacecraft_w.satellites_box.textActivated.connect(self.sat_show)
        self.spacecraft_w.button_update.clicked.connect(self.sat_show)
        self.parameters_w.start_button.clicked.connect(self.start_button_clicked)
        self.parameters_w.clear_button.clicked.connect(self.clear_button_clicked)
        self.com_center_w.lat_line.editingFinished.connect(self.base_show)
        self.com_center_w.lon_line.editingFinished.connect(self.base_show)
        self.color_w.finish_button.clicked.connect(self.color_change)
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

        self.color_change()
        self.setCentralWidget(window_widget)
        self.base_show()
        self.sat_show()

    @QtCore.pyqtSlot()
    def start_button_clicked(self):
        error = []
        peak_t = None
        start_t_str = None
        if len(self.g_viewer.pic_base_list) == 0:
            error.append("Нет спутника")
        for i in range(len(self.com_center_w.base_list)):
            if not isfloat(self.com_center_w.base_list[i][0]):
                error.append("Широта наземного пункта связи")
            if not isfloat(self.com_center_w.base_list[i][1]):
                error.append("Долгота наземного пункта связи")
            if not self.parameters_w.time_line.text().isnumeric():
                error.append("Дни сеанса связи")
            if not isfloat(self.parameters_w.degree_line.text()):
                error.append("Минимальный угол")
            elif float(self.parameters_w.degree_line.text()) > 90:
                error.append("Минимальный угол")
            if len(error) == 0:
                td = int(self.parameters_w.time_line.text())
                degrees = float(self.parameters_w.degree_line.text())
                t0 = self.time
                t1 = self.time + timedelta(days=td)
                stp = wgs84.latlon(self.com_center_w.base_list[i][0], self.com_center_w.base_list[i][1])
                dif = self.satellite - stp
                te, ev = self.satellite.find_events(stp, t0, t1, altitude_degrees=degrees)
                start_t, finish_t, top = None, None, None
                no_events = True
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
                        text = (f'НПУ: {self.com_center_w.base_box.itemText(i)}\n'
                                f'\tВремя (UTC+3): {peak_t}\n'
                                f'\tАзимут:\t{az}\n'
                                f'\tМаксимальный угол места:\t{alt}\n'                           
                                f'\tНачало:\t{start_t_str}\n'
                                f'\tКонец:\t{finish_t_str}\n'
                                f'\tДлит.:\t{dif_t_str}')
                        # print(str)
                        self.list_w.sessions_list.addItem(text)
                        no_events = False
                if no_events:
                    self.list_w.sessions_list.addItem("Не найдено сеансов связи")

        if len(error) > 0:
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowTitle("Ошибка")
            main_layout = QtWidgets.QVBoxLayout()
            label = QtWidgets.QLabel("Ошибки:")
            main_layout.addWidget(label)
            for i in range(len(error)):
                label_error = QtWidgets.QLabel(f"{error[i]}")
                main_layout.addWidget(label_error)
            dlg.setLayout(main_layout)
            dlg.exec()

    def add_button_clicked(self):
        if self.com_center_w.base_box.findText(self.com_center_w.base_box.currentText()) == -1:
            self.g_viewer.add_base(randint(0, 255), randint(0, 255), randint(0, 255))
            self.color_change()
            self.com_center_w.base_box.addItem(self.com_center_w.base_box.currentText())
            self.com_center_w.base_list.append([self.g_viewer.start_lat, self.g_viewer.start_lon])
            self.com_center_w.change_index(self.g_viewer.index)
            lat = self.g_viewer.start_lat
            lon = self.g_viewer.start_lon
            pix_lat, pix_lon = self.g_viewer.geo_to_pix(lat, lon)
            self.com_center_w.show_coords(lat, lon)
            self.g_viewer.move_base_to(pix_lat, pix_lon)
        # else:
        #     self.com_center_w.com_box.addItem(f"{self.com_center_w.com_box.count()+1}")
        #     self.com_center_w.com_list.append(self.start_pos)
        #     lat = self.com_center_w.com_list[self.com_center_w.com_box.currentIndex()][0]
        #     lon = self.com_center_w.com_list[self.com_center_w.com_box.currentIndex()][1]
        #     pix_lat, pix_lon = self.g_viewer.geo_to_pix(lat, lon)
        #     self.com_center_w.show_coords(lat, lon)
        #     self.g_viewer.move_base_to(pix_lat, pix_lon)

    def delete_button_clicked(self):
        if len(self.g_viewer.pic_base_list) > 1:
            self.g_viewer.del_base()
            self.com_center_w.base_list.pop(self.g_viewer.index)
            self.com_center_w.remove_index(self.g_viewer.index)
            self.change_base()
            #I don't know how to allow the deletion of all НПУ so that the program does not crash. I succeeded once, but the change of НПУ after deletion did not work correctly.

    def change_base(self):
        if len(self.g_viewer.pic_base_list) == 0:
            lat = 0
            lon = 0
            self.com_center_w.change_color(0, 0, 0)
        else:
            self.g_viewer.change_index(self.com_center_w.base_box.currentIndex())
            lat = self.com_center_w.base_list[self.g_viewer.index][0]
            lon = self.com_center_w.base_list[self.g_viewer.index][1]
            pix_lat, pix_lon = self.g_viewer.geo_to_pix(lat, lon)
            self.g_viewer.move_base_to(pix_lat, pix_lon)
            self.change_rgb_base()
        self.com_center_w.show_coords(lat, lon)

    def show_color_w(self):
        self.color_w.show()

    def color_change(self):
        if self.color_w.random_check.checkState() == QtCore.Qt.CheckState.Checked:
            r = randint(0, 255)
            g = randint(0, 255)
            b = randint(0, 255)
        else:
            r = int(self.color_w.red_line.text())
            g = int(self.color_w.green_line.text())
            b = int(self.color_w.blue_line.text())
        self.g_viewer.change_color(r, g, b)
        self.change_rgb_base()

    def clear_button_clicked(self):
        self.list_w.sessions_list.clear()

    def base_coords_handler(self, lat: float = 0, lon: float = 0):
        if self.g_viewer.pic_base_list != 0:
            self.com_center_w.show_coords(lat, lon)
        #print(f" index: {self.g_viewer.index}\n pic_base_list: {self.g_viewer.pic_base_list}\n color_base_list: {self.g_viewer.color_base_list}\n index_box: {self.com_center_w.base_box.currentIndex()}\n coords_list: {self.com_center_w.base_list}")

    def get_rgb_base(self):
        r, g, b, a = self.g_viewer.color_base_list[self.g_viewer.index].color().getRgb()
        return r, g, b

    def change_rgb_base(self):
        r, g, b = self.get_rgb_base()
        self.color_w.red_line.setText(f"{r}")
        self.color_w.green_line.setText(f"{g}")
        self.color_w.blue_line.setText(f"{b}")
        self.com_center_w.change_color(r, g, b)

    def base_change_handler(self, index: int):
        self.com_center_w.base_box.setCurrentIndex(index)
        self.change_base()

    def base_show(self):
        if isfloat(self.com_center_w.lat_line.text()):
            lat = float(self.com_center_w.lat_line.text())
            if lat > 90:
                lat = 90
            if -90 > lat:
                lat = -90
        else:
            lat = 0
        if isfloat(self.com_center_w.lon_line.text()):
            lon = float(self.com_center_w.lon_line.text())
            if lon > 180:
                lon = 180
            if -180 > lon:
                lon = -180
        else:
            lon = 0

        self.com_center_w.base_list[self.g_viewer.index] = [lat, lon]
        pix_lat, pix_lon = self.g_viewer.geo_to_pix(lat, lon)
        # print(pix_lat, pix_lon)
        self.com_center_w.show_coords(lat, lon)
        self.g_viewer.move_base_to(pix_lat, pix_lon)

    def sat_show(self):
        satellite_id = self.spacecraft_w.satellites_box.currentText()
        coords = self.get_satellite_coordinates(satellite_id)
        self.spacecraft_w.show_coords(coords[0], coords[1])
        self.g_viewer.move_sat_to(coords[0], coords[1])
        coords = self.get_satellite_path_coordinates(satellite_id)
        self.g_viewer.clear_dots()
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


    def get_satellite_coordinates(self, name):
        ts = load.timescale()
        t = ts.now()
        self.time = t
        # by_number = {sat.model.satnum: sat for sat in satellites}
        # satellite = by_number[number]
        by_name = {sat.name: sat for sat in self.spacecraft_w.satellites_file}
        satellite = by_name[name]
        self.satellite = satellite
        geocentric = satellite.at(t)
        lat_satellite, lon_satellite = wgs84.latlon_of(geocentric)
        return lat_satellite.degrees, lon_satellite.degrees

    def get_satellite_path_coordinates(self, name):
        ts = load.timescale()
        t1 = ts.now()
        # by_number = {sat.model.satnum: sat for sat in satellites}
        # satellite = by_number[number]
        by_name = {sat.name: sat for sat in self.spacecraft_w.satellites_file}
        satellite = by_name[name]
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
