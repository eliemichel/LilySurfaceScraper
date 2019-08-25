# Copyright (c) 2019 Elie Michel
#
# This file is part of LilySurfaceScrapper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

bl_info = {
    "name": "Lily Surface Scrapper",
    "author": "Élie Michel <elie.michel@exppad.com>",
    "version": (1, 1, 5),
    "blender": (2, 80, 0),
    "location": "Properties > Material",
    "description": "Import material from a single URL",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://github.com/eliemichel/LilySurfaceScrapper/issues",
    "support": "COMMUNITY",
    "category": "Import",
}

from . import frontend
from .callback import register_callback

def register():
    frontend.register()
    
def unregister():
    frontend.unregister()

if __name__ == "__main__":
    register()
