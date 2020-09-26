# Copyright (c) 2019 - 2020 Elie Michel
#
# This file is part of LilySurfaceScraper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import os
import bpy
from .CyclesMaterialData import CyclesMaterialData
from .CyclesWorldData import CyclesWorldData
from .ScrapersManager import ScrapersManager
from .callback import register_callback, get_callback
from .preferences import getPreferences
    
## Operators

# I really wish there would be a cleaner way to do so: I need to prompt twice
# the user (once for the URL, then for the variant, loaded from the URL) so I
# end up with two bpy operators but they need to share custom info, not
# sharable through regular properties. SO it is shared through this global
internal_states = {}

class PopupOperator(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class ObjectPopupOperator(PopupOperator):
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

class CallbackProps:
    callback_handle: bpy.props.IntProperty(
        name="Callback Handle",
        description=(
            "Handle to a callback to call once the operator is done." +
            "Use LilySurfaceScraper.register_callback(cb) to get such a handle."
        ),
        options={'HIDDEN', 'SKIP_SAVE'},
        default=-1
    )

### Material

class OBJECT_OT_LilySurfaceScraper(ObjectPopupOperator, CallbackProps):
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

    variant: bpy.props.StringProperty(
        name="Variant",
        description="Look for the variant that has this name (for scripting access only)",
        options={'HIDDEN', 'SKIP_SAVE'},
        default=""
    )

    def execute(self, context):
        pref = getPreferences(context)
        if bpy.data.filepath == '' and not os.path.isabs(pref.texture_dir):
            self.report({'ERROR'}, 'You must save the file before using LilySurfaceScraper')
            return {'CANCELLED'}

        texdir = os.path.dirname(bpy.data.filepath)
        data = CyclesMaterialData(self.url, texture_root=texdir)
        if data.error is not None:
            self.report({'ERROR_INVALID_INPUT'}, data.error)
            return {'CANCELLED'}
        
        variants = data.getVariantList()

        selected_variant = -1
        if not variants or len(variants) == 1:
            selected_variant = 0
        elif self.variant != "":
            for i, v in enumerate(variants):
                if v == self.variant:
                    selected_variant = i
                    break
        
        if selected_variant == -1:
            # More than one variant, prompt the user for which one she wants
            internal_states['skjhnvjkbg'] = data
            bpy.ops.object.lily_surface_prompt_variant('INVOKE_DEFAULT',
                internal_state='skjhnvjkbg',
                create_material=self.create_material,
                callback_handle=self.callback_handle)
        else:
            data.selectVariant(selected_variant)
            if self.create_material:
                mat = data.createMaterial()
                context.object.active_material = mat
            else:
                data.loadImages()
            cb = get_callback(self.callback_handle)
            cb(context)
        return {'FINISHED'}

class OBJECT_OT_LilyClipboardSurfaceScraper(ObjectPopupOperator, CallbackProps):
    """Same as lily_surface_import except that it gets the URL from clipboard."""
    bl_idname = "object.lily_surface_import_from_clipboard"
    bl_label = "Import from clipboard"
    
    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        bpy.ops.object.lily_surface_import('EXEC_DEFAULT', url=bpy.context.window_manager.clipboard)
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

class OBJECT_OT_LilySurfacePromptVariant(ObjectPopupOperator, CallbackProps):
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

class OBJECT_OT_LilyWorldScraper(PopupOperator, CallbackProps):
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

    variant: bpy.props.StringProperty(
        name="Variant",
        description="Look for the variant that has this name (for scripting access only)",
        options={'HIDDEN', 'SKIP_SAVE'},
        default=""
    )

    def execute(self, context):
        pref = getPreferences(context)
        if bpy.data.filepath == '' and not os.path.isabs(pref.texture_dir):
            self.report({'ERROR'}, 'You must save the file before using LilySurfaceScraper')
            return {'CANCELLED'}

        texdir = os.path.dirname(bpy.data.filepath)
        data = CyclesWorldData(self.url, texture_root=texdir)
        if data.error is not None:
            self.report({'ERROR_INVALID_INPUT'}, data.error)
            return {'CANCELLED'}
        
        variants = data.getVariantList()

        selected_variant = -1
        if not variants or len(variants) == 1:
            selected_variant = 0
        elif self.variant != "":
            for i, v in enumerate(variants):
                if v == self.variant:
                    selected_variant = i
                    break
        
        if selected_variant == -1:
            # More than one variant, prompt the user for which one she wants
            internal_states['zeilult'] = data
            bpy.ops.object.lily_world_prompt_variant('INVOKE_DEFAULT',
                internal_state='zeilult',
                create_world=self.create_world,
                callback_handle=self.callback_handle)
        else:
            data.selectVariant(selected_variant)
            if self.create_world:
                world = data.createWorld()
                context.scene.world = world
            else:
                data.loadImages()
            cb = get_callback(self.callback_handle)
            cb(context)
        return {'FINISHED'}
        
class OBJECT_OT_LilyClipboardWorldScraper(PopupOperator, CallbackProps):
    """Same as lily_world_import except that it gets the URL from clipboard."""
    bl_idname = "object.lily_world_import_from_clipboard"
    bl_label = "Import from clipboard"
    
    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        bpy.ops.object.lily_world_import('EXEC_DEFAULT', url=bpy.context.window_manager.clipboard)
        return {'FINISHED'}

def list_variant_enum(self, context):
    """Callback filling enum items for OBJECT_OT_LilySurfacePromptVariant"""
    global internal_states
    data = internal_states[self.internal_state]
    items = []
    for i, v in enumerate(data.getVariantList()):
        items.append((str(i), v, v))
    internal_states['ikdrtvhdlvhn'] = items # keep a reference to avoid a known crash of blander, says the doc
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

class MATERIAL_PT_LilySurfaceScraper(bpy.types.Panel):
    """Panel with the Lily Scraper button"""
    bl_label = "Lily Surface Scraper"
    bl_idname = "MATERIAL_PT_LilySurfaceScraper"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        pref = getPreferences(context)
        if bpy.data.filepath == '' and not os.path.isabs(pref.texture_dir):
            layout.label(text="You must save the file to use Lily Surface Scraper")
            layout.label(text="or setup a texture directory in preferences.")
        else:
            layout.operator("object.lily_surface_import")
            layout.operator("object.lily_surface_import_from_clipboard")
            layout.label(text="Available sources:")
            urls = {None}  # avoid doubles
            for S in ScrapersManager.getScrapersList():
                if 'MATERIAL' in S.scraped_type and S.home_url not in urls:
                    layout.operator("wm.url_open", text=S.source_name).url = S.home_url
                    urls.add(S.home_url)

class WORLD_PT_LilySurfaceScraper(bpy.types.Panel):
    """Panel with the Lily Scraper button"""
    bl_label = "Lily Surface Scraper"
    bl_idname = "WORLD_PT_LilySurfaceScraper"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"

    def draw(self, context):
        layout = self.layout
        pref = getPreferences(context)
        if bpy.data.filepath == '' and not os.path.isabs(pref.texture_dir):
            layout.label(text="You must save the file to use Lily Surface Scraper")
            layout.label(text="or setup a texture directory in preferences.")
        else:
            layout.operator("object.lily_world_import")
            layout.operator("object.lily_world_import_from_clipboard")
            layout.label(text="Available sources:")
            urls = {None}  # avoid doubles
            for S in ScrapersManager.getScrapersList():
                if 'WORLD' in S.scraped_type and S.home_url not in urls:
                    layout.operator("wm.url_open", text=S.source_name).url = S.home_url
                    urls.add(S.home_url)

## Registration

def register():
    bpy.utils.register_class(OBJECT_OT_LilySurfaceScraper)
    bpy.utils.register_class(OBJECT_OT_LilyClipboardSurfaceScraper)
    bpy.utils.register_class(OBJECT_OT_LilySurfacePromptVariant)
    bpy.utils.register_class(OBJECT_OT_LilyWorldScraper)
    bpy.utils.register_class(OBJECT_OT_LilyClipboardWorldScraper)
    bpy.utils.register_class(OBJECT_OT_LilyWorldPromptVariant)
    bpy.utils.register_class(MATERIAL_PT_LilySurfaceScraper)
    bpy.utils.register_class(WORLD_PT_LilySurfaceScraper)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_LilySurfaceScraper)
    bpy.utils.unregister_class(OBJECT_OT_LilyClipboardSurfaceScraper)
    bpy.utils.unregister_class(OBJECT_OT_LilySurfacePromptVariant)
    bpy.utils.unregister_class(OBJECT_OT_LilyWorldScraper)
    bpy.utils.unregister_class(OBJECT_OT_LilyClipboardWorldScraper)
    bpy.utils.unregister_class(OBJECT_OT_LilyWorldPromptVariant)
    bpy.utils.unregister_class(MATERIAL_PT_LilySurfaceScraper)
    bpy.utils.unregister_class(WORLD_PT_LilySurfaceScraper)
