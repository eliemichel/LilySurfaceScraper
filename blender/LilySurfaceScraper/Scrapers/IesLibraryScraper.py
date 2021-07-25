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

        variant = data["lumcat"]
        if variant == "":
            variant = asset_id

        self._download_url = data["downloadUrlIes"]
        self._blender_energy = data["energy"]
        self.asset_name = asset_id
        self._variant = variant
        self._thumbnailURL = data["preview"]
        return [self._variant]

    def getThumbnail(self):
        return self._thumbnailURL

    def fetchVariant(self, variant_index, material_data, reinstall=False):
        """Fill material_data with data from the selected variant.
        Must fill material_data.name and material_data.maps.
        Return a boolean status, and fill self.error to add error messages."""
        # Get data saved in fetchVariantList
        download_url = self._download_url
        blender_energy = self._blender_energy
        variant = self._variant

        if variant_index < 0 or variant_index >= len([variant]):
            self.error = "Invalid variant index: {}".format(variant_index)
            return False

        material_data.name = f"{self.home_dir}/{self.asset_name}/{variant}"

        data_file = self.fetchFile(download_url, "/".join(material_data.name.split("/")[:2]), f"{variant}.ies")
        data_dir = os.path.dirname(data_file)
        energy_path = os.path.join(data_dir, "lightEnergy")

        def saveEnergy(_):
            with open(energy_path, "w") as f:
                f.write(str(blender_energy))
        self.saveFile(energy_path, saveEnergy)

        material_data.maps["ies"] = os.path.join(data_dir, f"{variant}.ies")
        material_data.maps["energy"] = energy_path
        return True

    def isDownloaded(self, asset, target_variation):
        root = self.getTextureDirectory(os.path.join(self.home_dir, asset))
        return os.path.isfile(os.path.join(root, f"{target_variation}.ies"))
