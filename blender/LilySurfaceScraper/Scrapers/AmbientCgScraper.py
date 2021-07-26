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

import zipfile
import os
import re
from urllib.parse import urlparse, parse_qs
from .AbstractScraper import AbstractScraper


class AmbientCgScraper(AbstractScraper):
    source_name = "ambientCG"
    home_url = "https://ambientcg.com"
    home_dir = "ambientCG"

    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scraped by this scraper."""
        return re.match(r"https:\/\/(?:www\.)?ambientcg\.com\/view(?:\.php)?\?(?:tex|id)=(.+)", url) is not None

    def getVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""

        query = parse_qs(urlparse(url).query)
        asset_id = query.get('id', query.get('tex', [None]))[0]
        api_url = f"https://ambientcg.com/api/v1/full_json?id={asset_id}"
        
        data = self.fetchJson(api_url)
        if data is None:
            return None
        
        variants_data = data["Assets"][asset_id]["Downloads"]
        variants = sorted(list(variants_data.keys()),
                          key=lambda x: self.sortTextWithNumbers(" ".join(x.split("-")[::-1])))
        variants_urls = [ variants_data[v]["RawDownloadLink"] for v in variants ]

        self.metadata.setCustom("variants_urls", variants_urls)
        self.metadata.name = asset_id
        self.metadata.setCustom("thumbnail_url", data["Assets"][asset_id]["PreviewSphere"]["512-PNG"])
        return variants

    def getThumbnail(self):
        return self.metadata.getCustom("thumbnail_url")

    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        variants = self.metadata.variants
        variants_urls = self.metadata.getCustom("variants_urls")

        if variant_index < 0 or variant_index >= len(variants):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False
        
        variant = variants[variant_index]
        zip_url = variants_urls[variant_index]

        material_data.name = f"{self.home_dir}/{self.metadata.name}/{variant}"
        zip_path = self.fetchZip(zip_url, material_data.name, "textures.zip")
        zip_dir = os.path.dirname(zip_path)
        if os.path.getsize(zip_path) == 0:
            # maps already exist
            namelist = os.listdir(zip_dir)
        else:
            with zipfile.ZipFile(zip_path,"r") as zip_ref:
                namelist = zip_ref.namelist()
                zip_ref.extractall(zip_dir)
            # wipe zip to leave only a 0-sized file:
            open(zip_path, 'wb').close()
        
        # Translate cc0textures map names into our internal map names
        maps_tr = {
            # Names of the old website
            'col': 'baseColor',
            'nrm': 'normalInvertedY',
            'mask': 'opacity',
            'rgh': 'roughness',
            'met': 'metallic',
            'AO': 'ambientOcclusion',
            'disp': 'height',
            # New names
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
            map_type = base.split('_')[-1]
            if map_type in maps_tr:
                map_name = maps_tr[map_type]
                material_data.maps[map_name] = os.path.join(zip_dir, name)
        return True
