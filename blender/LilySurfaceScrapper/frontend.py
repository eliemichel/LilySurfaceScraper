# Copyright (c) 2019 Elie Michel
#
# This file is part of LilySurfaceScrapper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import os
import bpy
from .CyclesMaterialData import CyclesMaterialData
from .CyclesWorldData import CyclesWorldData
from .callback import register_callback, get_callback

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

class CallbackProps:
    callback_handle: bpy.props.IntProperty(
        name="Callback Handle",
        description=(
            "Handle to a callback to call once the operator is done." +
            "Use LilySurfaceScrapper.register_callback(cb) to get such a handle."
        ),
        options={'HIDDEN', 'SKIP_SAVE'},
        default=-1
    )


### Material

class OBJECT_OT_LilySurfaceScrapper(PopupOperator, CallbackProps):
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
            bpy.ops.object.lily_surface_prompt_variant('INVOKE_DEFAULT',
                internal_state='skjhnvjkbg',
                create_material=self.create_material,
                callback_handle=self.callback_handle)
        else:
            data.selectVariant(0)
            if self.create_material:
                mat = data.createMaterial()
                context.object.active_material = mat
            else:
                data.loadImages()
            cb = get_callback(self.callback_handle)
            cb(context)
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

class OBJECT_OT_LilySurfacePromptVariant(PopupOperator, CallbackProps):
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
        options={'HIDDEN', 'SKIP_SAVE'}
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
        cb = get_callback(self.callback_handle)
        cb(context)
        return {'FINISHED'}

### World

class OBJECT_OT_LilyWorldScrapper(PopupOperator, CallbackProps):
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
            bpy.ops.object.lily_world_prompt_variant('INVOKE_DEFAULT',
                internal_state='zeilult',
                create_world=self.create_world,
                callback_handle=self.callback_handle)
        else:
            data.selectVariant(0)
            if self.create_world:
                world = data.createWorld()
                context.scene.world = world
            else:
                data.loadImages()
            cb = get_callback(self.callback_handle)
            cb(context)
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

class OBJECT_OT_LilyWorldPromptVariant(PopupOperator, CallbackProps):
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
        options={'HIDDEN', 'SKIP_SAVE'}
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
        cb = get_callback(self.callback_handle)
        cb(context)
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
