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

class CgbookcaseScrapper(AbstractScrapper):
    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scrapped by this scrapper."""
        return url.startswith("https://www.cgbookcase.com/textures/")
    
    def fetchVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        html = self.fetchHtml(url)
        if html is None:
            return None
        
        # Get variants
        variants_data = html.xpath("//div[@class='textureSet']")
        variants = [v.xpath("h3/text()")[0] for v in variants_data]
        
        # Save some data for fetchVariant
        self._html = html
        self._variants_data = variants_data
        return variants
    
    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        html = self._html
        variants_data = self._variants_data
        
        if variant_index < 0 or variant_index >= len(variants_data):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False
        v = variants_data[variant_index]
        base_name = html.xpath("//div[@id='textureRight']/h2/text()")[0]
        variant_name = v.xpath("h3/text()")[0]
        
        material_data.name = "cgbookcase/" + base_name + "/" + variant_name
        
        # Translate cgbookcase map names into our internal map names
        maps_tr = {
            'Base_Color': 'baseColor',
            'Normal': 'normal',
            'Opacity': 'opacity',
            'Roughness': 'roughness',
            'Metallic': 'metallic',
        }
        for m in v.xpath(".//a[@class='directdownload']"):
            map_name = m.xpath("div[@class='downloadable']/text()")[0].strip()
            map_url = "https://www.cgbookcase.com" + m.attrib['href']
            if map_name in maps_tr:
                map_name = maps_tr[map_name]
                material_data.maps[map_name] = self.fetchImage(map_url, material_data.name, map_name)
        
        return True
