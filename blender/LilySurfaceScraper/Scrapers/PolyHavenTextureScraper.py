# Copyright (c) 2019 - 2020 Elie Michel
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
# This file is part of LilySurfaceScraper, a Blender add-on to import materials
# from a single URL

from .AbstractScraper import AbstractScraper

import re
import requests
from collections import defaultdict

class PolyHavenTextureScraper(AbstractScraper):
    source_name = "Poly Haven Texture"
    home_url = "https://polyhaven.com/textures"

    # Translate TextureHaven map names into our internal map names
    maps_tr = {
        'albedo': 'baseColor',
        'col 1': 'baseColor',
        'col 01': 'baseColor',
        'col 2': 'baseColor_02',
        'col 02': 'baseColor_02',
        'col 3': 'baseColor_03',
        'col 03': 'baseColor_03',
        'diffuse': 'diffuse',
        'diff png': 'diffuse',
        'diff_png': 'diffuse',
        'normal': 'normal',
        'nor_gl': 'normal',
        'specular': 'specular',
        'spec': 'specular',
        'ref': 'specular',
        'roughness': 'roughness',
        'rough': 'roughness',
        'metallic': 'metallic',
        'metal': 'metallic',
        'ao': 'ambientOcclusion',
        'rough ao': 'ambientOcclusionRough',
        'rough_ao': 'ambientOcclusionRough',
        'displacement': 'height',
        'translucent': 'opacity',
    }

    polyHavenUrl = re.compile(r"(?:https:\/\/)?polyhaven\.com\/a\/([^\/]+)")

    @classmethod
    def getUid(cls, url):
        match = cls.polyHavenUrl.match(url)
        if match is not None:
            return match.group(1)
        return None

    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scraped by this scraper."""
        uid = cls.getUid(url)
        if uid is not None:
            req = requests.get(f"https://api.polyhaven.com/info/{uid}")
            return req.status_code == 200 and req.json()["type"] == 1  # 1 for textures
        return False
    
    def _fetchVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        html = self.fetchHtml(url)
        if html is None:
            return None

        identifier = self.getUid(url)

        api_url = f"https://api.polyhaven.com/files/{identifier}"
        data = self.fetchJson(api_url)
        if data is None:
            self.error = "API error"
            return None

        variant_data = defaultdict(dict)
        for map_type, maps in data.items():
            if map_type.lower() not in self.maps_tr.keys():
                continue
            for res, formats in maps.items():
                for fmt, map_data in formats.items():
                    variant_data[(res, fmt)][map_type] = map_data['url']

        variant_data = [(*k, v) for k, v in variant_data.items()]
        variant_data.sort(key=lambda x: self.sortTextWithNumbers(f"{x[0]} ({x[1]})"))
        variants = [f"{res} ({fmt})" for res, fmt, _ in variant_data]

        self._asset_name = identifier
        self._variant_data = variant_data
        self._variants = variants
        return variants
    
    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        identifier = self._asset_name
        variant_data = self._variant_data
        variants = self._variants
        
        if variant_index < 0 or variant_index >= len(variants):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False
        
        var_name = variants[variant_index]
        material_data.name = "texturehaven/" + identifier + '/' + var_name
        
        maps = variant_data[variant_index][2]

        for map_name, map_url in maps.items():
            map_name = map_name.lower()
            if map_name in self.maps_tr:
                map_name = self.maps_tr[map_name]
                material_data.maps[map_name] = self.fetchImage(map_url, material_data.name, map_name)
        
        return True
