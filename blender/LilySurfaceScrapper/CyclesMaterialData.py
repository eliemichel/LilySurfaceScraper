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
        'roughness': 'Roughness',
        'metallic': 'Metallic',
        'specular': 'Specular',
        'opacity': 'Alpha',
        'emission': 'Emission',
        'diffuse': '',
        'normal': '',
        'normalInvertedY': '',
        'height': '',
        'ambientOcclusion': '', # FIXME Handle this better https://github.com/KhronosGroup/glTF-Blender-IO/issues/123
        'ambientOcclusionRough': '', # TODO Do something with this
        'glossiness': '',
    }

    def loadImages(self):
        """This is not needed by createMaterial, but is called when
        create_material is false to load images anyway"""
        for map_name, img in self.maps.items():
            if img is None or map_name.split("_")[0] not in __class__.input_tr:
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
        texcoords = principled_mat.node_texcoords
        principled_mat.roughness = 1.0
        front = {}
        back = {}

        # Create all of the texture nodes
        for map_name, img in self.maps.items():
            if img is None or map_name.split("_")[0] not in __class__.input_tr:
                continue
            
            texture_node = nodes.new(type="ShaderNodeTexImage")
            if map_name.endswith("_back"):
                map_name = map_name[:-5] # remove "_back"
                back[map_name] = texture_node
            else:
                front[map_name] = texture_node
            
            texture_node.image = getCyclesImage(img)
            texture_node.image.colorspace_settings.name = "sRGB" if map_name == "baseColor" or map_name == "diffuse" else "Non-Color"
            if hasattr(texture_node, "color_space"):
                texture_node.color_space = "COLOR" if map_name == "baseColor" or map_name == "diffuse" else "NONE"
            if map_name == "opacity":
                mat.blend_method = 'BLEND'
            if map_name == "height":
                mat.cycles.displacement_method = 'BOTH'

        if not front: # In case just the backside texture was chosen
            front = back
            back = {}

        def setup(name, node):
            links.new(texcoords.outputs["UV"], node.inputs["Vector"])
            if __class__.input_tr.get(name):
                links.new(node.outputs["Color"], principled.inputs[__class__.input_tr[name]])
            else:
                if name == "glossiness":
                    invert_node = nodes.new(type="ShaderNodeInvert")
                    links.new(node.outputs["Color"], invert_node.inputs["Color"])
                    links.new(invert_node.outputs["Color"], principled.inputs["Roughness"])
                if name == "diffuse":
                    if not principled.inputs["Base Color"].is_linked:
                        links.new(node.outputs["Color"], principled.inputs["Base Color"])
                elif name == "height":
                    displacement_node = nodes.new(type="ShaderNodeDisplacement")
                    displacement_node.inputs[2].default_value = .2
                    links.new(node.outputs["Color"], displacement_node.inputs["Height"])
                    links.new(displacement_node.outputs["Displacement"], mat_output.inputs[2])
                elif name == "normal":
                    normal_node = nodes.new(type="ShaderNodeNormalMap")
                    links.new(node.outputs["Color"], normal_node.inputs["Color"])
                    links.new(normal_node.outputs["Normal"], principled.inputs["Normal"])
                elif name == "normalInvertedY":
                    normal_node = nodes.new(type="ShaderNodeNormalMap")
                    separate_node = nodes.new(type="ShaderNodeSeparateRGB")
                    combine_node = nodes.new(type="ShaderNodeCombineRGB")
                    math_node = nodes.new(type="ShaderNodeMath")
                    math_node.operation = "MULTIPLY_ADD"
                    math_node.inputs[1].default_value = -1
                    math_node.inputs[2].default_value = 1

                    links.new(node.outputs["Color"], separate_node.inputs["Image"])
                    
                    links.new(separate_node.outputs["R"], combine_node.inputs[0])
                    links.new(separate_node.outputs["G"], math_node.inputs[0])
                    links.new(math_node.outputs["Value"], combine_node.inputs[1])
                    links.new(separate_node.outputs["B"], combine_node.inputs[2])

                    links.new(combine_node.outputs["Image"], normal_node.inputs["Color"])
                    links.new(normal_node.outputs["Normal"], principled.inputs["Normal"])

        if not back: # If there is no item in the back dictionary
            [setup(name, node) for name, node in front.items()]
        else:
            geometry_node = nodes.new("ShaderNodeNewGeometry")
            def pre_setup(name, front, back, mix):
                links.new(geometry_node.outputs["Backfacing"], mix.inputs[0])
                links.new(front.outputs["Color"], mix.inputs[1])
                links.new(back.outputs["Color"], mix.inputs[2])
                setup(name, mix)
            for name, node in front.items():
                if back.get(name):
                    pre_setup(name, node, back[name], nodes.new(type="ShaderNodeMixRGB"))
        
        autoAlignNodes(mat_output)

        return mat
