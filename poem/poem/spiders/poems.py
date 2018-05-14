# -*- coding: utf-8 -*-
import re

from scrapy import Spider, Request

from Company.poemr.poemr.items import PoemItem


class PoemSpider(Spider):
    name = 'poems'
    allowed_domains = ['so.gushiwen.org','www.gushiwen.org','song.gushiwen.org']
    start_urls = ['http://so.gushiwen.org/', 'http://www.gushiwen.org/','http://song.gushiwen.org/']

    poem_url = 'http://www.gushiwen.org/shiwen/default_0A0A{page}.aspx'
    ajax = 'http://so.gushiwen.org/shiwen2017/ajax{type}.aspx?id={id}'
    mp3_url = 'http://so.gushiwen.org/viewplay.aspx?id={id}'

    def start_requests(self):
        yield Request(self.poem_url.format(page=1), meta={'poem_num':0}, callback=self.poem_page)

    def poem_page(self, response):
        docs = response.css('.left .sons')
        poem_count = response.meta['poem_num']
        for doc in docs:
            detail_pages = doc.css('.cont .yizhu + p a::attr(href)').extract()
            for detail_page in detail_pages:
                poem_count += 1
                yield Request(detail_page, self.parse_poem)
        next_page = response.css('.pages > span + a::text').extract_first()
        all_poems = int(response.xpath('//div[@class="pages"]/span/text()').re('共[0-9]{1,5}篇')[0].lstrip('共').rstrip('篇'))
        if poem_count%3 == 0:
            print('Running Progress: ', '%.2f' %(poem_count*100/all_poems), '%', '\\', end='\r')
        elif poem_count%3 == 1:
            print('Running Progress: ', '%.2f' %(poem_count*100/all_poems), '%', '-', end='\r')
        else:
            print('Running Progress: ', '%.2f' %(poem_count*100/all_poems), '%', '/', end='\r')
        if poem_count <= all_poems:
            yield Request(self.poem_url.format(page=next_page), meta={'poem_num': poem_count}, callback=self.poem_page)

    def parse_poem(self, response):
        poem = response.css('.left div:nth-child(2)')
        item = PoemItem()
        href = re.compile('<a href=".*?>', re.S)
        item['fyids'] = []
        item['sxids'] = []
        item['fymbs'] = []
        item['sxmbs'] = []
        item['fyrfs'] = []
        item['sxrfs'] = []
        item['title'] = poem.css('h1::text').extract_first()
        item['dynasty'] = poem.css('.source a[href^="http"]::text').extract_first()
        item['poet'] = poem.css('.source a:not([href^="http"])::text').extract_first()
        item['plain'] = poem.xpath('string(.//div[@class="contson"])').extract_first()
        yizhu = poem.css('.yizhu').extract_first()
        temp = poem.css('.cont').extract_first()
        temp = re.sub(href,'',temp)
        item['article'] = temp.replace(yizhu,'').replace('</a>','')
        item['tags'] = poem.css('.tag a::text').extract()
        read = poem.xpath('//div[@class="left"]/div[@class="sons"][1]//a[@href]/@href').re('javascript:Play\(([0-9]{1,5})\)')
        item['readid'] = read[0] if read else ''
        item['readurl'] = self.mp3_url.format(id=read[0]) if read else ''
        if item['readurl']:
            yield Request(item['readurl'], meta={'key':item}, callback=self.parse_mp3)
        fyids = response.xpath('//div[@id]/@id').re('fanyi[0-9]{1,5}')
        sxids = response.xpath('//div[@id]/@id').re('shangxi[0-9]{1,5}')
        others = response.xpath('//div[@class="cankao"]/..')
        for other in others:
            ids = other.css('.contyishang > div > h2 > span::text').extract_first()
            speaker = other.xpath('.//img[@src="/img/speaker.png"]/..').extract_first()
            display = other.xpath('.//span[contains(@style,"display:none")]').extract_first()
            temp = other.css('.contyishang').extract_first().replace(speaker,'').replace(display,'')
            mbs = re.sub(href,'',temp).replace('</a>','')
            rfs = other.xpath('string(./div[@class="cankao"])').extract_first()
            if '译文' in ids:
                item['fyids'].append(ids)
                item['fymbs'].append(mbs)
                item['fyrfs'].append(rfs)
            else:
                item['sxids'].append(ids)
                item['sxmbs'].append(mbs)
                item['sxrfs'].append(rfs)
        for fyid in fyids:
            item['fyids'].append(fyid[5:])
            item['fymbs'].append(fyid[5:])
            item['fyrfs'].append(fyid[5:])
            yield Request(self.ajax.format(type=fyid[:5], id=fyid[5:]), meta={'key':item}, callback=self.parse_fysx)
        for sxid in sxids:
            item['sxids'].append(sxid[7:])
            item['sxmbs'].append(sxid[7:])
            item['sxrfs'].append(sxid[7:])
            yield Request(self.ajax.format(type=sxid[:7], id=sxid[7:]), meta={'key':item}, callback=self.parse_fysx)

    def parse_fysx(self, response):
        item = response.meta['key']
        ids = response.css('.contyishang > div > h2 > span::text').extract_first()
        speaker = response.xpath('.//img[@src="/img/speaker.png"]/..').extract_first()
        href = re.compile('<a href="http://.*?>', re.S)
        triangle = response.xpath('.//a[contains(@title,"收起")]').extract_first()
        temp = response.css('.contyishang').extract_first()
        try:
            temp = temp.replace(speaker, '')
        except:
            print(temp)
        mbs = re.sub(href,'',temp).replace(triangle,'').replace('</a>','')
        rfs = response.xpath('string(//div[@class="cankao"])').extract_first()
        typeid = response.css('a[href^="javascript"]::attr(href)').extract_first()
        tpid = re.search('(Shangxi|Fanyi){1}quan\(([0-9]{1,5})\)',typeid)
        ajax_type = tpid.group(1)
        ajax_id = tpid.group(2)
        if ajax_type == 'Fanyi':
            i = [i for i, x in enumerate(item['fyids']) if x == ajax_id][0]
            item['fyids'][i] = ids
            item['fymbs'][i] = mbs
            item['fyrfs'][i] = rfs
        elif ajax_type == 'Shangxi':
            i = [i for i, x in enumerate(item['sxids']) if x == ajax_id][0]
            item['sxids'][i] = ids
            item['sxmbs'][i] = mbs
            item['sxrfs'][i] = rfs
        if not ([x for x in item['fyids'] if x.isdigit()] or [x for x in item['sxids'] if x.isdigit()]):
            yield item

    def parse_mp3(self, response):
        item = response.meta['key']
        item['readurl'] = response.css('audio::attr(src)').extract_first()