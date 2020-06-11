# Copyright (c) 2019-2020 Elie Michel
#
# This file is part of LilySurfaceScrapper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import bpy
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper
from .MaterialData import MaterialData
from .cycles_utils import getCyclesImage, autoAlignNodes
from .preferences import getPreferences

def listAvailableColorSpaces(image):
    # Warning: hack ahead
    try:
        image.colorspace_settings.name = ''
    except TypeError as e:
        s = str(e)
    return eval(s[s.find('('):])

def findColorSpace(image, key):
    """This is important for custom OCIO config"""
    availableColorSpaces = listAvailableColorSpaces(image)
    if key in availableColorSpaces:
        return key
    for cs in availableColorSpaces:
        if key in cs:
            return cs
    return availableColorSpaces[0]

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

    def getGraph(self):
        return self.material.node_tree.nodes, self.material.node_tree.links

    def initMaterial(self):
        """Create the empty material at the core Principled Node"""
        self.material = bpy.data.materials.new(name=self.name)
        self.material.use_nodes = True
        principled_mat = PrincipledBSDFWrapper(self.material, is_readonly=False)
        principled_mat.roughness = 1.0
        self.principled_node = principled_mat.node_principled_bsdf
        self.mat_output = principled_mat.node_out

    def makeTextureNode(self, img, map_name):
        nodes, links = self.getGraph()
        if self.mapping_node is None:
            texcoord_node = nodes.new(type="ShaderNodeTexCoord")
            self.mapping_node = nodes.new(type="ShaderNodeMapping")
            links.new(texcoord_node.outputs["UV"], self.mapping_node.inputs["Vector"])

        texture_node = nodes.new(type="ShaderNodeTexImage")
        texture_node.image = getCyclesImage(img)

        links.new(self.mapping_node.outputs[0], texture_node.inputs["Vector"])

        baseColorSpace = findColorSpace(texture_node.image, 'sRGB')
        nonColorSpace = findColorSpace(texture_node.image, 'Non-Color')

        texture_node.image.colorspace_settings.name = baseColorSpace if map_name == "baseColor" or map_name == "diffuse" else nonColorSpace
        if hasattr(texture_node, "color_space"):
            texture_node.color_space = "COLOR" if map_name == "baseColor" or map_name == "diffuse" else "NONE"
        if map_name == "opacity":
            self.material.blend_method = 'BLEND'
        if map_name == "height":
            self.material.cycles.displacement_method = 'BOTH'
        
        # Save the texture in either the front or back texture dict
        if map_name.endswith("_back"):
            map_name = map_name[:-5] # remove "_back"
            self.back[map_name] = texture_node
        else:
            self.front[map_name] = texture_node

    def mixFrontBack(self, front_node, back_node):
        """Mix front and back node in the case of two-sided materials"""
        nodes, links = self.getGraph()
        if self.geometry_node is None:
            self.geometry_node = nodes.new("ShaderNodeNewGeometry")
        mix_node = nodes.new(type="ShaderNodeMixRGB")
        links.new(self.geometry_node.outputs["Backfacing"], mix_node.inputs[0])
        links.new(front_node.outputs["Color"], mix_node.inputs[1])
        links.new(back_node.outputs["Color"], mix_node.inputs[2])
        return mix_node

    def mixFrontBackDicts(self):
        """A step of createMaterial, create mix nodes to merge self.front and self.back"""
        mixed = {}
        if not self.back:
            mixed = self.front
        elif not self.front:
            mixed = self.back
        else:
            for name, node in self.front.items():
                if name in self.back:
                    mixed[name] = self.mixFrontBack(node, self.back[name])
                else:
                    mixed[name] = node
        return mixed

    def createMaterial(self):
        self.initMaterial()
        self.front = {}
        self.back = {}
        self.geometry_node = None
        self.mapping_node = None
        nodes, links = self.getGraph()

        # Create all of the texture nodes
        for map_name, img in self.maps.items():
            if img is None or map_name.split("_")[0] not in __class__.input_tr:
                continue
            
            self.makeTextureNode(img, map_name)

        mixed = self.mixFrontBackDicts()

        for name, node in mixed.items():
            if __class__.input_tr.get(name):
                links.new(node.outputs["Color"], self.principled_node.inputs[__class__.input_tr[name]])
            else:
                if name == "glossiness":
                    invert_node = nodes.new(type="ShaderNodeInvert")
                    links.new(node.outputs["Color"], invert_node.inputs["Color"])
                    links.new(invert_node.outputs["Color"], self.principled_node.inputs["Roughness"])
                if name == "diffuse":
                    if not self.principled_node.inputs["Base Color"].is_linked:
                        links.new(node.outputs["Color"], self.principled_node.inputs["Base Color"])
                elif name == "height":
                    displacement_node = nodes.new(type="ShaderNodeDisplacement")
                    displacement_node.inputs[2].default_value = .2
                    links.new(node.outputs["Color"], displacement_node.inputs["Height"])
                    links.new(displacement_node.outputs["Displacement"], self.mat_output.inputs[2])
                elif name == "normal":
                    normal_node = nodes.new(type="ShaderNodeNormalMap")
                    links.new(node.outputs["Color"], normal_node.inputs["Color"])
                    links.new(normal_node.outputs["Normal"], self.principled_node.inputs["Normal"])
                elif name == "normalInvertedY":
                    normal_node = nodes.new(type="ShaderNodeNormalMap")
                    separate_node = nodes.new(type="ShaderNodeSeparateRGB")
                    combine_node = nodes.new(type="ShaderNodeCombineRGB")
                    math_node = nodes.new(type="ShaderNodeMath")
                    math_node.operation = "SUBTRACT"
                    math_node.inputs[0].default_value = 1

                    links.new(node.outputs["Color"], separate_node.inputs["Image"])
                    
                    links.new(separate_node.outputs["R"], combine_node.inputs[0])
                    links.new(separate_node.outputs["G"], math_node.inputs[1])
                    links.new(math_node.outputs["Value"], combine_node.inputs[1])
                    links.new(separate_node.outputs["B"], combine_node.inputs[2])

                    links.new(combine_node.outputs["Image"], normal_node.inputs["Color"])
                    links.new(normal_node.outputs["Normal"], self.principled_node.inputs["Normal"])

        # Second pass, inserting AO requires that everything else (base color) is wired
        pref = getPreferences()
        if pref.use_ao:
            for name, node in mixed.items():
                if name == "ambientOcclusion":
                    basecolor_links = self.principled_node.inputs["Base Color"].links
                    if len(basecolor_links) == 0:
                        continue
                    base_color_output = basecolor_links[0].from_socket
                    mix_node = nodes.new(type="ShaderNodeMixRGB")
                    mix_node.blend_type = 'MULTIPLY'
                    links.new(base_color_output, mix_node.inputs[1])
                    links.new(node.outputs["Color"], mix_node.inputs[2])
                    links.new(mix_node.outputs["Color"], self.principled_node.inputs["Base Color"])

        autoAlignNodes(self.mat_output)

        return self.material
