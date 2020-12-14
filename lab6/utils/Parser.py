import sys
sys.path.append('e:\\Python\\ir\\lab6')

import module.ESIndex as ESI
import os
import pickle as pkl
import random as rr
import re

class Parser:
    def __init__(self, data_dir, data_out):
        with open(os.path.join('account', 'account.dict'), 'rb') as f:
            self.account = pkl.load(f)
        with open(os.path.join('account', 'user_key.dict'), 'rb') as f:
            self.user_key = pkl.load(f)
        with open(os.path.join(data_out, 'url_id.dict'), 'rb') as f:
            self.url_id_map = pkl.load(f)
        with open(os.path.join(data_out, 'doc_id.dict'), 'rb') as f:
            self.doc_id_map = pkl.load(f)
        # load doc_url
        f = open(data_dir + '/doc_url.txt', encoding='utf-8')
        info = f.read().split('\n')
        self.doc_url = {}
        for item in info:
            strs = item.split()
            size = len(strs) - 1
            did = int(strs[size])
            strs = "".join(strs[:size])
            self.doc_url.setdefault(did, strs)
        f.close()
        # load url_anc
        f = open(data_dir + '/url_anc.txt', encoding='utf-8')
        info = f.read().split('\n')
        self.url_anc = {}
        for item in info:
            strs = item.split()
            size = len(strs) - 1
            uid = int(strs[size])
            strs = "".join(strs[:size])
            self.url_anc.setdefault(uid, strs)
        f.close()
        self.command = ''
        self.data_dir = data_dir
        self.data_out = data_out
        self.isLogin = False
        self.username = 'admin'
        self.password = ''
        self.url_pool = {}
        self.advice = []
    
    def addUser(self, username, password):
        ppass = self.account.get(username)
        if ppass != None:
            return False
        self.account.setdefault(username, password)
        self.user_key.setdefault(username, None)
        return True


    def checkLogin(self, username, password):
        ppass = self.account.get(username)
        if password != ppass:
            self.isLogin = False
            return False
        self.username = username
        self.password = password
        self.isLogin = True
        return True

    def fetch(self, html, esi, isDoc=False):
        """获取对应内容的URL和部分文字"""
        ans = []
        hlist = html['hits']['hits']
        for item in hlist:
            score = item.get('_score')
            info = item.get('_source')
            url = info.get('url')
            strs = info.get('text')
            if not isDoc:
                text = self.url_anc.get(url)
                url = self.url_id_map.__getitem__(url)
            else:
                text = self.doc_url.get(url)
                url = self.doc_id_map.__getitem__(url)
            uid = self.url_id_map.__getitem__(url)
            if uid < len(esi.rank):
                rk = esi.rank[uid]
            else:
                rk = 0  
            score = 0.85 * score + 0.15 * rk
            # define as user's like
            if self.username != 'admin' and not isDoc:
                his = self.user_key.get(self.username)
                ulike = his.get('url')
                tlike = his.get('term')
                cid = self.url_id_map.__getitem__(url)        
                ts = esi.url_list.get(cid)
                for item in ulike:
                    ms = esi.url_list.get(item)
                    if len(ts & {item}) == 1:
                        score = score + 1
                    if len(ms & {cid}) == 1:
                        score = score + 1
            ans.append([score, text, url])
        if self.username != 'admin':
            his = self.user_key.get(self.username)
            ulike = his.get('url')
            tlike = his.get('term')
            # add for advice
            self.advice = []
            for j in range(0, 5):
                t = rr.randint(0, len(ulike) - 1)
                ulist = list(esi.url_list.get(t))
                t = rr.randint(0, len(ulist) - 1)
                info = self.url_anc.get(ulist[t])
                link = self.url_id_map.__getitem__(ulist[t])
                if info != None:
                    self.advice.append([info, link])
        # add for url_pool
        llist = []
        for item in ans:
            url = self.url_id_map.__getitem__(item[2])
            llist.append(url)
        temp = self.url_pool.get(self.command)
        if temp == None:
            self.url_pool.setdefault(self.command, [llist])
        else:
            temp.append(llist)
            self.url_pool.setdefault(self.command, temp)
        return ans
    
    def getT(self, command):
        code = -1      
        if command == '':
            return 0
        command = command.split()
        l = len(command) - 1
        print(command)    
        if command[l][0] != '-':
            print("站内查询")
            code = 1
            self.command = "".join(command)
        elif command[l][1] == 'q':
            print("站内查询")
            code = 1
            self.command = "".join(command[:l])
        elif command[l][1] == 'd':
            print("文档查询")
            code = 2
            self.command = "".join(command[:l])
        elif command[l][1] == 'l':
            print("日志记录")
            code = 3
            self.command = "".join(command[:l])
        elif command[l][1] == 'f':
            print("快照")
            code = 4
            self.command = "".join(command[:l])
        return code

    def save(self):
        if self.isLogin:
            keys = self.user_key.get(self.username)
            ulike = keys.get('url')
            tlike = keys.get('term')
            for item in self.url_pool:      
                temp = self.url_pool.get(item)
                size = len(temp) - 1
                llist = temp[size]
                if ulike == None:
                    ulike = []
                if tlike == None:
                    tlike = []
                tlike.append(item)
                for i in range(0, len(llist)):
                    ulike.append(llist[i])
                ulike = list(set(ulike))
                tlike = list(set(tlike))
                temp = {'url': ulike, 'term': tlike}
                self.user_key.setdefault(self.username, temp)
        with open(os.path.join('account', 'account.dict'), 'wb') as f:
            pkl.dump(self.account, f)
        with open(os.path.join('account', 'user_key.dict'), 'wb') as f:
            pkl.dump(self.user_key, f)

    def helper(self):
        print('NKU Search Engine 1.0 Helper')  
        print('---')
        print('\nBasic Format: <Query> [-param] | <KEY_WORD>')
        print('<KEY_WORD>')
        print('exit | quit')
        print('\t退出程序')
        print('help')
        print('\t帮助手册')
        print('login <Username> <Password>')
        print('\t登录（用户名密码应当匹配数据库内容）')
        print('regist <Username> <Password>')
        print('\t注册新用户')
        print('<Query>')
        print('\t支持中英文双语')
        print('[-param]')
        print('-d')
        print('\t文档查询')
        print('-f')
        print('\t网页快照')
        print('-l')
        print('\t保存日志')
        print('-q')
        print('\t站内查询（支持单词，短语，标准正则（采用Lucene语法）')
