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

import bpy

addon_idname = __package__.split(".")[0]

# -----------------------------------------------------------------------------

def getPreferences(context=None):
    if context is None: context = bpy.context
    preferences = context.preferences
    addon_preferences = preferences.addons[addon_idname].preferences
    return addon_preferences

# -----------------------------------------------------------------------------

class LilySurfaceScraperPreferences(bpy.types.AddonPreferences):
    bl_idname = addon_idname

    texture_dir: bpy.props.StringProperty(
        name="Texture Directory",
        subtype='DIR_PATH',
        default="LilySurface",
    )

    ieslibrary_apikey: bpy.props.StringProperty(
        name="ieslibrary API-Key",
        subtype='NONE',
        default="",
    )

    use_ao: bpy.props.BoolProperty(
        name="Use AO map",
        default=False,
    )

    use_arm: bpy.props.BoolProperty(
        name="Use ARM map instead of separate maps for AO/Roughness/Metalness",
        default=True,
    )

    use_ground_hdri: bpy.props.BoolProperty(
        name="Use Ground HDRI",
        default=False,
    )

    ies_use_strength: bpy.props.BoolProperty(
        name="Use Energy Value",
        default=True,
    )

    ies_add_blackbody: bpy.props.BoolProperty(
        name="Add Blackbody node",
        default=True,
    )

    ies_light_strength: bpy.props.BoolProperty(
        name="Use in strength node",
        default=False,
    )

    ies_pack_files: bpy.props.BoolProperty(
        name="Pack IES files internally",
        default=True,
    )

    def draw(self, context):
        layout = self.layout

        layout.label(text="The texture directory where the textures are downloaded.")
        layout.label(text="It can either be relative to the blend file, or global to all files.")
        layout.label(text="If it is relative, you must always save the blend file before importing materials and worlds.")
        layout.prop(self, "texture_dir")

        layout.label(text="For the import of lights from ieslibrary a valid API-Key is needed.")
        layout.label(text="Get the API-Key from ieslibrary.com (login needed)")
        layout.prop(self, "ieslibrary_apikey")

        split1 = layout.split(factor=1/3)

        material = split1.box()
        material.label(text="Material settings")
        material.separator()

        material.label(text="The AO map provided with some material must not be used")
        material.label(text="in a standard surface shader. Nevertheless, you can enable")
        material.label(text="using it as a multiplicator over base color.")
        material.prop(self, "use_ao")
        material.separator()
        material.prop(self, "use_arm")

        split2 = split1.split()

        hdri = split2.box()
        hdri.label(text="HRDI settings")
        hdri.separator()

        hdri.label(text="Ground HDRI projects the environment maps so that it creates a proper ground.")
        hdri.prop(self, "use_ground_hdri")

        textures = split2.box()
        textures.label(text="Light settings")
        textures.separator()

        layout.label(text="Add a Backbody node as color input when importing IES textures")
        layout.prop(self, "ies_add_blackbody")

        textures.label(text="Use the energy value from the IES library to determine the strength of the lamp")
        textures.prop(self, "ies_use_strength")

        if bool(self.ies_use_strength):
            strength = textures.box()
            strength.label(text="Put the energy value in the strength socket of the IES map instead of the lamp energy")
            strength.prop(self, "ies_light_strength")
        # textures.separator()
        textures.prop(self, "ies_pack_files")

# -----------------------------------------------------------------------------

classes = (LilySurfaceScraperPreferences,)

register, unregister = bpy.utils.register_classes_factory(classes)
