import sys
sys.path.append('e:\\Python\\ir\\lab6')

import contextlib
import heapq
import jieba
import math
import os
import pickle as pkl
import re
import wordninja as wdnj
from elasticsearch import Elasticsearch
from operator import itemgetter
from string import punctuation
from utils import *

class ESIndex:
    def __init__(self, data_dir, data_out):
        with open(os.path.join(data_out, 'url_list.dict'), 'rb') as f:
            self.url_list = pkl.load(f)
        self.data_dir = data_dir
        self.data_out = data_out
        self.es = Elasticsearch([{'host':'127.0.0.1', 'port':9200}])
        self.url = 'http://localhost:9200'
        self._index_mapping = {
            "mappings": {
                "properties": {
                    "url": { "type": "integer" },
                    "text": {
                        "type": "text",
                        "index": True,
                        "analyzer": jieba,
                        "search_analyzer": jieba
                    },                   
                }
            }
        }
        self._gen_rank(10, 0.85)

    def _gen_index(self):
        # *.info index
        docs = []
        for home, dirs, files in os.walk(self.data_dir):
            for filename in files:
                if re.search('\.info', filename) != None:
                    docs.append(filename)
        cnt = 0
        tot = 0
        for doc in docs:
            # 0. read files
            f = open(self.data_dir + '/' + doc, encoding='utf-8')
            iid = re.sub('\.info', '', doc)
            words = "".join(f.read().split())
            f.close()
            cnt = cnt + 1
            # 1. delete all the useless info
            words = re.sub('[“”【】\[\]《》\<\>\'\"‘’（）\(\)]', '', words)
            words = re.sub('[，；\_\&\@。\,\.、：——\:\-\+\\ \/©]', '', words)
            # 2. create index for this url(doc)     
            if (((cnt - 1) % 1000) == 0):
                index_name = 'urls' + str(tot)
                print("CHANGE index: ", index_name)
                tot = tot + 1
                r = self.es.indices.create(index=index_name, body=self._index_mapping, ignore=400)
            # 3. insert each td_pairs
            r = self.es.index(index=index_name, body={'url': int(iid), 'text': words})
            if cnt % 50 == 0:
                print('@', cnt, "FIN")
        # doc analyze
        doc = 'doc_url.txt'
        f = open(self.data_dir + '/' + doc, encoding='utf-8')
        docs = f.read().split('\n')
        f.close()
        index_name = 'docs'
        cnt = 0
        r = self.es.indices.create(index=index_name, body=self._index_mapping, ignore=400)
        for doc in docs:
            # 1. take apart anc & 
            cnt = cnt + 1
            temp = doc.split()
            uid = temp[len(temp) - 1]
            anc = "".join(temp[:len(temp) - 1])
            # 2. delete & cut with Jieba
            anc = re.sub('[“”【】\[\]《》\<\>\'\"‘’（）\(\)]', '', anc)
            anc = re.sub('[，；\_\&\@。\,\.、：——\:\-\+\\ \/©]', '', anc)
            r = self.es.index(index=index_name, body={'url': int(uid), 'text': anc})
            print('@', cnt, "FIN")
        print("GEN_INDEX FINISH")

    def _gen_rank(self, max_loop, d):
        tot = len(self.url_list)
        sumy = [0] * tot
        self.rank = [1] * tot
        for j in range(0, max_loop):
            for cur in self.url_list:
                if cur >= tot:
                    continue
                ulist = self.url_list.get(cur)
                if ulist == None or len(ulist) == 0:
                    continue
                step = self.rank[cur] / len(ulist)
                for url in ulist:
                    if url >= tot:
                        continue
                    sumy[url] = sumy[url] + step
            for i in range(0, len(self.rank)):
                self.rank[i] = (d * (self.rank[i] + sumy[i]) + (1 - d) / len(ulist)) / 10
            sumy = [0] * tot
        for i in range(0, len(self.rank)):
            self.rank[i] = self.rank[i] * 10000
        self.rank[0] = self.rank[0] + 20