# Copyright (c) 2019 - 2021 Elie Michel
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

import zipfile
import os
from urllib.parse import urlparse

class CgbookcaseScraper(AbstractScraper):
    source_name = "cgbookcase.com"
    home_url = "https://www.cgbookcase.com/textures/"
    home_dir = "cgbookcase"

    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scraped by this scraper."""
        return "cgbookcase.com/textures/" in url
    
    def getVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        html = self.fetchHtml(url)
        if html is None:
            return None

        parsed_url = urlparse(url)
        identifier = parsed_url.path.strip('/').split('/')[-1]
        api_url = f"https://www.cgbookcase.com/textures/{identifier}/LilySurfaceScraper.json"

        data = self.fetchJson(api_url)

        resolutions = sorted(data['files'].keys(), key=lambda x: x.zfill(3))

        if data["doublesided"]:
            variants = (
                [ x + " (double-sided)" for x in resolutions ] +
                [ x + " (front only)"   for x in resolutions ] +
                [ x + " (back only)"    for x in resolutions ]
            )
        else:
            variants = resolutions
        
        self.asset_name = data['title']
        self._id = identifier
        self._variants = variants
        self._resolutions = resolutions
        self._data = data
        self._doublesided = data['doublesided']
        return variants

    def getThumbnail(self, _):
        parse = self.fetchHtml(f"https://www.cgbookcase.com/textures/{self._id}")

        # mute errors, this is only a thumbnail
        if self.error is not None:
            self.error = None
            return None

        links = parse.xpath("//div[@id='upper']/div/img/@src")
        if links:
            return links[0]

    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        title = self.asset_name
        resolutions = self._resolutions
        variants = self._variants
        data = self._data
        doublesided = self._doublesided
        
        if variant_index < 0 or variant_index >= len(variants):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False

        variant_name = variants[variant_index]
        material_data.name = f"{self.home_dir}/{title}/{variant_name}"

        res = resolutions[variant_index % len(resolutions)]
        sideness = variant_index // len(resolutions)
        zip_url = data['files'][res]

        zip_path = self.fetchZip(zip_url, material_data.name, "textures.zip")
        zip_dir = os.path.dirname(zip_path)
        if os.path.getsize(zip_path) == 0:
            # maps already exist
            namelist = os.listdir(zip_dir)
        else:
            namelist = []
            with zipfile.ZipFile(zip_path,"r") as zip_ref:
                namelist = zip_ref.namelist()
                zip_ref.extractall(zip_dir)
            # wipe zip to leave only a 0-sized file:
            open(zip_path, 'wb').close()

        # Translate cgbookcase map names into our internal map names
        maps_tr = {
            'BaseColor': 'baseColor',
            'Normal': 'normal',
            'Opacity': 'opacity',
            'Roughness': 'roughness',
            'Metallic': 'metallic',
            'Height': 'height',
            'AO': 'ambientOcclusion',
        }
        for name in namelist:
            base = os.path.splitext(name)[0]
            tokens = base.split('_')
            map_type = tokens[-1]

            if map_type not in maps_tr:
                continue

            map_name = maps_tr[map_type]

            if doublesided:
                map_side = tokens[-2]

                if map_side == "front" and sideness == 2:
                    continue  # back only
                elif map_side == "back" and sideness == 1:
                    continue  # front only

                if map_side == "back":
                    map_name += "_back"
            
            material_data.maps[map_name] = os.path.join(zip_dir, name)
        
        return True
