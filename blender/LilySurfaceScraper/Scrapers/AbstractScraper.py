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

import os
import string

import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "site-packages"))
from lxml import etree

import requests
import shutil
import re
import json

from ..settings import TEXTURE_DIR
from ..preferences import getPreferences

class AbstractScraper():
    # Can be 'MATERIAL', 'WORLD', 'LIGHT'
    scraped_type = {'MATERIAL'}
    # The name of the scraped source, displayed in UI
    source_name = "<Abstract>"
    # The URL of the source's home, used for the list of available sources in panels
    home_url = None
    # directory of textures
    home_dir = None

    @staticmethod
    def sortTextWithNumbers(text):
        return [int(i) if i.isdigit() else i for i in re.split(r'(\d+)', text)]

    @classmethod
    def canHandleUrl(cls, url):
        raise NotImplementedError

    def __init__(self, texture_root=""):
        self.asset_name = None
        self.error = None
        self.texture_root = texture_root
        self.reinstall = False

    @classmethod
    def _fetch(cls, url):
        headers = {"User-Agent":"Mozilla/5.0"}  # fake user agent
        r = requests.get(url if "https://" in url else "https://" + url, headers=headers)
        if r.status_code != 200:
            return None
        else:
            return r

    def fetchHtml(self, url):
        """Get a lxml.etree object representing the scraped page.
        Use xpath queries to browse it."""
        r = self._fetch(url)
        if r is not None:
            return etree.HTML(r.text)
        else:
            self.error = "URL not found: {}".format(url)

    def fetchJson(self, url):
        r = self._fetch(url)
        if r is not None:
            return r.json()
        else:
            self.error = "URL not found: {}".format(url)

    def fetchXml(self, url):
        """Get a lxml.etree object representing the scraped page.
        Use xpath queries to browse it."""
        r = self._fetch(url)
        if r is not None:
            return etree.fromstring(r.text)
        else:
            self.error = "URL not found: {}".format(url)

    def getRedirection(self, url):
        headers = {"User-Agent":"Mozilla/5.0"}  # fake user agent
        url = url if "https://" in url else "https://" + url
        r = requests.get(url, headers=headers, allow_redirects=False)
        if r.status_code == 302:
            return r.headers.get("Location")
        else:
            return None

    def getTextureDirectory(self, material_name):
        """Return the texture dir, relative to the blend file, dependent on material's name"""
        texture_dir = getPreferences().texture_dir
        if texture_dir == "":
            texture_dir = TEXTURE_DIR
        if texture_dir.startswith("//"):
            texture_dir = texture_dir[2:]
        if not os.path.isabs(texture_dir):
            texture_dir = os.path.realpath(os.path.join(self.texture_root, texture_dir))
        name_path = material_name.replace('/', os.path.sep)
        dirpath = os.path.join(texture_dir, name_path)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
        return dirpath

    def downloadFunc(self, url):
        def func(path):
            headers = {"User-Agent": "Mozilla/5.0"}  # fake user agent
            r = requests.get(url, stream=True, headers=headers)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
            else:
                self.error = "URL not found: {}".format(url)
                return -1
        return func

    def fetchImage(self, url, material_name, map_name, force_ext=False):
        """Utility helper for download textures"""
        root = self.getTextureDirectory(material_name)
        if not force_ext:
            ext = os.path.splitext(url)[1]
            map_name = map_name + ext
        path = os.path.join(root, map_name)
        return self.saveFile(path, self.downloadFunc(url))

    def fetchFile(self, url, material_name, filename):
        root = self.getTextureDirectory(material_name)
        path = os.path.join(root, filename)

        return self.saveFile(path, self.downloadFunc(url))

    def fetchZip(self, url, material_name, zip_name):
        """Utility helper for download textures"""
        root = self.getTextureDirectory(material_name)
        path = os.path.join(root, zip_name)
        return self.saveFile(path, self.downloadFunc(url))

    def saveFile(self, path, dataCallbackFunction):
        """function for saving data, path is the location
        dataCallbackFunction is a function that is used if file is not already present, return -1 if error occurred"""
        if os.path.isfile(path) and not self.reinstall:
            print("Using cached {}.".format(path))
        else:
            print("Downloading {}...".format(path))
            r = dataCallbackFunction(path)
            if r == -1:
                return None
        return path

    def clearString(self, s):
        """Remove non printable characters"""
        printable = set(string.printable)
        return ''.join(filter(lambda x: x in printable, s))

    def fetchVariantList(self, url):
        # **must have self.asset_name**

        # get asset name and variants
        variants = self.getVariantList(url)
        assetName = self.asset_name

        root = self.getTextureDirectory(os.path.join(self.home_dir, assetName))

        # download thumbnail and make metadata file if meta file is not present
        metadataFile = os.path.join(root, ".meta")
        if not os.path.isfile(metadataFile):
            thumbnailName = self.downloadThumbnail(root, assetName)

            metadata = {
                "name": assetName,
                "scraper": self.__class__.__name__,
                "fetchUrl": url,
                "thumbnail": thumbnailName,
                "variants": variants,
            }
            with open(metadataFile, "w") as f:
                json.dump(metadata, f, indent=4)
        return variants

    def downloadThumbnail(self, assetPath, assetName):
        thumbnailUrl = self.getThumbnail()
        ext = None
        if thumbnailUrl is None:
            print("no thumbnail found, not downloading")
        else:
            thumbnailReq = self._fetch(thumbnailUrl)
            if thumbnailReq is None:
                return None
            thumbnailType = thumbnailReq.headers["Content-Type"]
            if thumbnailType == 'image/png':
                ext = "png"
            elif thumbnailType == "image/jpeg":
                ext = "jpg"
            else:
                print(f"thumbnail type '{thumbnailType}' is not a valid type")

        if ext is None:
            return None
        thumbnailName = f"thumb.{ext}"
        with open(os.path.join(assetPath, thumbnailName), "wb") as f:
            f.write(thumbnailReq.content)
        return thumbnailName

    def getVariantList(self, url):
        """Get a list of available variants.
        also fill self.asset_name for metadata, otherwise implement fetchVariantList
        The list may be empty, and must be None in case of error."""
        raise NotImplementedError

    def fetchVariant(self, variant_index, material_data):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        raise NotImplementedError

    def getThumbnail(self):
        """Function for getting a url for a thumbnail for the texture, preferably using only self.assetName
         but you can pass more arguments with self._*** as its called after getVariantList.
         you can return None if there is no thumbnail or you cant get one
         returns: url or None
         """
        raise NotImplementedError

    def isDownloaded(self, asset, targetVariation):
        """takes the asset and a variation name and checks if its installed, returns a boolean"""
        root = self.getTextureDirectory(os.path.join(self.home_dir, asset))
        return os.path.exists(os.path.join(root, targetVariation))
