import sys
import os
import time
import numpy as np
from functools import partial
import datetime
import pyqtgraph as pg
import pyqtgraph.exporters
from MainScreenThread import Thread
from PlaybackScreenThread import ScrollThread
from LiveRecordThread import LiveRecord
from findDevices import OAK_USB_Devices, Webcam_Devices, Load_Device_Thread
from PySide6.QtCore import Qt, QThread, Signal, Slot,QAbstractTableModel, QPoint, QRect, QSize, QTimer,QPointF
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QScreen, QPainter, QFontMetrics, QIcon, QCursor, QPalette, QBrush, QColor, QPen, QTransform
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget,QTableView,QTableWidget,
                               QScrollArea,QFrame, QTableWidgetItem,QProgressDialog,QRubberBand,QAbstractItemView, QStyle, QSlider, QToolBar, QFileDialog,QMessageBox, QDockWidget, QToolTip, QGraphicsScene,QGraphicsView,QGraphicsPixmapItem, QSizeGrip)


class EdgeWindow(QMainWindow):
    def __init__(self):
        super(EdgeWindow, self).__init__()
        self.setWindowTitle("Edge Tool Settings")
        self.setFixedWidth(300)
        self.setFixedHeight(500)

        