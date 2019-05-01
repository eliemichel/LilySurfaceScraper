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

from .ScrappersManager import ScrappersManager
from .ScrappedData import ScrappedData

class WorldData(ScrappedData):
    """Internal representation of world, responsible on one side for
    scrapping texture providers and on the other side to build blender materials.
    This class must not use the Blender API. Put Blender related stuff in subclasses
    like CyclesMaterialData."""
    
    def reset(self):
        self.name = "Lily World"
        self.maps = {
            'sky': None,
        }

    @classmethod
    def makeScrapper(cls, url):
        for S in ScrappersManager.getScrappersList():
            if 'WORLD' in S.scrapped_type and S.canHandleUrl(url):
                return S()
        return None
    
    def createWorld(self):
        """Implement this in derived classes"""
        raise NotImplementedError
    