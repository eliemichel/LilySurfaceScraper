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

from .settings import UNSUPPORTED_PROVIDER_ERR


class ScrapedData():
    """Internal representation of materials and worlds, responsible on one side for
    scrapping texture providers and on the other side to build blender materials.
    This class must not use the Blender API. Put Blender related stuff in subclasses
    like CyclesMaterialData."""

    @classmethod
    def makeScraper(cls, url):
        raise NotImplementedError

    def __init__(self, url, texture_root="", asset_name=None, scraping_type=None):
        """url: Base url to scrape
        texture_root: root directory where to store downloaded textures
        asset_name: the name of the asset / folder name
        """
        self.url = url.strip('"')
        deep_check = False
        if asset_name == "LOCAL_FILE_SCRAPER-SUBDIR":
            asset_name = None
            deep_check = True
        self.asset_name = asset_name
        self.error = None
        if url is None and asset_name is None:
            self.error = "No source given"

        self.texture_root = texture_root
        self.metadata = None
        self._scraper = type(self).makeScraper(self.url)
        self.reinstall = False

        if self._scraper is None:
            self.error = UNSUPPORTED_PROVIDER_ERR
        else:
            self._scraper.texture_root = texture_root
            self._scraper.metadata.scrape_type = scraping_type
            self._scraper.metadata.deep_check = deep_check

    def getVariantList(self):
        if self.error is not None:
            return None
        if self.metadata is not None:
            return self.metadata.variants
        if self.asset_name is not None:
            self._scraper.getVariantData(self.asset_name)
        else:
            self._scraper.fetchVariantList(self.url)
        self.metadata = self._scraper.metadata
        if not self.metadata.variants:
            self.error = self._scraper.error
        return self.metadata.variants

    def selectVariant(self, variant_index):
        if self.error is not None:
            return False
        if self.metadata is None:
            self.getVariantList()
        if not self._scraper.fetchVariant(variant_index, self):
            return False
        return True

    def setReinstall(self, value):
        self.reinstall = value
        self._scraper.reinstall = value

    def isDownloaded(self, variant):
        return self._scraper.isDownloaded(variant)
