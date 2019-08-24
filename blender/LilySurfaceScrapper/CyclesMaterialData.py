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
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper

from .MaterialData import MaterialData
from .cycles_utils import getCyclesImage, autoAlignNodes

class CyclesMaterialData(MaterialData):
    # Translate our internal map names into cycles principled inputs
    input_tr = {
        'baseColor': 'Base Color',
        'normal': 'Normal',
        'roughness': 'Roughness',
        'metallic': 'Metallic',
        'specular': 'Specular',
        'opacity': '<custom>',
    }

    def loadImages(self):
        """This is not needed by createMaterial, but is called when
        create_material is false to load images anyway"""
        for map_name, img in self.maps.items():
            if img is None or map_name not in __class__.input_tr:
                continue
            getCyclesImage(img)

    def createMaterial(self):
        mat = bpy.data.materials.new(name=self.name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        principled_mat = PrincipledBSDFWrapper(mat, is_readonly=False)
        principled = principled_mat.node_principled_bsdf
        mat_output = principled_mat.node_out
        principled_mat.roughness = 1.0

        for map_name, img in self.maps.items():
            if img is None or map_name not in __class__.input_tr:
                continue
            texture_node = nodes.new(type="ShaderNodeTexImage")
            texture_node.image = getCyclesImage(img)
            texture_node.image.colorspace_settings.name = "sRGB" if map_name == "baseColor" else "Non-Color"
            if hasattr(texture_node, "color_space"):
                texture_node.color_space = "COLOR" if map_name == "baseColor" else "NONE"
            if map_name == "opacity":
                transparence_node = nodes.new(type="ShaderNodeBsdfTransparent")
                mix_node = nodes.new(type="ShaderNodeMixShader")
                links.new(texture_node.outputs["Color"], mix_node.inputs[0])
                links.new(transparence_node.outputs[0], mix_node.inputs[1])
                links.new(principled.outputs[0], mix_node.inputs[2])
                links.new(mix_node.outputs[0], mat_output.inputs[0])
            elif map_name == "normal":
                normal_node = nodes.new(type="ShaderNodeNormalMap")
                links.new(texture_node.outputs["Color"], normal_node.inputs["Color"])
                links.new(normal_node.outputs["Normal"], principled.inputs["Normal"])
            else:
                links.new(texture_node.outputs["Color"], principled.inputs[__class__.input_tr[map_name]])

        autoAlignNodes(mat_output)

        return mat
