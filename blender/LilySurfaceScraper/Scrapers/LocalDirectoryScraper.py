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

import os
from .AbstractScraper import AbstractScraper


class LocalDirectoryScraper(AbstractScraper):
    """
    This scraper does not actually scrap a website, it links textures from a
    local directory, trying to guess the meaning of textures from their names.
    """
    source_name = "Local Directory"
    scraped_type = {'MATERIAL', "WORLD", "LIGHT"}
    home_url = None
    show_preview = False

    _texture_cache = None

    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scraped by this scraper."""
        return os.path.isdir(url) or os.path.isfile(url)

    def fetchVariantList(self, path):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        # if asked not to check for subfolders then just return the path given
        if not self.metadata.deep_check:
            variants = [path]
            self.metadata.variants = variants

        # check for sub items
        elif self.metadata.scrape_type == "WORLD":
            dirs = [os.path.splitext(os.path.join(path, i)) for i in os.listdir(path)]
            self.metadata.variants = ["".join(i) for i in dirs if i[1].lower() in [".hdr", ".exr", ".hdri"]]
            variants = [os.path.basename(i) for i in self.metadata.variants]

        elif self.metadata.scrape_type == "MATERIAL":
            files = [os.path.join(path, i) for i in os.listdir(path)]
            self.metadata.variants = [i for i in files if os.path.isdir(i)]
            variants = [os.path.basename(i) for i in self.metadata.variants]

        elif self.metadata.scrape_type == "LIGHT":
            files = [os.path.splitext(os.path.join(path, i)) for i in os.listdir(path)]
            self.metadata.variants = ["".join(i) for i in files if i[1].lower() in [".ies"]]
            variants = [os.path.basename(i) for i in self.metadata.variants]

        else:
            variants = []

        return variants

    def fetchVariant(self, variant_index, material_data):
        scrape_type = self.metadata.scrape_type
        variant = self.metadata.variants[variant_index]
        basedir = os.path.dirname(variant)
        material_data.name = f"{os.path.basename(basedir)}/{os.path.basename(variant)}"
        if self.metadata.deep_check:
            material_data.name = f"{os.path.basename(os.path.dirname(basedir))}/{material_data.name}"

        if scrape_type == "MATERIAL":
            namelist = [f for f in os.listdir(variant) if os.path.isfile(os.path.join(variant, f))]

            # TODO: Find a more exhaustive list of perfix/suffix
            maps_tr = {
                'baseColor': 'baseColor',
                'metallic': 'metallic',
                'height': 'height',
                'normalInvertedY': 'normalInvertedY',
                'opacity': 'opacity',
                'roughness': 'roughness',
                'ambientOcclusion': 'ambientOcclusion',
                'normal': 'normal',

                'Base Color': 'baseColor',
                'diffuse': 'diffuse',
                'Metallic': 'metallic',
                'Height': 'height',
                'col': 'baseColor',
                'nrm': 'normalInvertedY',
                'mask': 'opacity',
                'rgh': 'roughness',
                'met': 'metallic',
                'AO': 'ambientOcclusion',
                'disp': 'height',
                'Color': 'baseColor',
                'Normal': 'normalInvertedY',
                'Opacity': 'opacity',
                'Roughness': 'roughness',
                'Metalness': 'metallic',
                'AmbientOcclusion': 'ambientOcclusion',
                'Displacement': 'height'
            }
            for name in namelist:
                base = os.path.splitext(name)[0]
                for k, map_name in maps_tr.items():
                    if k in base:
                        map_name = maps_tr[k]
                        material_data.maps[map_name] = os.path.join(variant, name)
            return True
        elif scrape_type == "WORLD":
            if not os.path.isfile(variant):
                print("Not a world file")
                return False
            print(variant)
            material_data.maps['sky'] = variant
            return True
        else:
            if not os.path.isfile(variant):
                print("Not an IES file")
                return False
            material_data.maps["ies"] = variant
            material_data.maps["energy"] = 1
            return True
