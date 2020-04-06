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
        # Initialize variables
        mat : bpy.types.Material = bpy.data.materials.new(name=self.name)
        mat.use_nodes = True
        group : bpy.types.ShaderNodeTree = bpy.data.node_groups.new(self.name, "ShaderNodeTree")
        group.inputs.new("NodeSocketVector", "UV")
        mat_nodes = mat.node_tree.nodes
        mat_links = mat.node_tree.links
        nodes = group.nodes
        links = group.links
        front = {}
        back = {}

        # Setup nodes
        principled_mat = PrincipledBSDFWrapper(mat, is_readonly=False)
        principled : bpy.types.ShaderNodeBsdfPrincipled = principled_mat.node_principled_bsdf
        mat_output : bpy.types.ShaderNodeOutputMaterial = principled_mat.node_out
        group_inputs : bpy.types.NodeGroupInput = nodes.new("NodeGroupInput")
        group_outputs : bpy.types.NodeGroupOutput = nodes.new("NodeGroupOutput")
        texgroup : bpy.types.ShaderNodeGroup = mat_nodes.new("ShaderNodeGroup")
        texgroup.node_tree = group
        texcoords : bpy.types.ShaderNodeTexCoord = principled_mat.node_texcoords
        mat_links.new(texcoords.outputs["UV"], texgroup.inputs["UV"])

        # Create all of the texture nodes
        for map_name, img in self.maps.items():
            if img is None or map_name.split("_")[0] not in __class__.input_tr:
                continue
            
            texture_node : bpy.types.ShaderNodeTexImage = nodes.new(type="ShaderNodeTexImage")
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

        def export(name: str, output : bpy.types.NodeSocket, input : bpy.types.NodeSocket):
            """Creates a link between an output socket from
            inside the node group to a socket input on the material.
            """
            name = name.capitalize()
            group.outputs.new(output.bl_idname, name)
            links.new(output, group_outputs.inputs[name])
            mat_links.new(texgroup.outputs[name], input)

        def setup(name: str, node: bpy.types.ShaderNodeTexImage):
            """Creates a texture setup for the node and connects it with the principled
            shader on the material.

            If you want to add a node setup for a new map type, you'd do that here.
            """
            links.new(group_inputs.outputs["UV"], node.inputs["Vector"])
            if __class__.input_tr.get(name): # Is there a socket on the Pricipled BSDF with that name?
                export(name, node.outputs["Color"], principled.inputs[__class__.input_tr[name]])
            else:
                if name == "glossiness":
                    invert_node = nodes.new(type="ShaderNodeInvert")
                    links.new(node.outputs["Color"], invert_node.inputs["Color"])
                    export(name, invert_node.outputs["Color"], principled.inputs["Roughness"])
                if name == "diffuse":
                    if not principled.inputs["Base Color"].is_linked:
                        export(name, node.outputs["Color"], principled.inputs["Base Color"])
                elif name == "height":
                    displacement_node = mat_nodes.new(type="ShaderNodeDisplacement")
                    displacement_node.inputs[2].default_value = .2
                    export(name, node.outputs["Color"], displacement_node.inputs["Height"])
                    mat_links.new(displacement_node.outputs["Displacement"], mat_output.inputs[2])
                elif name == "normal":
                    normal_node = nodes.new(type="ShaderNodeNormalMap")
                    links.new(node.outputs["Color"], normal_node.inputs["Color"])
                    export(name, normal_node.outputs["Normal"], principled.inputs["Normal"])
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
                    export("normal", normal_node.outputs["Normal"], principled.inputs["Normal"])

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
        
        autoAlignNodes(group_outputs)
        autoAlignNodes(mat_output)

        return mat
