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

import zipfile
import os
from .AbstractScrapper import AbstractScrapper

class Cc0texturesScrapper(AbstractScrapper):
    _texture_cache = None

    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scrapped by this scrapper."""
        return url.startswith("https://cc0textures.com/view.php?tex=")
    
    def fetchVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        if Cc0texturesScrapper._texture_cache is None:
            Cc0texturesScrapper._texture_cache = self.fetchXml("https://cc0textures.com/api/getDownloadLinks.php")

        root = Cc0texturesScrapper._texture_cache

        texture = root.find(f"assets/item[link='{url}']")

        if texture is None:
            return None

        self._texture = texture
        self._variants = list(filter(lambda v: v.attrib["res"] in ['1', '2', '4', '8'], texture.findall("downloads-pretty/download")))
        return list(map(lambda v: v.attrib["res"], self._variants))
    
    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        texture = self._texture
        variants = self._variants

        if variant_index < 0 or variant_index >= len(variants):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False
        
        variant = variants[variant_index]

        material_data.name = "CC0Textures/" + texture.find("title").text + "/" + variant.attrib["res"]
        zip_url = variant.text
        zip_path = self.fetchZip(zip_url, material_data.name, "textures.zip")
        zip_dir = os.path.dirname(zip_path)
        namelist = []
        with zipfile.ZipFile(zip_path,"r") as zip_ref:
            namelist = zip_ref.namelist()
            zip_ref.extractall(zip_dir)
        
        # Translate cc0textures map names into our internal map names
        maps_tr = {
            'col': 'baseColor',
            'nrm': 'normal',
            'mask': 'opacity',
            'rgh': 'roughness',
            'met': 'metallic',
        }
        for name in namelist:
            base = os.path.splitext(name)[0]
            map_type = base.split('_')[-1]
            if map_type in maps_tr:
                map_name = maps_tr[map_type]
                material_data.maps[map_name] = os.path.join(zip_dir, name)
        return True
