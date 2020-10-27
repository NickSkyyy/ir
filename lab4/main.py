import array
import contextlib
import os
import pickle as pkl
import sys
import timeit
import urllib.request
import util
import zipfile

data_dir = 'pa1-data'
data_url = 'http://web.stanford.edu/class/cs276/pa/pa1-data.zip'
testIdMap = util.IdMap()
toy_dir = 'toy-data'

def download():
    urllib.request.urlretrieve(data_url, data_dir+'.zip')
    zip_ref = zipfile.ZipFile(data_dir+'.zip', 'r')
    zip_ref.extractall()
    zip_ref.close()  

def init():
    try:
        # 索引
        os.mkdir('output_dir')
    except FileExistsError:
        print("索引文件夹已存在")
        pass
    try: 
        # 测试文件索引
        os.mkdir('toy_output_dir')
    except FileExistsError:
        print("测试索引文件夹已存在")
        pass
    try: 
        # 测试文件输出
        os.mkdir('tmp')
    except FileExistsError:
        print("测试输出文件夹已存在")
        pass
    
if __name__ == "__main__":
    if not os.path.exists('pa1-data'):
        print("下载数据集...")
        download()
    print("数据集初始化成功")
    init()