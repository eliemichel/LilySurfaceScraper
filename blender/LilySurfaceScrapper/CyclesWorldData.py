# Copyright (c) 2019 Elie Michel
#
# This file is part of LilySurfaceScrapper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import bpy

from .WorldData import WorldData
from .cycles_utils import (
    getCyclesImage, autoAlignNodes,
    PrincipledWorldWrapper, guessColorSpaceFromExtension
)

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
            texcoords = nodes.new("ShaderNodeTexCoord")
            mapping = nodes.new("ShaderNodeMapping")
            texture_node.image = getCyclesImage(img)
            color_space = guessColorSpaceFromExtension(img)
            print("guessColorSpaceFromExtension(%s): " % (img,))
            print(color_space)
            texture_node.image.colorspace_settings.name = color_space["name"]
            if hasattr(texture_node, "color_space"):
                texture_node.color_space = color_space["old_name"]
            print(texture_node.image.colorspace_settings.name)
            links.new(texture_node.outputs["Color"], background.inputs["Color"])
            links.new(mapping.outputs["Vector"], texture_node.inputs["Vector"])
            links.new(texcoords.outputs["Generated"], mapping.inputs["Vector"])

        autoAlignNodes(world_output)

        return world
