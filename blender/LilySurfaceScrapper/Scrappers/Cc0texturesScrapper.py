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
import re
from typing import List, Union
from .AbstractScrapper import AbstractScrapper

class Cc0texturesScrapper(AbstractScrapper):
    source_name = "CC0 Textures"
    home_url = "https://cc0textures.com"
    material_view_url = "https://www.cc0textures.com/view?id="

    @classmethod
    def canHandleUrl(cls, url) -> bool:
        """Return true if the URL can be scrapped by this scrapper."""
        return url.startswith(cls.material_view_url)

    @classmethod
    def getMaterialName(cls, url) -> str:
        """Turn 'https://www.cc0textures.com/view?id=PavingStones055' into 'PavingStones055'."""
        return url[len(cls.material_view_url):]
    
    def fetchVariantList(self, url) -> Union[List[str], None]:
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        html = self.fetchHtml(url)
        if html is None:
            return None

        # List of these strings ".get?file=PavingStones055_2K-JPG.zip"
        download_sublinks = html.xpath("//div[@class='DownloadButton']/a/@href")
        if download_sublinks is None:
            return None

        def slice_variant_name(link) -> str:
            """Turn '.get?file=PavingStones055_2K-JPG.zip' into '2K-JPG'."""
            return link[len("./get?file=" + self.getMaterialName() + "_"):-len(".zip")]

        # Save the actual download links so fetchVariant can access them
        self._links = list(map(lambda link: self.home_url + link[1:] , download_sublinks))
        self._material_name = self.getMaterialName(url)

        return list(map(lambda link: slice_variant_name(link).replace("-", " "), download_sublinks))
    
    def fetchVariant(self, variant_index, material_data) -> bool:
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        links = self._links
        material_data.name = re.sub(r"(\w)([A-Z])", r"\1 \2", self._material_name) # https://www.w3resource.com/python-exercises/re/python-re-exercise-51.php

        if variant_index < 0 or variant_index >= len(links):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False
        
        variant = links[variant_index]

        zip_path = self.fetchZip(variant, material_data.name, "textures.zip")
        zip_dir = os.path.dirname(zip_path)
        namelist = []
        with zipfile.ZipFile(zip_path,"r") as zip_ref:
            namelist = zip_ref.namelist()
            zip_ref.extractall(zip_dir)
        
        # Translate cc0textures map names into our internal map names
        maps_tr = {
            'col': 'albedo',
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
