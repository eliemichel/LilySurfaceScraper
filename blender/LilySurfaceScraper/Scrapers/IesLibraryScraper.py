# Copyright (c) 2020 Zivoy and Elie Michel
#
# This file is part of LilySurfaceScraper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import os
import re
from .AbstractScraper import AbstractScraper
#todo make material name better
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

    def _fetchVariantList(self, url):
        """Get a list of available variants.
        The list may be empty, and must be None in case of error."""

        asset_id = re.match(self.pattern, url).group(1)

        api_url = f"https://ieslibrary.com/en/browse/data.json?ies={asset_id}"

        data = self.fetchJson(api_url)
        if data is None:
            return None

        self._download_url = data["downloadUrlIes"]
        self._blender_energy = data["energy"]
        self._asset_name = asset_id
        self._variant = data["lumcat"]
        self._thumbnailURL = data["preview"]
        return [self._variant]

    def getThumbnail(self, _):
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

        material_data.name = os.path.join(self.home_dir, self._asset_name, variant)

        data_file = self.fetchFile(download_url, material_data.name, "lightData.ies")
        data_dir = os.path.dirname(data_file)
        with open(os.path.join(data_dir, "lightEnergy"), "w+") as f:
            f.write(str(blender_energy))

        material_data.maps["ies"] = os.path.join(data_dir, "lightData.ies")
        material_data.maps["energy"] = os.path.join(data_dir, "lightEnergy")
        return True