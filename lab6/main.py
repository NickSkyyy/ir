import jieba
import json
import module.ESIndex as ESI
import os
import pickle as pkl
import random as rr
import re
import requests
import time
import wordninja
from elasticsearch import Elasticsearch
from utils import *

base_url = 'E:/Python/ir/lab6'
data_dir = 'data_dir'
data_out = 'data_out'
index_url = 'localhost'
index_port = 9200
logs_dir = 'logs'
max_index_bd = 20

cur_index_bd = 0
es = Elasticsearch([{'host':index_url, 'port':index_port}])
esi = ESI.ESIndex(data_dir, data_out)
pp = Parser.Parser(data_dir, data_out)
pre_index_bd = 0

if __name__ == "__main__":
    print("NKU Search Engine 1.0 (ir lab6 exercise)")
    print("@author Xiaorui Qi")  

    while True:
        command = input(">>> ")
        if command == 'quit' or command == 'exit':
            # EXIT / QUIT
            break
        temp = command.split()
        if not pp.isLogin and len(temp) == 3 and temp[0] == 'login':
            # LOGIN
            username = temp[1]
            password = temp[2]
            if pp.checkLogin(username, password):
                print('Welcome ', username)
                tt = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
                rtt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                trace_url = logs_dir + '/' + username + '/' + tt + '.log'
                trace = open(trace_url, "w+", encoding='utf-8')
            else:
                print('Wrong Username or Password')
            continue
        if command == 'help':
            # HELPER
            pp.helper()
            os.system('pause')
            continue
        if not pp.isLogin and len(temp) == 3 and temp[0] == 'regist':
            # REGIST
            username = temp[1]
            password = temp[2]
            if pp.addUser(username, password):
                print('Regist user ', username, 'success')
            else:
                print('Duplicated username')
            continue
        code = pp.getT(command)
        orin_c = command
        command = re.sub('\-(.)*', '', command)
        command = re.sub(' ', '', command)
        if code == -1:
            print("Wrong syntax")
            print("Please try \'help\' to get start")
        elif code == 0:
            continue
        elif code == 1:
            # 站内查询
            pre_index_bd = cur_index_bd
            while cur_index_bd == pre_index_bd:
                cur_index_bd = rr.randint(1, max_index_bd) - 1
            index_name = 'urls' + str(cur_index_bd)
            r = es.search(index=index_name, q='term="' + command + '"', size=5, sort='_score: desc')
            ans = pp.fetch(r, esi, False)
            if pp.isLogin:
                rtt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                trace.write('[' + rtt + '][' + pp.username + '] ')
                trace.write(orin_c + '\n')
                trace.write('[' + rtt + '][GET]\n')
                for item in ans:
                    trace.write('{\n')
                    trace.write('\t_score: ' + str(item[0]) + '\n')
                    trace.write('\t_title: ' + item[1] + '\n')
                    trace.write('\t_url: ' + item[2] + '\n')
                    trace.write('}\n')
            for item in ans:
                print(item)
            if len(pp.advice) > 0:
                print('是否还在寻找')
                for item in pp.advice:
                    print(item)
        elif code == 2:
            # 文档查询
            r = es.search(index='docs', q='term="' + command + '"', size=5, sort='_score: desc')
            ans = pp.fetch(r, esi, True)
            if pp.isLogin:
                rtt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                trace.write('[' + rtt + '][' + pp.username + '] ')
                trace.write(orin_c + '\n')
                trace.write('[' + rtt + '][GET]\n')
                for item in ans:
                    trace.write('{\n')
                    trace.write('\t_score: ' + str(item[0]) + '\n')
                    trace.write('\t_title: ' + item[1] + '\n')
                    trace.write('\t_url: ' + item[2] + '\n')
                    trace.write('}\n')
            for item in ans:
                print(item)
            if len(pp.advice) > 0:
                print('是否还在寻找')
                for item in pp.advice:
                    print(item)
        elif code == 3:
            # 日志记录
            tt = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            rtt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            f = open(logs_dir + '/' + pp.username + '/' + tt + '.log', "w+", encoding='utf-8')
            f.write('[' + rtt + '][' + pp.username + '] ')
            f.write(orin_c + '\n')
            pre_index_bd = cur_index_bd
            while cur_index_bd == pre_index_bd:
                cur_index_bd = rr.randint(1, max_index_bd) - 1
            index_name = 'urls' + str(cur_index_bd)
            r = es.search(index=index_name, q='term="' + command + '"', size=5, sort='_score: desc')
            rtt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            ans = pp.fetch(r, esi, False)
            f.write('[' + rtt + '][GET]\n')
            for item in ans:
                f.write('{\n')
                f.write('\t_score: ' + str(item[0]) + '\n')
                f.write('\t_title: ' + item[1] + '\n')
                f.write('\t_url: ' + item[2] + '\n')
                f.write('}\n')
            if pp.isLogin:
                rtt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                trace.write('[' + rtt + '][' + pp.username + '] ')
                trace.write(orin_c + '\n')
                trace.write('[' + rtt + '][GET]\n')
                for item in ans:
                    trace.write('{\n')
                    trace.write('\t_score: ' + str(item[0]) + '\n')
                    trace.write('\t_title: ' + item[1] + '\n')
                    trace.write('\t_url: ' + item[2] + '\n')
                    trace.write('}\n')           
            for item in ans:
                print(item)
            print('日志已保存')
            f.close()
        elif code == 4:
            # 网页快照
            pre_index_bd = cur_index_bd
            while cur_index_bd == pre_index_bd:
                cur_index_bd = rr.randint(1, max_index_bd) - 1
            index_name = 'urls' + str(cur_index_bd)      
            r = es.search(index=index_name, q='term="' + command + '"', size=5, sort='_score: desc', body={'highlight': {'fields': {'text': {}}}})
            tt = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
            ans = pp.fetch(r, esi, False)
            f = open(data_out + '/' + tt + '.html', "w+", encoding='utf-8')
            f.write(json.dumps(r, ensure_ascii=False))
            f.close()
            if pp.isLogin:
                rtt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                trace.write('[' + rtt + '][' + pp.username + '] ')
                trace.write(orin_c + '\n')
                trace.write('[' + rtt + '][GET]\n')
                trace.write(json.dumps(r, ensure_ascii=False))
            print('快照已加载')
            for item in ans:
                url = pp.url_id_map.__getitem__(item[1])
                if url != None:
                    print('本地原码：./' + data_dir + '/' + str(url) + '.info')
    if pp.isLogin:
        print('本次系统日志已记录：./' + trace_url)
    pp.save()
    print('Thanks for using!')