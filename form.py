from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import QgsGeometry, QgsWkbTypes
from qgis.gui import QgisInterface
import numpy as np
import matplotlib.pyplot
from matplotlib.patches import Polygon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from .models import Extent, Points

class dialog(QDialog):
    def __init__(self, iface:QgisInterface):
        super().__init__()
        self.extent = Extent()
        self.points = Points()
        self.iface = iface
        self.setWindowTitle("Random Points")

        # LAYERS COMBO BOX + CANVAS CHECK
        comboLayout = QHBoxLayout()
        comboLabel = QLabel("Active &layers")
        self.chooseCombo = QComboBox()
        self.chooseCombo.setMinimumWidth(100)
        comboLabel.setBuddy(self.chooseCombo)
        comboLayout.addWidget(comboLabel)
        comboLayout.addWidget(self.chooseCombo)
        comboLayout.addStretch()

        checkLabel = QLabel("Active &window")
        self.checkCanvas = QCheckBox()
        checkLabel.setBuddy(self.checkCanvas)
        comboLayout.addWidget(self.checkCanvas)
        comboLayout.addWidget(checkLabel)

        # LAYER FROM FILE
        fieldLayout = QHBoxLayout()
        fieldLabel = QLabel("&File from disc")
        self.chooseField = QLineEdit()
        chooseFiledButton = QPushButton("...")
        self.chooseField.setPlaceholderText("Choose file...")
        fieldLabel.setBuddy(self.chooseField)
        fieldLayout.addWidget(fieldLabel)
        fieldLayout.addWidget(self.chooseField)
        fieldLayout.addWidget(chooseFiledButton)

        # CURRENT EXTENT
        extentLayout = QHBoxLayout()
        extentLabel = QLabel("Current extent:")
        self.extentValues = QLineEdit()
        extentLabel.setBuddy(self.extentValues)
        #self.extentValues.setText("53.54857 17.423784 , 52.8372548 16.483264587")
        self.extentValues.setEnabled(False)
        extentLabel.setAlignment(Qt.AlignCenter)
        extentLayout.addWidget(extentLabel)
        extentLayout.addWidget(self.extentValues)

        # PARAMETERS OF SAMPLING
        self.npointsSpin = QSpinBox()
        self.npointsSpin.setRange(1, 2147483647)
        self.npointsSpin.setValue(100)
        self.npointsSpin.setWrapping(False)
        npointsLabel = QLabel("Number of &points")
        npointsLabel.setBuddy(self.npointsSpin)

        intValidator = QIntValidator(0, 10000)
        self.bufferField = QLineEdit()
        self.bufferField.setValidator(intValidator)
        bufferLabel = QLabel("Size of &Buffer")
        bufferLabel.setBuddy(self.bufferField)
        self.bufferField.setText("0")

        self.seedField = QLineEdit()
        self.seedField.setValidator(intValidator)
        seedLabel = QLabel("&Seed")
        seedLabel.setBuddy(self.seedField)
        self.seedField.setPlaceholderText("Random sample")
        self.seedField.setText("")

        self.plotButton = QPushButton("&Plot")

        # FIGURE CANVAS
        self.figure = matplotlib.pyplot.Figure(figsize = (6, 6))
        self.canvas = FigureCanvas(self.figure)

        # MERGING PLOT AND PARAMETERS
        self.leftLayout = QVBoxLayout()
        self.leftLayout.addWidget(npointsLabel)
        self.leftLayout.addWidget(self.npointsSpin)
        self.leftLayout.addWidget(bufferLabel)
        self.leftLayout.addWidget(self.bufferField)
        self.leftLayout.addWidget(seedLabel)
        self.leftLayout.addWidget(self.seedField)
        self.leftLayout.addWidget(self.plotButton)
        self.leftLayout.addStretch()

        plotLayout = QHBoxLayout()
        plotLayout.addWidget(self.canvas)
        plotLayout.addLayout(self.leftLayout)

        # OK AND CANCEL BUTTONS
        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        # FINAL LAYOUT
        mainLayout = QVBoxLayout()
        
        mainLayout.addLayout(comboLayout)
        mainLayout.addLayout(fieldLayout)
        mainLayout.addLayout(extentLayout)
        mainLayout.addLayout(plotLayout)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        # CONNECTIONS
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        chooseFiledButton.clicked.connect(self.chooseButton_clicked)
        self.chooseCombo.currentIndexChanged.connect(lambda: self.change("combo"))
        self.checkCanvas.stateChanged.connect(lambda: self.change("check"))
        self.iface.mapCanvas().extentsChanged.connect(lambda: self.change("check") if self.checkCanvas.isChecked() else None)
        self.plotButton.clicked.connect(self.plot)

    def plot_extent(self):
        """ Plot source of extent on figure for reference """
        shapes = self.extent.get_source()
        point_extent_added = False
        for shape in shapes:
            if shape.wkbType() == QgsWkbTypes.MultiPolygon:
                poly = shape.asMultiPolygon()[0][0]
                poly = Polygon(np.array(poly), facecolor='lightgrey')
                self.ax.add_patch(poly)
            elif shape.wkbType() == QgsWkbTypes.Polygon:
                poly = shape.asPolygon()[0]
                poly = Polygon(np.array(poly), facecolor='lightgrey')
                self.ax.add_patch(poly)
            elif shape.wkbType() == QgsWkbTypes.MultiLineString:
                line = shape.asMultiPolyline()[0]
                x_data = [p.x() for p in line]
                y_data = [p.y() for p in line]
                self.ax.plot(x_data, y_data, c='#222222')
            elif shape.wkbType() == QgsWkbTypes.LineString:
                line = shape.asPolyline()
                x_data = [p.x() for p in line]
                y_data = [p.y() for p in line]
                self.ax.plot(x_data, y_data, c='#222222')
            elif shape.wkbType() == QgsWkbTypes.Point:
                if not point_extent_added:
                    ext = QgsGeometry.fromRect(self.extent.get_extent())
                    poly = ext.asPolygon()[0]
                    poly = Polygon(np.array(poly), facecolor='lightgrey')
                    self.ax.add_patch(poly)
                    point_extent_added = True
                mp = shape.asPoint()
                self.ax.scatter(mp.x(), mp.y(), marker='x', c='#222222', s=20)

    def plot(self):
        """ Sample points from extent and plot them on figure """
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.points.sample_points_random(
            self.extent.get_extent(),
            int(self.bufferField.text()) if self.bufferField.text() != '' else 0,
            self.npointsSpin.value(),
            self.seedField.text()
        )
        self.plot_extent()
        points = self.points.get_points()
        self.ax.scatter(points["x"], points["y"], c='red', s=6)
        self.ax.tick_params(axis='x', labelsize=6)
        self.ax.tick_params(axis='y', labelsize=6)
        self.canvas.draw()

    def chooseButton_clicked(self):
        """ Open file dialog window after clicking the button"""
        fileName = QFileDialog.getOpenFileName(self, "File to take extend from", "", "All Files (*)")
        self.chooseField.setText(fileName[0])
        self.change("field")

    def set_extent(self):
        """ Show current extent in the GUI """
        self.extent_values = self.extent.get_extent()
        e = self.extent_values
        extent_values = f"{e.xMinimum()} {e.xMaximum()} {e.yMinimum()} {e.yMaximum()}"
        self.extentValues.setText(extent_values)

    def connect_to_extent(self, extent:Extent):
        """ Connect to Extent object """
        self.extent = extent
        self.extent.get_extent_from_canvas()
        self.set_extent()

    def connect_to_points(self, points:Points):
        """ Connect to Points object """
        self.points = points

    def change(self, what):
        """ Change state of layer combobox, file dialog window and canvas checkbox after clicking one of them """
        if what != "combo" and self.chooseCombo.currentIndex() != 0:
            self.chooseCombo.blockSignals(True)
            self.chooseCombo.setCurrentIndex(0)
            self.chooseCombo.blockSignals(False)
        if what != "field" and self.chooseField.text() != '':
            self.chooseField.clear()
        if what != "check" and self.checkCanvas.isChecked():
            self.checkCanvas.blockSignals(True)
            self.checkCanvas.setChecked(False)
            self.checkCanvas.blockSignals(False)

        if what == "combo": self.extent.get_extent_from_layer(self.chooseCombo.currentIndex())
        if what == "field": self.extent.get_extent_from_file(self.chooseField.text())
        if what == "check": self.extent.get_extent_from_canvas()

        self.set_extent()
