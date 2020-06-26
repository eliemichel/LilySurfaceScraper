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

from .TexturesOneScrapper import TexturesOneMaterialScrapper, TexturesOneWorldScrapper
from .AbstractScrapper import AbstractScrapper
from random import choice
import requests

class TexturesOneSearchScrapper(TexturesOneMaterialScrapper):
    scrapped_type = "NONE"
    home_url = None  # Prevent double with TexturesOneMaterialScrapper in UI
    scrapped_type_name = ""
    supported_creators = []

    @classmethod
    def findSource(cls, search_term: str) -> str:
        """Search and pick a random result from the results site"""
        creator_filter = "&".join(["creator[]=" + x for x in cls.supported_creators])
        url = "https://textures.one/search/?query=" + search_term + "&" + cls.scrapped_type_name + "&" + creator_filter
        html = AbstractScrapper.fetchHtml(None, url)
        print("url: {}".format(url))
        if html is None: raise ConnectionError
        print("html: {}".format(html))
        links = html.xpath("//div[@class='asset-container']/a/@href")
        print("links: {}".format(links))
        if links == []:
            return None

        url = choice(links)

        # resolve URL
        if not url.startswith("http"):
            url = "https://www.3dassets.one" + url

        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, allow_redirects=False)
        if r.status_code == 200:
            return url
        elif 'Location' in r.headers:
            return r.headers['Location']
        else:
            return None

    @classmethod
    def canHandleUrl(cls, url: str) -> bool:
        if "/" in url:
            # It is an URL, not a search query
            return False
        return cls.cacheSourceUrl(url)

class TexturesOneSearchMaterialScrapper(TexturesOneSearchScrapper):
    scrapped_type = "MATERIAL"
    scrapped_type_name = "tex-pbr"
    supported_creators = ['cc0textures', 'cgbookcase', 'texturehaven'] # IDs of the websites on Textures.one that we support

class TexturesOneSearchWorldScrapper(TexturesOneSearchScrapper):
    scrapped_type = "WORLD"
    scrapped_type_name = "hdri-sphere"
    supported_creators = ['hdrihaven']
