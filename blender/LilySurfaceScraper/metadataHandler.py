# Copyright (c) 2021 Zivoy
#
# This file is part of LilySurfaceScraper, a Blender add-on to import
# materials from a single URL. It is released under the terms of the GPLv3
# license. See the LICENSE.md file for the full text.

import json
import os


class Metadata:
    def __init__(self, name, identifier, scraper_name, source_url, thumbnail_filename, variants_list):
        """class for storing metadata for scrapers about an asset"""
        self.name = name
        self.id = identifier
        self.scraper = scraper_name
        self.fetchUrl = source_url
        self.thumbnail = thumbnail_filename
        self.variants = variants_list
        self.custom = dict()

    def load(self, metadata_file):
        obj = self.open(metadata_file)
        self.name = obj.name
        self.id = obj.id
        self.scraper = obj.scraper if self.scraper == "" else self.scraper
        self.fetchUrl = obj.fetchUrl
        self.thumbnail = obj.thumbnail
        self.variants = obj.variants
        self.custom = obj.custom

    @classmethod
    def open(cls, metadata_file):
        if not os.path.isfile(metadata_file):
            return cls.createBlank()
        with open(metadata_file, "r") as f:
            data = json.load(f)
        obj = cls(cls._defaultTo(data, "name", ""),
                   cls._defaultTo(data, "id", ""),
                   cls._defaultTo(data, "scraper", ""),
                   cls._defaultTo(data, "fetchUrl", ""),
                   cls._defaultTo(data, "thumbnail", None),
                   cls._defaultTo(data, "variants", list()))
        obj.custom = cls._defaultTo(data, "custom", dict())
        return obj

    @classmethod
    def createBlank(cls):
        return cls("", "", "", "", None, list())

    @staticmethod
    def _defaultTo(dictionary, key, default):
        return dictionary[key] if key in dictionary else default

    def save(self, metadata_filepath):
        metadata = {
            "name": self.name,
            "id": self.id,
            "scraper": self.scraper,
            "fetchUrl": self.fetchUrl,
            "thumbnail": self.thumbnail,
            "variants": self.variants,
            "custom": self.custom
        }
        with open(metadata_filepath, "w") as f:
            json.dump(metadata, f, indent=4)

    def getCustom(self, key):
        return self.custom[key]

    def setCustom(self, key, value):
        self.custom[key] = value
