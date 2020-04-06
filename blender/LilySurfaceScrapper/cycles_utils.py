# Copyright (c) 2019 Elie Michel
#
# This file is part of LilySurfaceScrapper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import os
import bpy
import enum
import re
from mathutils import Vector
from pathlib import Path
from typing import List, Dict, Union, Iterable, Optional

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
    BLEND_FILE = Path(__file__).parent / "node-groups.blend"

    @property
    def randomize_tiles (self) -> bpy.types.ShaderNodeTree:
        # TODO Refactor with walrus operator once Blender ships with Python 3.8 (oh god, they'll support Blender 2.83 until end of next year)
        if __appended_node_groups["Randomize Tile"] is None:
            __appended_node_groups["Randomize Tile"] = appendFromBlend(BLEND_FILE, bpy.types.BlendData.node_groups , "Randomize Tiles")[0]
        return __appended_node_groups["Randomize Tile"]


def appendFromBlend(filepath: Path, name: Optional[Union[Iterable[str], str]] = None, datatype: Optional[str] = None) -> List[bpy.types.ID]:
    """Append stuff from a given blend file at file path. You could for example
    append all node_groups, Object "Suzanne" and "Cube", or everything in the file.
    Already existing data in your file will not get overwritten, Blender will but a `.001`
    at the end of the appended asset in that case.

    If `name = None`, everything will be appended.
    To improve performance you can specify for which datatype[1] you are looking for. \\
    This function is a wrapper for `BlendDataLibraries`[2], so it's not using `bpy.ops.wm.append().`

    [1] https://docs.blender.org/api/current/bpy.types.BlendData.html \\
    [2] https://docs.blender.org/api/current/bpy.types.BlendDataLibraries.html?highlight=blenddatalibrary
    """

    # TODO Actually return the imported assets (convenience)

    # Sanitize datatype
    if "." in datatype: # bpy.types.BlendData.node_groups to node_groups
        datatype = datatype.rsplit(".", 1)[0].replace("BlendData", "", 1)
    if datatype.startswith("BlendData"): # BlendDataLattices to lattices
        datatype = re.sub('(?!^)([A-Z]+)', r'_\1', datatype.replace("BlendData", "", 0)).lower()
    
    with bpy.data.libraries.load(str(filepath), link = False) as (data_from, data_to):
        def append(datatype):
            if name:
                setattr(data_to, datatype, [name] if isinstance(name, str) else name)
            else:
                setattr(data_to, attr, getattr(data_from, attr))

        if datatype:
            append(datatype)
        else:
            for attr in dir(data_from):
                append(attr)
