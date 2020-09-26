# Copyright (c) 2019 - 2020 Elie Michel
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
# This file is part of LilySurfaceScraper, a Blender add-on to import materials
# from a single URL

from .ScrapersManager import ScrapersManager
from .ScrapedData import ScrapedData

class MaterialData(ScrapedData):
    """Internal representation of materials, responsible on one side for
    scrapping texture providers and on the other side to build blender materials.
    This class must not use the Blender API. Put Blender related stuff in subclasses
    like CyclesMaterialData."""
    
    def reset(self):
        self.name = "Lily Material"
        # FIXME Maybe we can use Python enums instead?
        self.maps = {
            'baseColor': None,
            'diffuse': None,
            'normal': None,
            'normalInvertedY': None, # https://help.cc0textures.com/doku.php?id=usage:directx-opengl
            'opacity': None,
            'roughness': None,
            'glossiness': None,
            'metallic': None,
            'specular': None,
            'height': None,
            'vectorDisplacement': None,
            'emission': None,
            'ambientOcclusion': None,
            'ambientOcclusionRough': None,
        }

    @classmethod
    def makeScraper(cls, url):
        for S in ScrapersManager.getScrapersList():
            if 'MATERIAL' in S.scraped_type and S.canHandleUrl(url):
                print("Using scraper '{}'".format(S.__name__))
                return S()
        return None
    
    def loadImages(self):
        """This is not needed by createMaterial, but is called when
        create_material is false to load images anyway
        Implement this in derived classes"""
        raise NotImplementedError

    def createMaterial(self):
        """Implement this in derived classes"""
        raise NotImplementedError
    