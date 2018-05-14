# -*- coding: utf-8 -*-
import re

from scrapy import Spider, Request

from Company.poemr.poemr.items import PoetItem


class PoetSpider(Spider):
    name = 'poet'
    allowed_domains = ['so.gushiwen.org']
    start_urls = ['http://so.gushiwen.org/']

    poet_url = 'http://so.gushiwen.org/author_{page}.aspx'
    info_url = 'http://so.gushiwen.org/authors/ajaxziliao.aspx?id={id}'

    def start_requests(self):
        yield Request(self.poet_url.format(page=1), self.parse_poet)

    def parse_poet(self, response):
        currentPage = int(re.findall('[0-9]{1,4}',response.url)[0])
        print('::::::::: Page %d :::::::::'%currentPage)
        item = PoetItem()
        item['zlids'] = []
        item['zlmbs'] = []
        item['zlrfs'] = []
        docs = response.css('.left .sonspic')
        item['poetName'] = docs.css('h1 span b::text').extract_first()
        try:
            a = docs.xpath('.//a[contains(@href,"/authors/authorsw_")]').xpath('./parent::*').extract_first().split('<a href="/authors/authorsw_{}A1.aspx">'.format(currentPage))
            item['poems'] = a[-1].split('► ')[-1].split('篇')[0]
            item['intro'] = a[0].split('>')[-1]
        except:
            if not currentPage == 3156:
                yield Request(self.poet_url.format(page=currentPage + 1), self.parse_poet)
        zlids = response.xpath('//div[@id]/@id').re('fanyi[0-9]{1,5}')
        others = response.xpath('//div[@class="cankao"]/..')
        for other in others:
            ids = other.css('.contyishang > div > h2 > span::text').extract_first()
            mbs = other.xpath('string(./div[@class="contyishang"])').extract_first()
            rfs = other.xpath('string(./div[@class="cankao"])').extract_first()
            item['zlids'].append(ids)
            item['zlmbs'].append(mbs)
            item['zlrfs'].append(rfs)
        for zlid in zlids:
            item['zlids'].append(zlid[5:])
            item['zlmbs'].append(zlid[5:])
            item['zlrfs'].append(zlid[5:])
            yield Request(self.info_url.format(id=zlid[5:]), meta={'key': item}, callback=self.parse_fysx)
        if not currentPage == 3156:
            yield Request(self.poet_url.format(page=currentPage+1), self.parse_poet)

    def parse_fysx(self, response):
        item = response.meta['key']
        ajax_id = re.findall('id=(\d{1,5})', response.url)[0]
        i = [i for i, x in enumerate(item['zlids']) if x == ajax_id][0]
        item['zlids'][i] = response.css('.contyishang > div > h2 > span::text').extract_first()
        item['zlmbs'][i] = response.xpath('string(//div[@class="contyishang"])').extract_first()
        item['zlrfs'][i] = response.xpath('string(//div[@class="cankao"])').extract_first()
        if not [x for x in item['zlids'] if x.isdigit()]:
            yield item