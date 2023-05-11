from qgis.gui import QgisInterface
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from . import resources
from .form import dialog
from .models import Extent, Points

class SamplingPlugin:
    def __init__(self, iface:QgisInterface):
        self.iface = iface
        self.dialog = dialog(iface)
        self.registry = QgsProject.instance()
        self.extent = Extent(iface)
        self.create_layer_list()
        self.points = Points(iface)
        self.registry.layersAdded.connect(self.create_layer_list)
        self.registry.layersRemoved.connect(self.create_layer_list)
        self.dialog.connect_to_extent(self.extent)
        self.dialog.connect_to_points(self.points)
    def initGui(self):
        self.action = QAction(QIcon(":/plugins/custom/icon.png"), "Random sampling plugin", self.iface.mainWindow())
        self.action.setStatusTip("sample points from extent")
        self.action.triggered.connect(self.run)    
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Home made", self.action)
    def unload(self):
        self.iface.removePluginMenu("&Home made", self.action)
        self.iface.removeToolBarIcon(self.action)
    def run(self):
        self.dialog.show()
        result = self.dialog.exec_()
        if result:
            self.create_point_file()
            #self.iface.messageBar().pushInfo("It works!", "I guess...")
        exit
    def create_layer_list(self):
        """ Create list of layers in combobox """
        self.dialog.chooseCombo.blockSignals(True)
        self.dialog.chooseCombo.clear()
        layer_list = list(self.registry.mapLayers().values())
        self.layers = layer_list
        self.extent.update_layers(layer_list)
        layer_list = [""] + [layer.name() for layer in layer_list]
        self.dialog.chooseCombo.addItems(layer_list)
        self.dialog.chooseCombo.blockSignals(False)
    def prepare_points(self) -> list[QgsFeature]:
        """ Create point features from pairs of coordinates """
        qPoints = []
        coords = self.dialog.points.get_points()
        for id, pt in enumerate(zip(coords["x"], coords["y"])):
            qPoint = QgsFeature()
            qpt = QgsPointXY(*pt)
            qPoint.setGeometry(QgsGeometry.fromPointXY(qpt))
            qPoint.setAttributes([id + 1])
            qPoints.append(qPoint)
        return qPoints
    def add_layer(self, points:list[QgsFeature]):
        """ Add created point layer to map canvas """
        layerSource = f'Point?crs={self.extent.crs.authid()}&field=id:integer'
        layer = QgsVectorLayer(layerSource, 'random' ,'memory')
        layer.dataProvider().addFeatures(points)
        layer.updateExtents()
        self.registry.addMapLayer(layer)
    def create_point_file(self):
        """" Sample points from extent and create point layer from them """
        if self.dialog.points.coords is None:
            self.dialog.points.sample_points_random(
                self.dialog.extent.get_extent(),
                int(self.dialog.bufferField.text()) if self.dialog.bufferField.text() != '' else 0,
                self.dialog.npointsSpin.value()
            )
        points = self.prepare_points()
        self.add_layer(points)