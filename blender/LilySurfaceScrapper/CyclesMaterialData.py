# Copyright (c) 2019 Elie Michel
#
# This file is part of LilySurfaceScrapper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

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
        'opacity': 'Alpha',
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
            elif map_name == "normal":
                normal_node = nodes.new(type="ShaderNodeNormalMap")
                links.new(texture_node.outputs["Color"], normal_node.inputs["Color"])
                links.new(normal_node.outputs["Normal"], principled.inputs["Normal"])
            else:
                links.new(texture_node.outputs["Color"], principled.inputs[__class__.input_tr[map_name]])

            if map_name == "opacity":
                mat.blend_method = 'BLEND'

        autoAlignNodes(mat_output)

        return mat
