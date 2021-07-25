# Copyright (c) 2019 - 2020 Elie Michel
#
# This file is part of LilySurfaceScraper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import os
import bpy
from .CyclesLightData import CyclesLightData
from .CyclesMaterialData import CyclesMaterialData
from .CyclesWorldData import CyclesWorldData
from .ScrapersManager import ScrapersManager
from .callback import get_callback
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

# -------------------------------------------------------------------
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
        if data.error is None:
            variants = data.getVariantList()
        if data.error is not None:
            self.report({'ERROR_INVALID_INPUT'}, data.error)
            return {'CANCELLED'}

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
        icon = "CHECKMARK" if data.isDownloaded(v) else "IMPORT"
        items.append((str(i), v, v, icon, i))
    internal_states['kbjfknvglvhn'] = items  # keep a reference to avoid a known crash of blander, says the doc
    return items

class OBJECT_OT_LilySurfacePromptVariant(ObjectPopupOperator, CallbackProps):
    """While importing a material, prompt the user for the texture variant
    if there are several materials provided by the URL"""
    bl_idname = "object.lily_surface_prompt_variant"
    bl_label = "Select Variant"
    
    variant: bpy.props.EnumProperty(
        name="Variant",
        description="Name of the material variant to load",
        items=list_variant_enum,
    )

    reisntall: bpy.props.BoolProperty(
        name="Reinstall Textures",
        description="Reinstall the textures instead of using the ones present on the system",
        default=False,
        options={"SKIP_SAVE"}
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
        data.setReinstall(bool(self.reisntall))
        data.selectVariant(int(self.variant))
        if self.create_material:
            mat = data.createMaterial()
            context.object.active_material = mat
        else:
            data.loadImages()
        cb = get_callback(self.callback_handle)
        cb(context)
        return {'FINISHED'}

# -------------------------------------------------------------------
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
        if data.error is None:
            variants = data.getVariantList()
        if data.error is not None:
            self.report({'ERROR_INVALID_INPUT'}, data.error)
            return {'CANCELLED'}

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
        icon = "CHECKMARK" if data.isDownloaded(v) else "IMPORT"
        items.append((str(i), v, v, icon, i))
    internal_states['ikdrtvhdlvhn'] = items  # keep a reference to avoid a known crash of blander, says the doc
    return items

class OBJECT_OT_LilyWorldPromptVariant(PopupOperator, CallbackProps):
    """While importing a world, prompt the user for the texture variant
    if there are several worlds provided by the URL"""
    bl_idname = "object.lily_world_prompt_variant"
    bl_label = "Select Variant"
    
    variant: bpy.props.EnumProperty(
        name="Variant",
        description="Name of the world variant to load",
        items=list_variant_enum,
    )

    reisntall: bpy.props.BoolProperty(
        name="Reinstall Textures",
        description="Reinstall the textures instead of using the ones present on the system",
        default=False,
        options={"SKIP_SAVE"}
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
        data.setReinstall(bool(self.reisntall))
        data.selectVariant(int(self.variant))
        if self.create_world:
            world = data.createWorld()
            context.scene.world = world
        else:
            data.loadImages()
        cb = get_callback(self.callback_handle)
        cb(context)
        return {'FINISHED'}

# -------------------------------------------------------------------
### Light

class OBJECT_OT_LilyLightScraper(PopupOperator, CallbackProps):
    """Import a world just by typing its URL. See documentation for a list of supported world providers."""
    bl_idname = "object.lily_light_import"
    bl_label = "Import light"

    url: bpy.props.StringProperty(
        name="URL",
        description="Address from which importing the light data",
        default=""
    )

    create_world: bpy.props.BoolProperty(
        name="Create World",
        description=(
            "Create the light material associated with downloaded maps. " +
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
        data = CyclesLightData(self.url, texture_root=texdir)
        if data.error is None:
            variants = data.getVariantList()
        if data.error is not None:
            self.report({'ERROR_INVALID_INPUT'}, data.error)
            return {'CANCELLED'}

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
            internal_states['kamour'] = data
            bpy.ops.object.lily_light_prompt_variant('INVOKE_DEFAULT',
                internal_state='kamour',
                callback_handle=self.callback_handle)
        else:
            data.selectVariant(selected_variant)
            data.createLights()
            cb = get_callback(self.callback_handle)
            cb(context)
        return {'FINISHED'}

class OBJECT_OT_LilyClipboardLightScraper(PopupOperator, CallbackProps):
    """Same as lily_world_import except that it gets the URL from clipboard."""
    bl_idname = "object.lily_light_import_from_clipboard"
    bl_label = "Import from clipboard"

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        bpy.ops.object.lily_light_import('EXEC_DEFAULT', url=bpy.context.window_manager.clipboard)
        return {'FINISHED'}

def list_variant_enum(self, context):
    """Callback filling enum items for OBJECT_OT_LilySurfacePromptVariant"""
    global internal_states
    data = internal_states[self.internal_state]
    items = []
    for i, v in enumerate(data.getVariantList()):
        icon = "CHECKMARK" if data.isDownloaded(v) else "IMPORT"
        items.append((str(i), v, v, icon, i))
    internal_states['dsdweykgkbit'] = items  # keep a reference to avoid a known crash of blander, says the doc
    return items

class OBJECT_OT_LilyLightPromptVariant(PopupOperator, CallbackProps):
    """While importing a light, prompt the user for the texture variant
    if there are several worlds provided by the URL"""
    bl_idname = "object.lily_light_prompt_variant"
    bl_label = "Select Variant"

    variant: bpy.props.EnumProperty(
        name="Variant",
        description="Name of the light variant to load",
        items=list_variant_enum,
    )

    reisntall: bpy.props.BoolProperty(
        name="Reinstall Textures",
        description="Reinstall the textures instead of using the ones present on the system",
        default=False,
        options={"SKIP_SAVE"}
    )

    internal_state: bpy.props.StringProperty(
        name="Internal State",
        description="System property used to transfer the state of the operator",
        options={'HIDDEN', 'SKIP_SAVE'}
    )


    def execute(self, context):
        data = internal_states[self.internal_state]
        data.setReinstall(bool(self.reisntall))
        data.selectVariant(int(self.variant))
        data.createLights()
        cb = get_callback(self.callback_handle)
        cb(context)
        return {'FINISHED'}


# -------------------------------------------------------------------
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

class LIGHT_PT_LilySurfaceScraper(bpy.types.Panel):
    """Panel with the Lily Scraper button"""
    bl_label = "Lily Surface Scraper"
    bl_idname = "LIGHT_PT_LilySurfaceScraper"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == "LIGHT"

    def draw(self, context):
        layout = self.layout
        pref = getPreferences(context)
        if bpy.data.filepath == '' and not os.path.isabs(pref.texture_dir):
            layout.label(text="You must save the file to use Lily Surface Scraper")
            layout.label(text="or setup a texture directory in preferences.")
        else:
            layout.operator("object.lily_light_import")
            layout.operator("object.lily_light_import_from_clipboard")
            layout.label(text="Available sources:")
            urls = {None}  # avoid doubles
            for S in ScrapersManager.getScrapersList():
                if 'LIGHT' in S.scraped_type and S.home_url not in urls:
                    layout.operator("wm.url_open", text=S.source_name).url = S.home_url
                    urls.add(S.home_url)

## Registration

classes = (
    OBJECT_OT_LilySurfaceScraper,
    OBJECT_OT_LilyClipboardSurfaceScraper,
    OBJECT_OT_LilySurfacePromptVariant,

    OBJECT_OT_LilyWorldScraper,
    OBJECT_OT_LilyClipboardWorldScraper,
    OBJECT_OT_LilyWorldPromptVariant,

    OBJECT_OT_LilyLightScraper,
    OBJECT_OT_LilyClipboardLightScraper,
    OBJECT_OT_LilyLightPromptVariant,

    MATERIAL_PT_LilySurfaceScraper,
    WORLD_PT_LilySurfaceScraper,
    LIGHT_PT_LilySurfaceScraper,
)

register, unregister = bpy.utils.register_classes_factory(classes)
