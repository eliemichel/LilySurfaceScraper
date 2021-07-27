# Copyright (c) 2020 Zivoy and Elie Michel
#
# This file is part of LilySurfaceScraper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import os
import re
from .AbstractScraper import AbstractScraper


class IesLibraryScraper(AbstractScraper):
    scraped_type = {'LIGHT'}
    source_name = "IES Library"
    home_url = "https://ieslibrary.com"
    home_dir = "ieslibrary"

    pattern = r"https://ieslibrary\.com/.*#ies-(.+)"

    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scrapped by this scraper."""
        return re.match(cls.pattern, url) is not None

    def getVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""

        asset_id = re.match(self.pattern, url).group(1)

        api_url = f"https://ieslibrary.com/en/browse/data.json?ies={asset_id}"

        data = self.fetchJson(api_url)
        if data is None:
            return None

        variant = data["lumcat"]  # data["manufacturString"]
        if variant == "":
            variant = asset_id

        self.metadata.setCustom("download_url", data["downloadUrlIes"])
        self.metadata.setCustom("blender_energy", data["energy"])
        self.metadata.name = asset_id
        self.metadata.setCustom("thumbnailURL", data["preview"])
        return [variant]

    def getThumbnail(self):
        return self.metadata.getCustom("thumbnailURL")

    def fetchVariant(self, variant_index, material_data, reinstall=False):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in getVariantList
        download_url = self.metadata.getCustom("download_url")
        blender_energy = self.metadata.getCustom("blender_energy")
        variant = self.metadata.variants[0]

        if variant_index < 0 or variant_index >= len([variant]):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False

        material_data.name = f"{self.home_dir}/{self.metadata.name}/{variant}"

        data_file = self.fetchFile(download_url, f"{self.home_dir}/{self.metadata.name}", f"{variant}.ies")
        data_dir = os.path.dirname(data_file)

        material_data.maps["ies"] = os.path.join(data_dir, f"{variant}.ies")
        material_data.maps["energy"] = blender_energy
        return True

    def isDownloaded(self, target_variation):
        root = self.getTextureDirectory(os.path.join(self.home_dir, self.metadata.name))
        return os.path.isfile(os.path.join(root, f"{target_variation}.ies"))

    def getUrlFromName(self, asset_name):
        return f"https://ieslibrary.com/en/browse#ies-{asset_name}"
