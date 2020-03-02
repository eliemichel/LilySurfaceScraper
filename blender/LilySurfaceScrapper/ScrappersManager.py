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

class ScrappersManager():
    all_scrappers = None

    @staticmethod
    def makeScrappersList():
        """dirty but useful, for one to painlessly write scrapping class
        and just drop them in the scrappers dir"""
        import importlib
        scrappers_names = []
        scrappers_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Scrappers")
        package = __name__[:__name__.rfind('.')]
        for f in os.listdir(scrappers_dir):
            if f.endswith(".py") and os.path.isfile(os.path.join(scrappers_dir, f)):
                scrappers_names.append(f[:-3])
        scrappers = []
        for s in scrappers_names:
            module = importlib.import_module('.Scrappers.' + s, package=package)
            for x in dir(module):
                if x == 'AbstractScrapper':
                    continue
                m = getattr(module, x)
                if isinstance(m, type) and issubclass(m, AbstractScrapper):
                    scrappers.append(m)
        return scrappers

    @classmethod
    def getScrappersList(cls):
        if cls.all_scrappers is None:
            cls.all_scrappers = ScrappersManager.makeScrappersList()
        return cls.all_scrappers
