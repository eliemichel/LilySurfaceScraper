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

from .PolyHavenAbstractScraper import PolyHavenAbstract


class TextureHavenScraper(PolyHavenAbstract):
    source_name = "Poly Haven Textures"
    home_url = "https://polyhaven.com/textures"
    target = 1
    
    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        json = self._json
        variants = self._variants
        
        if variant_index < 0 or variant_index >= len(variants):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False
        
        base_name = self._id
        var_name = variants[variant_index]
        material_data.name = "texturehaven/" + base_name + '/' + var_name

        # Translate TextureHaven map names into our internal map names
        maps_tr = {
            'Diffuse': 'diffuse',
            'nor_gl': 'normal',
            'Rough': 'roughness',
            'AO': 'ambientOcclusion',
            'Displacement': 'height',
            'spec': 'specular',
            'Metal': 'metallic',
            'rough_ao': 'ambientOcclusionRough',
            "translucent": "opacity",
            'col1': 'baseColor',
            'col_01': 'baseColor',
            'col_1': 'baseColor',
            'coll1': 'baseColor',
            'col2': 'baseColor_02',
            'col_02': 'baseColor_02',
            'col_2': 'baseColor_02',
            'coll2': 'baseColor_02',
            'col_03': 'baseColor_03',
            "ref": 'specular',
            'diff_png': 'diffuse',
            "rough_diff": "diffuseRough",
            # "Bump": "",
            # "arm": "",  # AO/Rough/Metal todo probably make use of this
            # "diff_polar": "",
            # "rough_polar": "",
            # "nor_polar": "",
            # "page": "",  # only in 1 thing (book_pattern)
            # "normal_gl": "",
        }
        for m in json.keys():
            if m in maps_tr:
                map_name = maps_tr[m]
                map = json[m]
                ext = "png"  # "jpg"
                # prefer exr for normal maps
                if map_name == "normal":
                    ext = "exr"
                map_url = map[var_name][ext]["url"]
                material_data.maps[map_name] = self.fetchImage(map_url, material_data.name, map_name)
        return True
