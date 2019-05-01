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

from .settings import UNSUPPORTED_PROVIDER_ERR

class ScrappedData():
    """Internal representation of materials and worlds, responsible on one side for
    scrapping texture providers and on the other side to build blender materials.
    This class must not use the Blender API. Put Blender related stuff in subclasses
    like CyclesMaterialData."""

    @classmethod
    def makeScrapper(cls, url):
        raise NotImplementedError

    def reset(self):
        """Implement in subclasses to (re)init specific data"""
        pass

    def __init__(self, url, texture_root=""):
        """url: Base url to scrap
        texture_root: root directory where to store downloaded textures
        """
        self.url = url
        self.texture_root = texture_root
        self.error = None
        self._variants = None
        self._scrapper = type(self).makeScrapper(url)
        if self._scrapper is None:
            self.error = UNSUPPORTED_PROVIDER_ERR
        else:
            self._scrapper.texture_root = texture_root
        self.reset()

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
