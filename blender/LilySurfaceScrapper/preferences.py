# Copyright (c) 2019-2020 Elie Michel
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

import bpy

addon_idname = __package__.split(".")[0]

# -----------------------------------------------------------------------------

def ensureLxmlInstalled():
    try:
        from lxml import etree
    except (ImportError, ModuleNotFoundError):
        print("LilySurfaceScrapper: No system-wide installation of lxml found. Installing it...")
        import sys
        import subprocess
        import importlib
        binary_path_python = sys.executable
        if binary_path_python.endswith(("blender", "blender.exe")):
            import bpy
            binary_path_python = bpy.app.binary_path_python
        try:
            # Not all releases have ensurepip, but if they don't they have pip
            subprocess.check_call([binary_path_python, "-m", "ensurepip"])
        except subprocess.CalledProcessError:
            pass
        subprocess.check_call([binary_path_python, "-m", "pip", "install", "--user", "--upgrade", "pip"]) # upgrading pip
        subprocess.check_call([binary_path_python, "-m", "pip", "install", "--user", "lxml"]) # TODO Use a requirements.txt instead
        importlib.invalidate_caches()
        from lxml import etree


def getPreferences(context=None):
    if context is None: context = bpy.context
    preferences = context.preferences
    addon_preferences = preferences.addons[addon_idname].preferences
    return addon_preferences

# -----------------------------------------------------------------------------

class LilySurfaceScrapperPreferences(bpy.types.AddonPreferences):
    bl_idname = addon_idname

    texture_dir: bpy.props.StringProperty(
        name="Texture Directory",
        subtype='DIR_PATH',
        default="LilySurface",
        )

    def draw(self, context):
        layout = self.layout
        layout.label(text="The texture directory where the textures are downloaded.")
        layout.label(text="It can either be relative to the blend file, or global to all files.")
        layout.label(text="If it is relative, you must always save the blend file before importing materials and worlds.")
        layout.prop(self, "texture_dir")

# -----------------------------------------------------------------------------

classes = (LilySurfaceScrapperPreferences,)

register, unregister = bpy.utils.register_classes_factory(classes)
