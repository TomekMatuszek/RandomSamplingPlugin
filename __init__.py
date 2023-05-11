# -*- coding: utf-8 -*-
def classFactory(iface):
    from .sampling_plugin import SamplingPlugin
    return SamplingPlugin(iface)
