# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import os
import re
import requests
from scrapy.exceptions import DropItem

class Mp3Pipeline(object):
    def __init__(self):
        self.path = 'D:\\MyProject\\learnPython\\epub\\poem\\mp3s\\{file}.mp3'
    def process_item(self, item, spider):
        if item['readid']:
            if not os.path.exists(self.path.format(file=item['readid'])):
                try:
                    data = requests.get(item['readurl'])
                except requests.RequestException:
                    print('###### 链接不存在，继续下载下一首 ######')
                with open(self.path.format(file=item['readid']), 'wb') as f:
                    f.write(data.content)

class PoemrPipeline(object):
    def __init__(self):
        self.path = 'D:\\MyProject\\learnPython\\epub\\poem\\poems\\{file}.txt'
        self.list_r = '“”\"\'《》、<>'
        self.drop_list = [' ', '及']  # 清除作者项冗余，还原真实作者名

    def repl(self, matchobj):
        if self.list_r.find(matchobj.group(0)) != -1:
            if self.list_r.find(matchobj.group(0)) in range(3):
                return ''
            return matchobj.group(0)
        else:
            return matchobj.group(0) + '\n'

    def repl_2(self, matchobj):
        return '<br/>' + matchobj.group(0)

    def ispoem(self, obj):
        poem_piece = re.split('[~·,，.。!！、?？:：;；\"\'<>“‘’”《》]', obj.replace('\n',''))
        while '' in poem_piece:
            poem_piece.remove('')
        for i, itm in enumerate(poem_piece):
            for j, jtm in enumerate(poem_piece, i):
                if len(jtm) != len(itm):
                    return re.sub('[.。!！?？;；\"\'“”《》<>]', self.repl, obj)
        else:
            return re.sub('[,，.。!！、?？:：;；\"\'“”《》<>]', self.repl, obj)

    def process_item(self, item, spider, status=0): #修改status数值切换保存txt与否
        if status == 1:
            if item['title']:
                title = re.sub('[\\\\/:*?\"<>|]', '-', item['title'])
                if not os.path.exists(self.path.format(file=title)):
                    if item['plain'] and item['dynasty'] and item['poet']:
                        content = re.sub('[\(（].*?[\)）]', '', item['plain'].replace('\u3000\u3000',''), re.S).strip()
                        content = '\n' + self.ispoem(content)
                        content = content.replace('\n', '\n\u3000\u3000')
                        content = '\u3000\u3000' + item['title'] + '\n\u3000\u3000' + item['dynasty'] + ':' + item['poet'] + '\n' + content
                        with open(self.path.format(file=title), 'w', encoding='utf-8') as wrpoem:
                            wrpoem.write(content)
                return item
            else:
                return DropItem('Missing Title')
        else:
            if item['title']:
                if item['poet']:
                    for i, x in enumerate(self.drop_list):
                        if x in item['poet']:
                            item['poet'] = item['poet'].split(x)[0]
                return item
            else:
                return DropItem('Missing Title')

class PoetPipeline(object):
    def process_item(self, item, spider):
        if item['poetName']:
            return item
        else:
            return DropItem('Missing Title')

class MongoPipeline(object):
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri= crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def process_item(self, item, spider):
        name = item.__class__.__name__
        self.db[name].insert(dict(item))
        return item

    def close_spider(self, spider):
        self.client.close()