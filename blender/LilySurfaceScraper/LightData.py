# Copyright (c) 2020 Zivoy and Elie Michel
#
# This file is part of LilySurfaceScraper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

from .ScrapersManager import ScrapersManager
from .ScrapedData import ScrapedData


class LightData(ScrapedData):
    """Internal representation of world, responsible on one side for
    scrapping texture providers and on the other side to build blender materials.
    This class must not use the Blender API. Put Blender related stuff in subclasses
    like CyclesMaterialData."""

    def __init__(self, url, texture_root="", asset_name=None):
        super().__init__(url, texture_root=texture_root, asset_name=asset_name, scraping_type="LIGHT")

        self.name = "Lily Light"
        self.maps = {
            'ies': None,
            'energy': None
        }

    @classmethod
    def makeScraper(cls, url):
        for S in ScrapersManager.getScrapersList():
            if 'LIGHT' in S.scraped_type and S.canHandleUrl(url):
                return S()
        return None

    def createLights(self):
        """Implement this in derived classes"""
        raise NotImplementedError
