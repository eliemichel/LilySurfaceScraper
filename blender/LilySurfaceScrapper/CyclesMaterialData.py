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

from .MaterialData import MaterialData
from cycles_utils import getCyclesImage, autoAlignNodes

class CyclesMaterialData(MaterialData):
    def createMaterial(self):
        mat = bpy.data.materials.new(name=self.name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        principled = nodes["Principled BSDF"]
        mat_output = nodes["Material Output"]
        principled.inputs["Roughness"].default_value = 1.0
        # Translate our internal map names into cycles principled inputs
        input_tr = {
            'baseColor': 'Base Color',
            'normal': 'Normal',
            'roughness': 'Roughness',
            'metallic': 'Metallic',
            'specular': 'Specular',
            'opacity': '<custom>',
        }
        for input, img in self.maps.items():
            if img is None or input not in input_tr:
                continue
            texture_node = nodes.new(type="ShaderNodeTexImage")
            texture_node.image = getCyclesImage(img)
            texture_node.color_space = 'COLOR' if input == 'baseColor' else 'NONE'
            if input == 'opacity':
                transparence_node = nodes.new(type="ShaderNodeBsdfTransparent")
                mix_node = nodes.new(type="ShaderNodeMixShader")
                links.new(texture_node.outputs[0], mix_node.inputs[0])
                links.new(transparence_node.outputs[0], mix_node.inputs[1])
                links.new(principled.outputs[0], mix_node.inputs[2])
                links.new(mix_node.outputs[0], mat_output.inputs[0])
            elif input == "normal":
                normal_node = nodes.new(type="ShaderNodeNormalMap")
                links.new(texture_node.outputs["Color"], normal_node.inputs["Color"])
                links.new(normal_node.outputs["Normal"], principled.inputs["Normal"])
            else:
                links.new(texture_node.outputs[0], principled.inputs[input_tr[input]])

        autoAlignNodes(mat_output)

        return mat
