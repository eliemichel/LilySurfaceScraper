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


class HdriHavenScraper(PolyHavenAbstract):
    scraped_type = {'WORLD'}
    source_name = "Poly Haven HDRIs"
    home_url = "https://polyhaven.com/hdris"
    target = 0

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
        material_data.name = "hdrihaven/" + base_name + '/' + var_name

        map_url = json["hdri"][var_name]["hdr"]["url"]
        material_data.maps['sky'] = self.fetchImage(map_url, material_data.name, 'sky')
        
        return True
