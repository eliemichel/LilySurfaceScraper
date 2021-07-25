# Copyright (c) 2019 Bent Hillerkus
# Edited in 2020 by Elie Michel

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

from .AbstractScraper import AbstractScraper
from ..ScrapersManager import ScrapersManager

class TexturesOneMaterialScraper(AbstractScraper):  
    source_name = "3DAssets.one"
    home_url = "https://www.3dassets.one"
    scraped_type = "MATERIAL"

    url_cache = {}

    @classmethod
    def findSource(cls, url: str) -> str:
        """Find the original page from where the texture is being distributed via scraping."""
        return cls.getRedirection(None, url)

    @classmethod
    def cacheSourceUrl(cls, url) -> bool:
        """Look for a scraper that can scrap the source page, and if so caches the
        result for further use."""
        source_url = cls.findSource(url)
        if source_url is None:
            print("source url is none")
            return False
        for S in ScrapersManager.getScrapersList():
            if cls.scraped_type in S.scraped_type and S.canHandleUrl(source_url):
                scraper_class: AbstractScraper = S
                scraped_type: str = scraper_class.scraped_type
                cls.url_cache[url] = (source_url, scraper_class, scraped_type)
                return True
        print("no scraper could handle {}".format(source_url))
        return False

    @classmethod
    def canHandleUrl(cls, url :str) -> bool:
        """Return true if the URL can be scraped by this scraper."""
        if ("textures.one/go" in url or "3dassets.one/go" in url) and "?id=" in url:
            return cls.cacheSourceUrl(url)
        return False

    def fetchVariantList(self, url: str) -> list:
        cls = self.__class__
        if url not in cls.url_cache:
            return []
        source_url, scraper_class, scraped_type = cls.url_cache[url]
        self.scraped_type = scraped_type
        self.source_scraper = scraper_class(self.texture_root)
        return self.source_scraper.fetchVariantList(source_url)

    def fetchVariant(self, variant_index, material_data):
        return self.source_scraper.fetchVariant(variant_index, material_data)


class TexturesOneWorldScraper(TexturesOneMaterialScraper):
    scraped_type = "WORLD"
