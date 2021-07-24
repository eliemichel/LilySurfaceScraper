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
import requests


class PolyHavenAbstract(AbstractScraper):
    source_name = "Poly Haven"
    home_url = "https://polyhaven.com/"
    target = -1  # 0: hdris, 1: textures, 2:models
    apiBase = "https://api.polyhaven.com"

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
        uid = cls.getUid(url)
        if uid is not None:
            # data = cls.fetchJson(f"{cls.apiBase}/info/{uid}")
            req = requests.get(f"{cls.apiBase}/info/{uid}")
            return req.status_code == 200 and req.json()["type"] == cls.target
        return False
    
    def fetchVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""
        uid = self.getUid(url)

        data = self.fetchJson(f"{self.apiBase}/files/{uid}")

        firstVal = "hdri" if self.target == 0 else "arm"
        variants = sorted(list(data[firstVal].keys()))
        imageTypes = list(data[firstVal][variants[0]].keys())

        self._json = data
        self._variants = variants
        self._types = imageTypes
        self._id = uid
        return variants
