# Copyright (c) 2019-2020 Elie Michel
#
# This file is part of LilySurfaceScrapper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

bl_info = {
    "name": "Lily Surface Scrapper",
    "author": "Élie Michel <elie.michel@exppad.com>",
    "version": (1, 3, 2),
    "blender": (2, 82, 0),
    "location": "Properties > Material",
    "description": "Import material from a single URL",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://github.com/eliemichel/LilySurfaceScrapper/issues",
    "support": "COMMUNITY",
    "category": "Import",
}

def isImportedInBlender():
    try:
        import bpy
        return True
    except ImportError:
        return False

if isImportedInBlender():
    from . import frontend
    from . import preferences
    from .callback import register_callback

    def register():
        preferences.register()
        frontend.register()
        
    def unregister():
        frontend.unregister()
        preferences.unregister()

    if __name__ == "__main__":
        register()

else:
    from .WorldData import WorldData
    from .MaterialData import MaterialData
    from .ScrappersManager import ScrappersManager
