# Copyright (c) 2019 Elie Michel
#
# This file is part of LilySurfaceScrapper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import os
import bpy
import enum
from mathutils import Vector
from pathlib import Path
from typing import List, Dict

def getCyclesImage(imgpath):
    """Avoid reloading an image that has already been loaded"""
    for img in bpy.data.images:
        if os.path.abspath(img.filepath) == os.path.abspath(imgpath):
            return img
    return bpy.data.images.load(imgpath)

def autoAlignNodes(root: bpy.types.Node):
    def makeTree(node):
        descendentCount = 0
        children : List[bpy.types.Node] = []
        for i in node.inputs:
            for l in i.links:
                subtree = makeTree(l.from_node)
                children.append(subtree)
                descendentCount += subtree[2] + 1
        return node, children, descendentCount

    tree = makeTree(root)

    def placeNodes(tree, rootLocation, xstep = 400, ystep = 170):
        # TODO The results still aren't ideal; especially texture nodes are sometimes placed completely off
        root, children, count = tree
        root.location = rootLocation
        childLoc = rootLocation + Vector((-xstep, ystep * count / 2.))
        acc = 0.25
        for child in children:
            print(child[0].name, acc)
            acc += (child[2]+1)/2.
            placeNodes(child, childLoc + Vector((0, -ystep * acc)))
            acc += (child[2]+1)/2.

    placeNodes(tree, Vector((0,0)))

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

def guessColorSpaceFromExtension(img: str) -> Dict[str, str]:
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

class appendableNodeGroups:
    """Use this as a wrapper for appendFromBlend to append
    one of the node groups included within node-groups.blend
    """
    __appended_node_groups = {}
    BLEND_FILE = Path(__path__).parent / "node-groups.blend"

    @property
    def randomize_tiles (self) -> bpy.types.ShaderNodeTree:
        (group := __appended_node_groups["Randomize Tile"])
        if group is None:
            group = appendFromBlend(BLEND_FILE, bpy.types.BlendDataNodeTrees , "Randomize Tiles")[0]
        return group

def appendFromBlend(filepath: Path, type: bpy.types.BlendData, names: List[str]) -> List[bpy.types.ID]:
    """Append a collection of objects from a specifc BlendData [1] type.
    This is done via `BlendDataLibraries` [2] instead of `bpy.ops.wm.append().`

    [1] https://docs.blender.org/api/current/bpy.types.BlendData.html?highlight=node_group#bpy.types.BlendData.node_groups \\
    [2] https://docs.blender.org/api/current/bpy.types.BlendDataLibraries.html?highlight=blenddatalibrary
    """

    with bpy.data.libraries.load(str(filepath)) as (data_from, data_to):
        
