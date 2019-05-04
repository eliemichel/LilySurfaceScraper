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
import bpy
from .CyclesMaterialData import CyclesMaterialData
from .CyclesWorldData import CyclesWorldData

## Operators

# I really wish there would be a cleaner way to do so: I need to prompt twice
# the user (once for the URL, then for the variant, loaded from the URL) so I
# end up with two bpy operators but they need to share custom info, not
# sharable through regular properties. SO it is shared through this global
internal_states = {}

class PopupOperator(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

### Material

class OBJECT_OT_LilySurfaceScrapper(PopupOperator):
    """Import a material just by typing its URL. See documentation for a list of supported material providers."""
    bl_idname = "object.lily_surface_import"
    bl_label = "Import Surface"
    
    url: bpy.props.StringProperty(
        name="URL",
        description="Address from which importing the material",
        default=""
    )

    create_material: bpy.props.BoolProperty(
        name="Create Material",
        description=(
            "Create the material associated with downloaded maps. " +
            "You most likely want this, but for integration into other tool " +
            "you may want to set it to false and handle the material creation by yourself."
        ),
        options={'HIDDEN', 'SKIP_SAVE'},
        default=True
    )

    def execute(self, context):
        if bpy.data.filepath == '':
            self.report({'ERROR'}, 'You must save the file before using LilySurfaceScrapper')
            return {'CANCELLED'}

        texdir = os.path.dirname(bpy.data.filepath)
        data = CyclesMaterialData(self.url, texture_root=texdir)
        if data.error is not None:
            self.report({'ERROR_INVALID_INPUT'}, data.error)
            return {'CANCELLED'}
        
        variants = data.getVariantList()
        if variants and len(variants) > 1:
            # More than one variant, prompt the user for which one she wants
            internal_states['skjhnvjkbg'] = data
            bpy.ops.object.lily_surface_prompt_variant('INVOKE_DEFAULT', internal_state='skjhnvjkbg', create_material=self.create_material)
        else:
            data.selectVariant(0)
            if self.create_material:
                mat = data.createMaterial()
                context.object.active_material = mat
            else:
                data.loadImages()
        return {'FINISHED'}
        

def list_variant_enum(self, context):
    """Callback filling enum items for OBJECT_OT_LilySurfacePromptVariant"""
    global internal_states
    data = internal_states[self.internal_state]
    items = []
    for i, v in enumerate(data.getVariantList()):
        items.append((str(i), v, v))
    internal_states['kbjfknvglvhn'] = items # keep a reference to avoid a known crash of blander, says the doc
    return items

class OBJECT_OT_LilySurfacePromptVariant(PopupOperator):
    """While importing a material, prompt the user for teh texture variant
    if there are several materials provided by the URL"""
    bl_idname = "object.lily_surface_prompt_variant"
    bl_label = "Select Variant"
    
    variant: bpy.props.EnumProperty(
        name="Variant",
        description="Name of the material variant to load",
        items=list_variant_enum,
    )
    
    internal_state: bpy.props.StringProperty(
        name="Internal State",
        description="System property used to transfer the state of the operator",
        options={'HIDDEN', 'SKIP_SAVE'},
        update=lambda self, ctx: self.variant
    )

    create_material: bpy.props.BoolProperty(
        name="Create Material",
        description=(
            "Create the material associated with downloaded maps. " +
            "You most likely want this, but for integration into other tool " +
            "you may want to set it to false and handle the material creation by yourself."
        ),
        options={'HIDDEN', 'SKIP_SAVE'},
        default=True
    )

    def execute(self, context):
        data = internal_states[self.internal_state]
        data.selectVariant(int(self.variant))
        if self.create_material:
            mat = data.createMaterial()
            context.object.active_material = mat
        else:
            data.loadImages()
        return {'FINISHED'}

### World

class OBJECT_OT_LilyWorldScrapper(PopupOperator):
    """Import a world just by typing its URL. See documentation for a list of supported world providers."""
    bl_idname = "object.lily_world_import"
    bl_label = "Import World"
    
    url: bpy.props.StringProperty(
        name="URL",
        description="Address from which importing the world",
        default=""
    )

    create_world: bpy.props.BoolProperty(
        name="Create World",
        description=(
            "Create the world associated with downloaded maps. " +
            "You most likely want this, but for integration into other tool " +
            "you may want to set it to false and handle the world creation by yourself."
        ),
        options={'HIDDEN', 'SKIP_SAVE'},
        default=True
    )

    def execute(self, context):
        if bpy.data.filepath == '':
            self.report({'ERROR'}, 'You must save the file before using LilySurfaceScrapper')
            return {'CANCELLED'}

        texdir = os.path.dirname(bpy.data.filepath)
        data = CyclesWorldData(self.url, texture_root=texdir)
        if data.error is not None:
            self.report({'ERROR_INVALID_INPUT'}, data.error)
            return {'CANCELLED'}
        
        variants = data.getVariantList()
        if variants and len(variants) > 1:
            # More than one variant, prompt the user for which one she wants
            internal_states['zeilult'] = data
            bpy.ops.object.lily_world_prompt_variant('INVOKE_DEFAULT', internal_state='zeilult', create_world=self.create_world)
        else:
            data.selectVariant(0)
            if self.create_world:
                world = data.createWorld()
                context.scene.world = world
            else:
                data.loadImages()
        return {'FINISHED'}
        

def list_variant_enum(self, context):
    """Callback filling enum items for OBJECT_OT_LilySurfacePromptVariant"""
    global internal_states
    data = internal_states[self.internal_state]
    items = []
    for i, v in enumerate(data.getVariantList()):
        items.append((str(i), v, v))
    internal_states['kbjfknvglvhn'] = items # keep a reference to avoid a known crash of blander, says the doc
    return items

class OBJECT_OT_LilyWorldPromptVariant(PopupOperator):
    """While importing a world, prompt the user for teh texture variant
    if there are several worlds provided by the URL"""
    bl_idname = "object.lily_world_prompt_variant"
    bl_label = "Select Variant"
    
    variant: bpy.props.EnumProperty(
        name="Variant",
        description="Name of the world variant to load",
        items=list_variant_enum,
    )
    
    internal_state: bpy.props.StringProperty(
        name="Internal State",
        description="System property used to transfer the state of the operator",
        options={'HIDDEN', 'SKIP_SAVE'},
        update=lambda self, ctx: self.variant
    )

    create_world: bpy.props.BoolProperty(
        name="Create World",
        description=(
            "Create the world associated with downloaded maps. " +
            "You most likely want this, but for integration into other tool " +
            "you may want to set it to false and handle the world creation by yourself."
        ),
        options={'HIDDEN', 'SKIP_SAVE'},
        default=True
    )

    def execute(self, context):
        data = internal_states[self.internal_state]
        data.selectVariant(int(self.variant))
        if self.create_world:
            world = data.createWorld()
            context.scene.world = world
        else:
            data.loadImages()
        return {'FINISHED'}


## Panels

class MATERIAL_PT_LilySurfaceScrapper(bpy.types.Panel):
    """Panel with the Lily Scrapper button"""
    bl_label = "Lily Surface Scrapper"
    bl_idname = "MATERIAL_PT_LilySurfaceScrapper"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if bpy.data.filepath == '':
            row.label(text="You must save the file to use Lily Surface Scrapper")
        else:
            row.operator("object.lily_surface_import")

class WORLD_PT_LilySurfaceScrapper(bpy.types.Panel):
    """Panel with the Lily Scrapper button"""
    bl_label = "Lily Surface Scrapper"
    bl_idname = "WORLD_PT_LilySurfaceScrapper"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if bpy.data.filepath == '':
            row.label(text="You must save the file to use Lily Surface Scrapper")
        else:
            row.operator("object.lily_world_import")

## Registration

def register():
    bpy.utils.register_class(OBJECT_OT_LilySurfaceScrapper)
    bpy.utils.register_class(OBJECT_OT_LilySurfacePromptVariant)
    bpy.utils.register_class(OBJECT_OT_LilyWorldScrapper)
    bpy.utils.register_class(OBJECT_OT_LilyWorldPromptVariant)
    bpy.utils.register_class(MATERIAL_PT_LilySurfaceScrapper)
    bpy.utils.register_class(WORLD_PT_LilySurfaceScrapper)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_LilySurfaceScrapper)
    bpy.utils.unregister_class(OBJECT_OT_LilySurfacePromptVariant)
    bpy.utils.unregister_class(OBJECT_OT_LilyWorldScrapper)
    bpy.utils.unregister_class(OBJECT_OT_LilyWorldPromptVariant)
    bpy.utils.unregister_class(MATERIAL_PT_LilySurfaceScrapper)
    bpy.utils.unregister_class(WORLD_PT_LilySurfaceScrapper)
