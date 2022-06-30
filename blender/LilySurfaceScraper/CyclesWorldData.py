# Copyright (c) 2019 - 2020 Elie Michel
#
# This file is part of LilySurfaceScraper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import bpy
import os

from .WorldData import WorldData
from .cycles_utils import (
    getCyclesImage, autoAlignNodes,
    PrincipledWorldWrapper, guessColorSpaceFromExtension
)
from .preferences import getPreferences

def getGroundHdriNodeGroup():
    if "GroundHdri" not in bpy.data.node_groups:
        blendfile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "database.blend")
        section   = "\\NodeTree\\"
        object    = "GroundHdri"
        filepath  = blendfile + section + object
        directory = blendfile + section
        filename  = object
        bpy.ops.wm.append(
            filepath=filepath,
            filename=filename,
            directory=directory)
    return bpy.data.node_groups["GroundHdri"]

class CyclesWorldData(WorldData):
    def loadImages(self):
        """This is not needed by createMaterial, but is called when
        create_material is false to load images anyway"""
        img = self.maps['sky']
        if img is not None:
            getCyclesImage(img)
            
    def createWorld(self):
        world = bpy.data.worlds.new(name=self.name)
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        PrincipledWorldWrapper
        principled_world = PrincipledWorldWrapper(world)
        background = principled_world.node_background
        world_output = principled_world.node_out

        img = self.maps['sky']
        if img is not None:
            texture_node = nodes.new(type="ShaderNodeTexEnvironment")
            texture_node.image = getCyclesImage(img)
            color_space = guessColorSpaceFromExtension(texture_node.image, img)
            texture_node.image.colorspace_settings.name = color_space["name"]
            if hasattr(texture_node, "color_space"):
                texture_node.color_space = color_space["old_name"]
            links.new(texture_node.outputs["Color"], background.inputs["Color"])

            mapping_node = nodes.new(type="ShaderNodeMapping")

            pref = getPreferences()
            if pref.use_ground_hdri:
                ground_hdri_node = nodes.new(type="ShaderNodeGroup")
                ground_hdri_node.node_tree = getGroundHdriNodeGroup()
                links.new(mapping_node.outputs[0], ground_hdri_node.inputs[0])
                links.new(ground_hdri_node.outputs[0], texture_node.inputs[0])
            else:
                links.new(mapping_node.outputs[0], texture_node.inputs[0])

            texcoord_node = nodes.new(type="ShaderNodeTexCoord")
            links.new(texcoord_node.outputs[0], mapping_node.inputs[0])

        autoAlignNodes(world_output)

        return world
