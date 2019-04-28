# Copyright (c) 2019 Elie Michel
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# The Software is provided “as is”, without warranty of any kind, express or
# implied, including but not limited to the warranties of merchantability,
# fitness for a particular purpose and noninfringement. In no event shall
# the authors or copyright holders be liable for any claim, damages or other
# liability, whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other dealings in the
# Software.
#
# This file is part of LilySurfaceScrapper, a Blender add-on to import materials
# from a single URL

import os

from .Scrappers.AbstractScrapper import AbstractScrapper
from .settings import TEXTURE_DIR, UNSUPPORTED_PROVIDER_ERR

# dirty but useful, for one to painlessly write scrapping class
# and just drop them in the scrappers dir
def makeScrappersList():
    import importlib
    scrappers_names = []
    scrappers_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Scrappers")
    for f in os.listdir(scrappers_dir):
        if f.endswith(".py") and os.path.isfile(os.path.join(scrappers_dir, f)):
            scrappers_names.append(f[:-3])
    scrappers = []
    for s in scrappers_names:
        module = importlib.import_module('.Scrappers.' + s, package='LilySurfaceScrapper')
        for x in dir(module):
            if x == 'AbstractScrapper':
                continue
            m = getattr(module, x)
            if isinstance(m, type) and issubclass(m, AbstractScrapper):
                scrappers.append(m)
    return scrappers
all_scrappers = makeScrappersList()

class MaterialData():
    """Internal representation of materials, responsible on one side for
    scrapping texture providers and on the other side to build blender materials.
    This class must not use the Blender API. Put Blender related stuff in subclasses
    like CyclesMaterialData."""
    
    @classmethod
    def makeScrapper(cls, url):
        global all_scrappers
        for S in all_scrappers:
            if S.canHandleUrl(url):
                return S()
        return None
    
    def __init__(self, url, texture_root=""):
        """url: Base url to scrap
        texture_root: root directory where to store downloaded textures
        """
        self.url = url
        self.name = "Name"
        self.error = None
        self.texture_root = texture_root
        self.maps = {
            'baseColor': None,
            'normal': None,
            'opacity': None,
            'roughness': None,
            'metallic': None,
        }
        self._variants = None
        self._scrapper = MaterialData.makeScrapper(url)
        if self._scrapper is None:
            self.error = UNSUPPORTED_PROVIDER_ERR
        else:
            self._scrapper.texture_root = texture_root
        
    def getVariantList(self):
        if self.error is not None:
            return None
        if self._variants is not None:
            return self._variants
        self._variants = self._scrapper.fetchVariantList(self.url)
        if self._variants is None:
            self.error = self.scrapper.error
        return self._variants

    def selectVariant(self, variant_index):
        if self.error is not None:
            return False
        if self._variants is None:
            self.getVariantList()
        if not self._scrapper.fetchVariant(variant_index, self):
            return False
        return True
    
    def createMaterial(self):
        """Implement this in derived classes"""
        raise NotImplementedError
    