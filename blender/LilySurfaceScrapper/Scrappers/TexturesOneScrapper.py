# Copyright (c) 2019 Bent Hillerkus

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from .AbstractScrapper import AbstractScrapper
from ..ScrappersManager import ScrappersManager

class TexturesOneMaterialScrapper(AbstractScrapper):  
    source_name = "Textures.one"
    home_url = "https://www.textures.one"
    scrapped_type = "MATERIAL"

    url_cache = {}

    @classmethod
    def findSource(cls, url: str) -> str:
        """Find the original page from where the texture is being distributed via scraping."""
        html = AbstractScrapper.fetchHtml(None, url)
        if html is None: raise ConnectionError
        
        # Scrape the url
        return html.xpath("//span[@class='goLink']/a")[0].get("href")

    @classmethod
    def cacheSourceUrl(cls, url) -> bool:
        """Look for a scrapper that can scrap the source page, and if so caches the
        result for further use."""
        source_url = cls.findSource(url)
        if source_url is None:
            return False
        for S in ScrappersManager.getScrappersList():
            if cls.scrapped_type in S.scrapped_type and S.canHandleUrl(source_url):
                scrapper_class: AbstractScrapper = S
                scrapped_type: str = scrapper_class.scrapped_type
                cls.url_cache[url] = (source_url, scrapper_class, scrapped_type)
                return True
        return False

    @classmethod
    def canHandleUrl(cls, url :str) -> bool:
        """Return true if the URL can be scrapped by this scrapper."""
        if "textures.one/go" and "?id=" in url:
            return cls.cacheSourceUrl(url)
        return False

    def fetchVariantList(self, url: str) -> list:
        cls = self.__class__
        if url not in cls.url_cache:
            return []
        source_url, scrapper_class, scrapped_type = cls.url_cache[url]
        self.scrapped_type = scrapped_type
        self.source_scrapper = scrapper_class(self.texture_root)
        return self.source_scrapper.fetchVariantList(source_url)

    def fetchVariant(self, variant_index, material_data):
        return self.source_scrapper.fetchVariant(variant_index, material_data)

class TexturesOneWorldScrapper(TexturesOneMaterialScrapper):
    scrapped_type = "WORLD"
