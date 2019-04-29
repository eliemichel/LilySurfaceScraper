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

from .AbstractScrapper import AbstractScrapper

class HdriHeavenScrapper(AbstractScrapper):
    scrapped_type: {'WORLD'}

    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scrapped by this scrapper."""
        return url.startswith("https://hdrihaven.com/tex")
    
    def fetchVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        html = self.fetchHtml(url)
        if html is None:
            return None

        maps = html.xpath("//div[@class='download-buttons']//div[@class='map-type']")

        variants = maps[0].xpath(".//div[@class='res-item']/a/div/text()")
        variants = [self.clearString(s) for s in variants]

        self._html = html
        self._maps = maps
        self._variants = variants
        return variants
    
    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        html = self._html
        maps = self._maps
        variants = self._variants
        
        if variant_index < 0 or variant_index >= len(variants):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False
        
        base_name = html.xpath("//title/text()")[0].split('|')[0].strip()
        var_name = variants[variant_index]
        material_data.name = "textureheaven/" + base_name + '/' + var_name

        # Translate cgbookcase map names into our internal map names
        maps_tr = {
            'Diffuse': 'baseColor',
            'Normal': 'normal',
            'Specular': 'specular',
            'Roughness': 'roughness',
            'Metallic': 'metallic',
        }
        for m in maps:
            map_name = m.xpath("div[@class='map-download']//text()")[0]
            map_url = "https://texturehaven.com" + m.xpath(".//div[@class='res-item']/a/@href")[variant_index]
            if map_name in maps_tr:
                map_name = maps_tr[map_name]
                material_data.maps[map_name] = self.fetchImage(map_url, material_data.name, map_name)
        
        return True
