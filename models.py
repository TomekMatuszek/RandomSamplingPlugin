from qgis.gui import QgisInterface
from qgis.core import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
import numpy as np

class Extent:
    """ Class used to generate and store extent used to point sampling """
    def __init__(self, iface:QgisInterface=None):
        self.iface = iface
        self.crs = QgsProject.instance().crs()
    def update_layers(self, layersList:list[QgsVectorLayer]=[QgsVectorLayer()]):
        """ Update list of layers to properly choose layer in get_extent_from_layer() method"""
        self.layers = layersList
    def get_extent_from_layer(self, index:int) -> QgsRectangle:
        """ Set extent for sampling using layer from current project """
        index = index-1 if index > 0 else 0
        layer = self.layers[index]
        if isinstance(layer, QgsVectorLayer):
            self.crs = layer.sourceCrs()
            self.source = [f.geometry() for f in layer.getFeatures()]
            self.extent = layer.extent()
        elif isinstance(layer, QgsRasterLayer):
            self.extent = layer.dataProvider().extent()
            self.crs = layer.crs()
            self.source = [QgsGeometry.fromRect(self.extent)]
        return self.extent
    def get_extent_from_file(self, file:str) -> QgsRectangle:
        """ Set extent for sampling using layer from chosen file """
        if file.endswith(('.shp', '.gpkg')):
            layer = QgsVectorLayer(file, "v_layer")
            self.crs = layer.sourceCrs()
            self.source = [f.geometry() for f in layer.getFeatures()]
            self.extent = layer.extent()
        elif file.endswith('.tif'):
            layer = QgsRasterLayer(file, "r_layer")
            self.extent = layer.dataProvider().extent()
            self.crs = layer.crs()
            self.source = [QgsGeometry.fromRect(self.extent)]
        else:
            self.iface.messageBar().pushWarning('Invalid file', 'file extension not recognized, extent taken from canvas')
            self.get_extent_from_canvas()
        return self.extent
    def get_extent_from_canvas(self) -> QgsRectangle:
        """ Set extent for sampling from current map canvas """
        self.extent = self.iface.mapCanvas().extent()
        self.crs = QgsProject.instance().crs()
        self.source = [QgsGeometry.fromRect(self.extent)]
        return self.extent
    def get_extent(self) -> QgsRectangle:
        """ Return current extent """
        return self.extent
    def get_source(self) -> list[QgsGeometry]:
        """ Return source layer of current extent """
        return self.source
    
class Points:
    """ Class used to generate and store random points """
    def __init__(self, iface:QgisInterface=None):
        self.iface = iface
        self.coords = None
    def sample_points_random(self, extent:QgsRectangle, buffer:int, npoints:int, seed:str="") -> dict[str, list]:
        """ Sample points randomly from extent """
        seed = int(seed) if seed != '' else np.random.randint(1, 10000)
        np.random.seed(seed)
        x = list(np.random.uniform(extent.xMinimum() - buffer, extent.xMaximum() + buffer, npoints))
        y = list(np.random.uniform(extent.yMinimum() - buffer, extent.yMaximum() + buffer, npoints))
        self.coords = {"x": x, "y": y}
        return self.coords
    def sample_points_stratified(self, buffer, npoints, spacing) -> dict[str, list]:
        return self.coords
    def sample_points_regular(self, buffer, spacing) -> dict[str, list]:
        return self.coords
    def get_points(self) -> dict[str, list]:
        """ Return currently sampled points """
        return self.coords