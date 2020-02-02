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
    source_name = "cgbookcase.com"
    home_url = "https://www.cgbookcase.com/textures/"

    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scrapped by this scrapper."""
        return "cgbookcase.com/textures/" in url
    
    def fetchVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        html = self.fetchHtml(url)
        if html is None:
            return None
        
        # Get resolutions
        resolutions = int(html.xpath("//meta[@name='tex1:resolution']/@content")[0])

        # Has front or back-side?
        # Checks for the "Front" text below the item name
        # Example: https://www.cgbookcase.com/textures/autumn-leaf-22
        double_sided = len(html.xpath("//div[@id='view-downloadSection']/h3")) != 0

        # Get variants
        variants_data = html.xpath("//div[@id='view-downloadLinks']/div")
        variants = []
        variants += [str(n) + "K" for n in range(resolutions, 0, -1)]
        if double_sided:
            front_variants = [v for v in variants]
            variants += [v + " Backside" for v in front_variants]
            variants += [v + " Twosided" for v in front_variants]
        
        # Save some data for fetchVariant
        self._html = html
        self._variants_data = variants_data
        self._variants = variants
        self._double_sided = double_sided
        return variants
    
    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        html = self._html
        variants_data = self._variants_data
        variants = self._variants
        double_sided = self._double_sided

        if variant_index < 0 or variant_index >= len(variants):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False

        base_name = str(html.xpath("//h1/text()")[0])
        variant_name = variants[variant_index]
        material_data.name = "cgbookcase/" + base_name + "/" + variant_name

        # If two sided, use several variants, and label them with is_back_side bool
        n = len(variants_data)
        selected_variants = [(variants_data[variant_index % n], False)]
        if double_sided and variant_index >= n and variant_index < n * 1.5:
            selected_variants.append((variants_data[variant_index % n + n // 2], True))

        # Translate cgbookcase map names into our internal map names
        maps_tr = {
            'Base Color': 'albedo',
            'Normal': 'normal',
            'Opacity': 'opacity',
            'Roughness': 'roughness',
            'Metallic': 'metallic',
            'Height': 'height',
            'AO': 'ambientOcclusion',
        }
        for variant_html_data, is_back_side in selected_variants:
            for m in variant_html_data.xpath(".//a"):
                map_url = "https://www.cgbookcase.com" + m.attrib['href']

                temp = map_url[map_url.find("K_") + 2:-4].split("_")
                map_name = " ".join(temp[1:]).title() if double_sided else " ".join(temp).title()

                if map_name in maps_tr:
                    map_name = maps_tr[map_name]
                    if is_back_side:
                        map_name += "_back"
                    material_data.maps[map_name] = self.fetchImage(map_url, material_data.name, map_name)
        
        return True
