import array
import BSBIIndex
import InvertedIndex as ii
import os
import pickle as pkl
import sys
import timeit
import urllib.request
import util
import zipfile

data_dir = 'pa1-data'
data_out = 'output_dir'
data_vbout = 'output_vbdir'
data_url = 'http://web.stanford.edu/class/cs276/pa/pa1-data.zip'
testIdMap = util.IdMap()
toy_dir = 'toy-data'
toy_out = 'toy_output_dir'

bisi = BSBIIndex.BSBIIndex(data_dir=data_dir, output_dir=data_out, index_name='data')
bisi_vb = BSBIIndex.BSBIIndex(data_dir=data_dir, output_dir=data_vbout, index_name='vb', postings_encoding=util.CompressedPostings)

def download():
    urllib.request.urlretrieve(data_url, data_dir+'.zip')
    zip_ref = zipfile.ZipFile(data_dir+'.zip', 'r')
    zip_ref.extractall()
    zip_ref.close()  

def get_files(dir):
    file_list = []
    for home, dirs, files in os.walk(dir):
        for filename in dirs:
            file_list.append(filename)
    return file_list

def init():
    if not os.path.exists('pa1-data'):
        print("下载数据集...")
        download()
    print("数据集初始化成功")
    try:
        # 索引
        os.mkdir('output_dir')
    except FileExistsError:
        print("索引文件夹已存在")
    try:
        # VB压缩索引
        os.mkdir('output_vbdir')
    except FileExistsError:
        print("VB索引已存在")
    try: 
        # 测试文件索引
        os.mkdir('toy_output_dir')
    except FileExistsError:
        print("测试索引文件夹已存在")
    try: 
        # 测试文件输出
        os.mkdir('tmp')
    except FileExistsError:
        print("测试输出文件夹已存在")
    if not os.path.exists('output_dir/data.index'):
        print("创建索引...（整个过程可能需要 15-20 min）")
        bisi.index()
    print("索引（未压缩）创建成功")
    if not os.path.exists('output_vbdir/vb.index'):
        print("创建VB索引...（整个过程可能需要 15-20 min）")
        bisi_vb.index()
    print("VB索引创建成功")

if __name__ == "__main__":
    init()
    #encoding = util.CompressedPostings.encode([824, 829, 215406])
    #print(encoding)
    #print(util.CompressedPostings.decode(encoding))
    #encoding = util.UncompressedPostings.encode([824, 829, 215406])
    #print(encoding)
    #print(util.UncompressedPostings.decode(encoding))
    while True:
        query = input("请输入查询内容）：")
        if query == "0":
            break
        result = bisi.retrieve(query)
        if result == []:
            print("查询词不存在，请重新输入")
            continue
        print(result)
        