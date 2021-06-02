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

class HdriHavenScraper(AbstractScraper):
    scraped_type = {'WORLD'}
    source_name = "HDRI Haven"
    home_url = "https://hdrihaven.com/hdris/"

    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scraped by this scraper."""
        return url.startswith("https://hdrihaven.com/hdri")
    
    def extractButtonName(self, d):
        names = d.xpath(".//div[@class='button']/b/text()")
        if len(names) >= 1:
            return names[0]
        names = d.xpath(".//div[@class='button']/text()")
        if len(names) >= 1:
            return names[0].split("⋅")[0].strip()
        names = d.xpath(".//div[@class='dl-btn']/b/text()")
        if len(names) >= 1:
            return names[0]
        names = d.xpath(".//div[@class='dl-btn']/text()")
        if len(names) >= 1:
            return names[0].split("⋅")[0].strip()
        return "(unrecognized option)"


    def fetchVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        html = self.fetchHtml(url)
        if html is None:
            return None

        variant_data = html.xpath("//div[@class='download-buttons']/a")
        variants = [self.clearString(self.extractButtonName(d)) for d in variant_data]

        self._html = html
        self._variant_data = variant_data
        self._variants = variants
        return variants
    
    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        html = self._html
        variant_data = self._variant_data
        variants = self._variants
        
        if variant_index < 0 or variant_index >= len(variants):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False
        
        base_name = html.xpath('//h1/b/text()')[0]
        var_name = variants[variant_index]
        material_data.name = "hdrihaven/" + base_name + '/' + var_name

        url = variant_data[variant_index].attrib['href']
        if url.startswith("//"):
            url = "https:" + url
        if url.endswith('.exr') or url.endswith('.hdr') or url.endswith('.jpg'):
            map_url = url
        else:
            redirect_html = self.fetchHtml(url)
            map_url = redirect_html.xpath("//a[@download]/@href")[0]
            if map_url.startswith("//"):
            	map_url = "https:" + map_url
            elif not map_url.startswith("http"):
            	map_url = "https://hdrihaven.com" + map_url
        material_data.maps['sky'] = self.fetchImage(map_url, material_data.name, 'sky')
        
        return True
