# Copyright (c) 2020 Zivoy and Elie Michel
#
# This file is part of LilySurfaceScraper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import bpy

from .LightData import LightData
from .cycles_utils import autoAlignNodes
from .preferences import getPreferences
import os


class CyclesLightData(LightData):
    def createLights(self):
        pref = getPreferences()

        light = bpy.data.lights.new(self.name, "POINT")
        bpy.context.object.data = light

        light.use_nodes = True
        light.shadow_soft_size = 0

        tree = light.node_tree
        nodes = tree.nodes
        links = tree.links

        nodes.clear()

        ies = self.maps['ies']
        energy = self.maps['energy']

        out = nodes.new(type="ShaderNodeOutputLight")
        emmision = nodes.new(type="ShaderNodeEmission")
        links.new(out.inputs['Surface'], emmision.outputs['Emission'])

        iesNode = nodes.new(type="ShaderNodeTexIES")
        if pref.ies_pack_files:
            bpy.ops.text.open(filepath=ies, internal=False)
            iesNode.ies = bpy.data.texts[os.path.basename(ies)]
        else:
            iesNode.mode = "EXTERNAL"
            iesNode.filepath = ies
        links.new(iesNode.outputs['Fac'], emmision.inputs["Strength"])

        if pref.ies_use_strength:
            if pref.ies_light_strength:
                value = nodes.new(type="ShaderNodeValue")
                value.outputs['Value'].default_value = energy
                links.new(value.outputs["Value"], iesNode.inputs["Strength"])
            else:
                light.energy = energy

        autoAlignNodes(out)

        return light
