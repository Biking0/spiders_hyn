# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SpidersHynItem(scrapy.Item):
    f = scrapy.Field()  # flightNumber
    d = scrapy.Field()  # depTime
    a = scrapy.Field()  # arrTime
    fc = scrapy.Field()  # fromCity
    tc = scrapy.Field()  # toCity
    c = scrapy.Field()  # currency
    ap = scrapy.Field()  # adultPrice
    at = scrapy.Field()  # adultTax
    n = scrapy.Field()  # netFare
    m = scrapy.Field()  # maxSeats
    cb = scrapy.Field()  # cabin
    cr = scrapy.Field()  # carrier
    i = scrapy.Field()  # isChange
    s = scrapy.Field()  # segments
    g = scrapy.Field()  # getTime
    da = scrapy.Field()  # depAirport
    aa = scrapy.Field()  # arrAirport
    info =scrapy.Field()   # info
