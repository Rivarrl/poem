# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class PoemItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = Field()
    dynasty = Field()
    poet = Field()
    plain = Field()
    article = Field()
    tags = Field()
    fyids = Field()
    sxids = Field()
    fymbs = Field()
    sxmbs = Field()
    fyrfs = Field()
    sxrfs = Field()
    readid = Field()
    readurl = Field()

class PoetItem(Item):
    poetName = Field()
    poems = Field()
    intro = Field()
    zlids = Field()
    zlmbs = Field()
    zlrfs = Field()