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
from collections import defaultdict


class PolyHavenHdriScraper(AbstractScraper):
    scraped_type = {'WORLD'}
    source_name = "Poly Haven HDRI"
    home_url = "https://polyhaven.com/hdris"
    home_dir = "hdrihaven"

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
        return url.startswith("https://polyhaven.com/a/")

    def getVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        identifier = self.getUid(url)

        if identifier is None:
            self.error = "Bad Url"
            return None

        data = self.fetchJson(f"https://api.polyhaven.com/info/{identifier}")
        if data is None:
            self.error = "API error"
            return None
        elif data["type"] != 0:  # 0 for hdris
            self.error = "Not a texture"
            return None

        api_url = f"https://api.polyhaven.com/files/{identifier}"
        data = self.fetchJson(api_url)
        if data is None:
            self.error = "API error"
            return None

        variant_data = defaultdict(dict)
        for res, maps in data["hdri"].items():
            for fmt, dat in maps.items():
                variant_data[(res, fmt)] = dat['url']

        variant_data = [(*k, v) for k, v in variant_data.items()]
        variant_data.sort(key=lambda x: self.sortTextWithNumbers(f"{x[1]} {x[0]}"))
        variants = [f"{res} ({fmt})" for res, fmt, _ in variant_data]

        self.asset_name = identifier
        self._variant_data = variant_data
        self._variants = variants
        return variants

    def getThumbnail(self):
        return f"https://cdn.polyhaven.com/asset_img/thumbs/{self.asset_name}.png?width=512&height=512"

    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        identifier = self.asset_name
        variant_data = self._variant_data
        variants = self._variants
        
        if variant_index < 0 or variant_index >= len(variants):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False
        
        var_name = variants[variant_index]
        material_data.name = f"{self.home_dir}/{identifier}/{var_name}"

        map_url = variant_data[variant_index][2]
        material_data.maps['sky'] = self.fetchImage(map_url, material_data.name, 'sky')
        
        return True
