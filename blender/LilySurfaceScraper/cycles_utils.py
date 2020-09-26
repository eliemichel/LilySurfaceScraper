# Copyright (c) 2019 - 2020 Elie Michel
#
# This file is part of LilySurfaceScraper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import os
from collections import OrderedDict
from itertools import repeat

import bpy
from mathutils import Vector

def getCyclesImage(imgpath):
    """Avoid reloading an image that has already been loaded"""
    for img in bpy.data.images:
        if os.path.abspath(img.filepath) == os.path.abspath(imgpath):
            return img
    return bpy.data.images.load(imgpath)

node_height = {
    'BSDF_PRINCIPLED': 571.0,
    'TEX_COORD': 231.0,
    'MAPPING': 348.0,
    'TEX_IMAGE': 251.0,
    'NORMAL_MAP': 151.0,
    'DISPLACEMENT': 168.0,
    'OUTPUT_MATERIAL': 117.0,
    ...: 150.0
}

def get_node_height(node):
    """Work around the fact that blender does not update
    dimensions.y for nodes that have just been created"""
    return node_height.get(node.type, node_height[...])

def nodes_arrange(nodelist, level, margin_x, margin_y, x_last):
    """Largely imported from NodeArrange add-on by JuhaW (GPL)
    https://github.com/JuhaW/NodeArrange"""
    parents = []
    for node in nodelist:
        parents.append(node.parent)
        node.parent = None

    widthmax = max([x.width for x in nodelist])
    xpos = x_last - (widthmax + margin_x) if level != 0 else 0
    
    y = 0

    for node in nodelist:

        if node.hide:
            hidey = (get_node_height(node) / 2) - 8
            y = y - hidey
        else:
            hidey = 0

        node.location.y = y
        y = y - margin_y - get_node_height(node) + hidey

        node.location.x = xpos

    y = y + margin_y

    for i, node in enumerate(nodelist):
        node.parent =  parents[i]

    return xpos

def autoAlignNodes(root, margin_x=100, margin_y=20):
    a = []
    a.append([root])

    level = 0

    while a[level]:
        a.append([])

        for node in a[level]:
            inputlist = [i for i in node.inputs if i.is_linked]

            if inputlist:
                for input in inputlist:
                    for nlinks in input.links:
                        node1 = nlinks.from_node
                        a[level + 1].append(node1)

        level += 1

    del a[level]
    level -= 1

    #remove duplicate nodes at the same level, first wins
    for x, nodes in enumerate(a):
        a[x] = list(OrderedDict(zip(a[x], repeat(None))))

    #remove duplicate nodes in all levels, last wins
    top = level
    for row1 in range(top, 1, -1):
        for col1 in a[row1]:
            for row2 in range(row1-1, 0, -1):
                for col2 in a[row2]:
                    if col1 == col2:
                        a[row2].remove(col2)
                        break

    ########################################

    level_count = level + 1
    x_last = 0
    for level in range(level_count):
        x_last = nodes_arrange(a[level], level, margin_x, margin_y, x_last)

class PrincipledWorldWrapper:
    """This is a wrapper similar in use to PrincipledBSDFWrapper (located in
    bpy_extras.node_shader_utils) but for use with worlds. This is required to
    avoid relying on node names, which depend on Blender's UI language settings
    (see issue #7) """

    def __init__(self, world):
        self.node_background = None
        self.node_out = None
        for n in world.node_tree.nodes:
            if self.node_background is None and n.type == "BACKGROUND":
                self.node_background = n
            elif self.node_out is None and n.type == "OUTPUT_WORLD":
                self.node_out = n

def guessColorSpaceFromExtension(img):
    """Guess the most appropriate color space from filename extension"""
    img = img.lower()
    if img.endswith(".jpg") or img.endswith(".jpeg") or img.endswith(".png"):
        return {
            "name": "sRGB",
            "old_name": "COLOR", # mostly for backward compatibility
        }
    else:
        return {
            "name": "Linear",
            "old_name": "NONE",
        }
