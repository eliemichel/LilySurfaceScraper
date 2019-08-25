# Copyright notice?

from .AbstractScrapper import AbstractScrapper
from ..ScrappersManager import ScrappersManager

class TexturesOneScrapper(AbstractScrapper):  
    source_name = "Textures.one"
    home_url = "https://www.textures.one"
    
    # There is probably something rotten about doing it this way, but I couldn't really figure out another way
    source_scrapper_type = None # lovely global state
    source_scrapper = None

    @classmethod
    def findSource(cls, url):
        """Find the original page from where the texture is being distributed via scraping."""
        html = super().fetchHtml(None, url)
        if html is None:
            return None
        
        # Scrape the url
        return html.xpath("//span[@class='goLink']/a")[0].get("href")

    @classmethod
    def canHandleUrl(cls, url):
        """Return true if the URL can be scrapped by this scrapper."""
        if "textures.one/go/?id=" in url: # this is superior to url.startswith(), because it can deal with leaving out "https://" or "www."
            source_url = cls.findSource(url)
            if source_url is not None:
                # Look for a scrapper that can scrape the source page
                for S in ScrappersManager.getScrappersList():
                    if S.canHandleUrl(source_url):
                        cls.source_scrapper_type = S
                        cls.source_scrapper = S("") # I'd love to create this in this classes __init__(), but it gave me headache with scope problems.
                        cls.scrapped_type = cls.source_scrapper_type.scrapped_type # This works
                        return True
        return False

    def fetchVariantList(self, url):
        self.source_scrapper.texture_root = self.texture_root # I'd love to do this just once via the constructor, but again, didn't really get __init__() here to work
        return self.source_scrapper.fetchVariantList(url)

    def fetchVariant(self, variant_index, material_data):
        self.source_scrapper.texture_root = self.texture_root
        return self.source_scrapper.fetchVariant(variant_index, material_data)
