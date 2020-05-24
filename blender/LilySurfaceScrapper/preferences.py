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

import os.path
import bpy
import sys
import os

addon_idname = __package__.split(".")[0]

# -----------------------------------------------------------------------------

def modules_path():
    # Copied and adapted from https://github.com/jesterKing/import_3dm/blob/9f96e644e40edd571829cbaf777d6bda63dbb5db/import_3dm/read3dm.py
    # set up addons/modules under the user
    # script path. Here we'll install the
    # dependencies
    modulespath = os.path.normpath(
        os.path.join(
            bpy.utils.script_path_user(),
            "addons",
            "modules"
        )
    )
    if not os.path.exists(modulespath):
        os.makedirs(modulespath)

    # set user modules path at beginning of paths for earlier hit
    if sys.path[1] != modulespath:
        sys.path.insert(1, modulespath)

    return modulespath

modules_path()

def install_dependencies():
    # Copied and adapted from https://github.com/jesterKing/import_3dm/blob/9f96e644e40edd571829cbaf777d6bda63dbb5db/import_3dm/read3dm.py
    modulespath = modules_path()

    try:
        from subprocess import run as sprun
        try:
            import pip
        except:
            print("LilySurfaceScrapper: Installing pip... "),
            pyver = ""
            if sys.platform != "win32":
                pyver = "python{}.{}".format(
                    sys.version_info.major,
                    sys.version_info.minor
                )

            ensurepip = os.path.normpath(
                os.path.join(
                    os.path.dirname(bpy.app.binary_path_python),
                    "..", "lib", pyver, "ensurepip"
                )
            )
            # install pip using the user scheme using the Python
            # version bundled with Blender
            res = sprun([bpy.app.binary_path_python, ensurepip, "--user"])

            if res.returncode == 0:
                import pip
            else:
                raise Exception("Failed to install pip.")

        print("LilySurfaceScrapper: Installing lxml to {}... ".format(modulespath)),

        # call pip in a subprocess so we don't have to mess
        # with internals. Also, this ensures the Python used to
        # install pip is going to be used
        res = sprun([bpy.app.binary_path_python, "-m", "pip", "install", "--upgrade", "--target", modulespath, "lxml"])
        if res.returncode!=0:
            print("LilySurfaceScrapper: Please try manually installing lxml with: pip3 install --upgrade --target {} lxml".format(modulespath))
            raise Exception("Failed to install lxml. See console for manual install instruction.")
    except:
        raise Exception("Failed to install dependencies. Please make sure you have pip installed.")

def ensureLxmlInstalled():
    try:
        from lxml import etree
    except (ImportError, ModuleNotFoundError):
        print("LilySurfaceScrapper: No system-wide installation of lxml found. Installing it...")
        import importlib
        
        install_dependencies()
        
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
