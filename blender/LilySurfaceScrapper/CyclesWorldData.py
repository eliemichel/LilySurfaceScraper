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

import bpy

from .WorldData import WorldData
from cycles_utils import getCyclesImage

class CyclesWorldData(WorldData):
    def createWorld(self):
        world = bpy.data.worlds.new(name=self.name)
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        background = nodes["Background"]
        world_output = nodes["World Output"]
        background.inputs["Roughness"].default_value = 1.0

        img = self.maps['sky']
        if img is not None:
            texture_node = nodes.new(type="ShaderNodeTexEnvironment")
            texture_node.image = getCyclesImage(img)
            texture_node.color_space = 'COLOR'
            links.new(texture_node.outputs["Color"], background.inputs["Color"])
        
        autoAlignNodes(world_output)

        return world
