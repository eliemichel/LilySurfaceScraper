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
        light = bpy.context.object.data

        light.use_nodes = True
        light.type = "POINT"
        light.shadow_soft_size = 0

        nodes = light.node_tree.nodes
        links = light.node_tree.links

        nodes.clear()

        ies = self.maps['ies']
        energyPath = self.maps['energy']
        with open(energyPath, "r") as f:
            energy = float(f.read())

        out = nodes.new(type="ShaderNodeOutputLight")
        emmision = nodes.new(type="ShaderNodeEmission")
        links.new(out.inputs['Surface'], emmision.outputs['Emission'])

        iesNode = nodes.new(type="ShaderNodeTexIES")
        if pref.ies_pack_files:
            bpy.ops.text.open(filepath=ies, internal=False)
            name = os.path.basename(ies)
            iesNode.ies = bpy.data.texts[name]
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
