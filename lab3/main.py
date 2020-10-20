import math
import nltk
import numpy as np
import os
import re
from collections import defaultdict
from operator import itemgetter
from string import punctuation

url = "E:\\python\\IR\\lab1\\files"
# 构造每种类型词的正则表达式，()代表分组，?P<NAME>为组命名
token_or = r'(?P<OR>\|\|)'
token_not = r'(?P<NOT>\!)'
token_word = r'(?P<WORD>[a-zA-Z]+)'
token_and = r'(?P<AND>&&)'
token_lp = r'(?P<LP>\()'
token_rp = r'(?P<RP>\))'
token_q = r'(?P<Q>\")'
lexer = re.compile('|'.join([token_or, token_not, token_word,
                            token_and, token_lp, token_rp, 
                            token_q]))  # 编译正则表达式

def get_files(dir, type='.txt'):
    file_list = []
    for home, dirs, files in os.walk(dir):
        for filename in files:
            if type in filename:
                file_list.append(os.path.join(home, filename))
    return file_list

def get_tokens(query):
    tokens = []  # tokens中的元素类型为(token, token类型)
    for token in re.finditer(lexer, query):
        tokens.append((token.group(), token.lastgroup))
    return tokens

def get_words(text):
    text = re.sub(r"[{}]+".format(punctuation), " ", text)  # 将标点符号转化为空格
    text = text.lower()                                     # 全部字符转为小写
    words = nltk.word_tokenize(text)                        # 分词
    # words = list(set(words))     
    return words

class BoolRetrieval:
    def __init__(self, index_path=''):
        if index_path == '':
            self.index = defaultdict(list)
            self.bi_index = defaultdict(list)
            self.tri_gram = defaultdict(list)
            self.sound = defaultdict(list)
        # 已有构建好的索引文件
        else:
            data = np.load(index_path, allow_pickle=True)
            # print(data)
            self.files = data['files'][()]
            self.index = data['index'][()]
            self.bi_index = data['bi_index'][()]
            self.tri_gram = data['tri_gram'][()]
            self.sound = data['sound'][()]
        self.query_tokens = []
        self.empty_tokens = []

    def build_index(self, text_dir):
        self.files = get_files(text_dir)  # 获取所有文件名
        for num in range(0, len(self.files)):
            f = open(self.files[num], encoding='utf-8')
            text = f.read()
            words = get_words(text)  # 分词
            # 构建倒排索引
            for i in range(0, len(words)):
                diction = self.index[words[i]]
                if not i + 1 == len(words):
                    key = words[i] + '+' + words[i + 1]
                    bi_diction = self.bi_index[key]
                    # 双词索引
                    update = False
                    for result in bi_diction:
                        if result[0] == num:
                            update = True
                            result.append(i)
                            break
                    if not update:
                        result = [num, i]
                        key = words[i] + '+' + words[i + 1]
                        self.bi_index[key].append(result)
                # 单词索引
                update = False
                for result in diction:
                    if result[0] == num:
                        update = True
                        result.append(i)
                        break
                if not update:
                    result = [num, i]
                    self.index[words[i]].append(result)    
                # 3-gram索引
                for j in range(0, len(words[i])):
                    if j + 3 > len(words[i]):
                        break
                    gram = words[i][j : j + 3]
                    diction = self.tri_gram[gram]
                    if words[i] not in self.tri_gram[gram]:
                        self.tri_gram[gram].append(words[i])
                # 处理开头和结尾
                gram = words[i][0 : 2]
                diction = self.tri_gram[gram]
                if words[i] not in self.tri_gram[gram]:
                    self.tri_gram[gram].append(words[i])
                gram = words[i][len(words[i]) - 2 : len(words[i])]
                diction = self.tri_gram[gram]
                if words[i] not in self.tri_gram[gram]:
                    self.tri_gram[gram].append(words[i]) 
                # 声音索引
                result = self.find_sound(words[i])
                if words[i] not in self.sound[result]:
                    self.sound[result].append(words[i])
        # print(self.files, self.index)
        np.savez('index.npz', files=self.files, index=self.index, bi_index=self.bi_index, tri_gram=self.tri_gram, sound=self.sound)

    def check_parentheses(self, p, q):
        """
        判断表达式是否为 (expr)
        整个表达式的左右括号必须匹配才为合法的表达式
        返回True或False
        """
        if self.query_tokens[p][1] == 'LP' and self.query_tokens[q][1] == 'RP':
            s = self.query_tokens[p + 1 : q]
            num = 1
            for token in s:
                if token[1] == 'RP':
                    if num == 1:
                        return False
                    num = num - 1
                if token[1] == 'LP':
                    num = num + 1
            return True    
        return False

    def check_quotation(self, p, q):
        if self.query_tokens[p][1] == 'Q' and self.query_tokens[q][1] == 'Q':
            result = True
            for i in range(p + 1, q):
                if not self.query_tokens[i][1] == 'WORD':
                    result = False
                    break
            return result
        return False

    def edit_length(self, src, tar):
        """
        计算编辑距离
        """
        x = len(src) + 1
        y = len(tar) + 1
        ans = []
        # 初始化 
        for i in range(0, x):
            line = []
            for j in range(0, y):
                line.append(0)
            ans.append(line)
        for i in range(0, x):
            ans[i][0] = i
        for j in range(0, y):
            ans[0][j] = j
        for i in range(1, x):
            for j in range(1, y):
                ans[i][j] = min(ans[i - 1][j], ans[i][j - 1], ans[i - 1][j - 1])
                if src[i - 1] != tar[j - 1]:
                    ans[i][j] = ans[i][j] + 1
        return ans[x - 1][y - 1]

    # 递归解析布尔表达式，p、q为子表达式左右边界的下标
    def evaluate(self, p, q):
        # 解析错误
        if p > q:
            return []
        # 单个token，一定为查询词
        elif p == q:
            files = self.index[self.query_tokens[p][0]]
            result = []
            for item in files:
                result.append(item[0])
            if result == []:
                self.empty_tokens.append(p)
            return result
        # 去掉外层括号
        elif self.check_parentheses(p, q):
            return self.evaluate(p + 1, q - 1)
        # 短语检查
        elif self.check_quotation(p, q):
            files = self.phrase_search(p + 1, q - 1)
            result = []
            for item in files:
                result.append(item[0])
            return result
        else:
            op = self.find_operator(p, q)
            if op == -1:
                return []
            # files1为运算符左边得到的结果，files2为右边
            if self.query_tokens[op][1] == 'NOT':
                files1 = []
            else:
                files1 = self.evaluate(p, op - 1)
            files2 = self.evaluate(op + 1, q)
            return self.merge(files1, files2, self.query_tokens[op][1])

    def evaluate_length(self, p, q):
        if p > q:
            return 0
        if p == q:
            # 单个单词
            token = self.query_tokens[p]
            return len(self.index[token[0]])
        elif self.check_parentheses(p, q):
            # 左右括号匹配
            return self.evaluate_length(p + 1, q - 1)
        elif self.check_quotation(p, q):
            return self.phrase_length(p + 1, q - 1)
        else:
            op = self.find_operator(p, q)
            if op == -1:
                return 0
            # files1为运算符左边得到的结果，files2为右边
            if self.query_tokens[op][1] == 'NOT':
                len1 = len(self.files)
            else:
                len1 = self.evaluate_length(p, op - 1)
            len2 = self.evaluate_length(op + 1, q)
            return self.merge_length(len1, len2, self.query_tokens[op][1])

    def find_operator(self, p, q):
        s = self.query_tokens[p : q + 1]
        length = []
        op = []
        f = 0
        level = 3                       # 运算等级：2 for !, 1 for &&, 0 for ||
        num = -1
        for token in s:
            num = num + 1
            if f != 0:
                if token[1] == 'RP':    # 减少可匹配的括号区间
                    f = f - 1
                if token[1] == 'LP':    # 增加可匹配的括号区间
                    f = f + 1
                continue
            else:
                if token[1] == 'NOT' and level > 2:
                    level = 2
                    op.append(num + p)
                if token[1] == 'AND':
                    if level > 1:
                        level = 1  
                        op.clear()
                        length.clear()
                    if level == 1:
                        l = p if len(op) == 0 else op[len(op) - 1] + 1
                        op.append(num + p)
                        temp = self.evaluate_length(l, num + p - 1)
                        length.append(temp)
                if token[1] == 'OR':
                    if level > 0:
                        level = 0
                        op.clear()
                        length.clear()
                    if level == 0:
                        l = p if len(op) == 0 else op[len(op) - 1] + 1
                        op.append(num + p)
                        temp = self.evaluate_length(l, num + p - 1)
                        length.append(temp)
                if token[1] == 'LP':
                    f = f + 1           # 增加可匹配的括号区间
                    continue
        if len(length) == 0:
            return op.pop(0)
        temp = self.evaluate_length(op[len(op) - 1] + 1, q)
        length.append(temp)
        ans = op[0]
        minn = length[1] * length[0] if level == 1 else length[1] + length[0]
        for i in range(0, len(length) - 1):
            temp = length[i] * length[i + 1] if level == 1 else length[i] + length[i + 1]
            if temp < minn:
                minn = temp
                ans = op[i]
        return ans

    def find_sound(self, word):
        result = word[0]
        for j in range(1, len(word)):
            ch = word[j]
            if ch in ['b', 'f', 'p', 'v']:
                result = result + '1'
            elif ch in ['c', 'g', 'j', 'k', 'q', 's', 'x', 'z']:
                result = result + '2'
            elif ch == 'd' or ch == 't':
                result = result + '3'
            elif ch == 'l':
                result = result + '4'
            elif ch == 'm' or ch == 'n':
                result = result + '5'
            elif ch == 'r':
                result = result + '6'
        for j in range(len(result), 4):
            result = result + '0'
        result = result[0 : 4]
        return result

    def find_words(self, word, num):
        num = int(num / 2)
        result = []
        isSorted = False
        for i in range(0, len(word)):
            if i + 3 > len(word):
                break
            gram = word[i : i + 3]
            diction = self.tri_gram[gram]
            for item in diction:
                if not isSorted and len(result) == num:
                    result.sort(key=itemgetter(1, 0))
                    isSorted = True
                isExist = False
                for elem in result:
                    if item == elem[0]:
                        isExist = True
                        break
                if isExist:
                    continue
                length = self.edit_length(word, item)
                if not isSorted :
                    result.append([item, length])
                else:
                    # 满num个数之后的更新
                    for j in range(0, len(result)):
                        if length < result[j][1]:
                            result[j + 1 : num] = result[j : num - 1]
                            result[j] = [item, length]
                            break 
        # 开头和结尾的处理
        gram = word[0 : 2]
        diction = self.tri_gram[gram]
        for item in diction:
            if not isSorted and len(result) == num:
                result.sort(key=itemgetter(1, 0))
                isSorted = True
            length = self.edit_length(word, item)
            if [item, length] in result:
                continue
            if not isSorted:
                result.append([item, length])
            else:
                # 满num个数之后的更新
                for j in range(0, len(result)):
                    if length < result[j][1]:
                        result[j + 1 : num] = result[j : num - 1]
                        result[j] = [item, length]
                        break 
        gram = word[len(word) - 2 : len(word)]
        diction = self.tri_gram[gram]
        for item in diction:
            if not isSorted and len(result) == num:
                result.sort(key=itemgetter(1, 0))
                isSorted = True
            length = self.edit_length(word, item)
            if [item, length] in result:
                continue
            if not isSorted:
                result.append([item, length])
            else:
                # 满num个数之后的更新
                for j in range(0, len(result)):
                    if length < result[j][1]:
                        result[j + 1 : num] = result[j : num - 1]
                        result[j] = [item, length]
                        break 
        ans = []
        # 检查是否有仅修改1-2次的词项
        for item in result:
            if item[1] > 2:
                break
            ans.append(item[0])
        if ans == []:
            for item in result:
                ans.append(item[0])
        # 声音查询结果添加
        num = num * 2
        sid = self.find_sound(word)
        diction = self.sound[sid]
        for item in diction:
            if item not in ans:
                ans.append(item)
            if len(ans) == num:
                break
        return ans

    def merge(self, files1, files2, op_type):
        """
        根据运算符对进行相应的操作
        在Python中可以通过集合的操作来实现
        但为了练习算法，请遍历files1, files2合并
        """
        result = []

        if op_type == 'AND':
            # result = list(set(files1) & set(files2))
            p1 = 0
            p2 = 0
            s1 = int(math.sqrt(len(files1)))
            s2 = int(math.sqrt(len(files2)))
            while (p1 < len(files1) and p2 < len(files2)):
                if files1[p1] == files2[p2]:
                    result.append(files1[p1])
                    p1 = p1 + 1
                    p2 = p2 + 1
                elif files1[p1] < files2[p2]:
                    if (p1 + s1 >= len(files1) or files1[p1 + s1] > files2[p2]):
                        p1 = p1 + 1
                    else:
                        p1 = p1 + s1
                else:
                    if (p2 + s2 >= len(files2) or files2[p2 + s2] > files1[p1]):
                        p2 = p2 + 1
                    else:
                        p2 = p2 + s2
        elif op_type == "OR":
            # result = list(set(files1) | set(files2))
            p1 = 0
            p2 = 0
            while (p1 < len(files1) and p2 < len(files2)):
                if files1[p1] == files2[p2]:
                    result.append(files1[p1])
                    p1 = p1 + 1
                    p2 = p2 + 1
                elif files1[p1] < files2[p2]:
                    result.append(files1[p1])
                    p1 = p1 + 1
                else:
                    result.append(files2[p2])
                    p2 = p2 + 1
            if p1 == len(files1):
                for i in range(p2, len(files2)):
                    result.append(files2[i])
            elif p2 == len(files2):
                for i in range(p1, len(files1)):
                    result.append(files1[i])
        elif op_type == "NOT":
            # result = list(set(range(0, len(self.files))) - set(files2))
            p0 = 0
            p2 = 0
            while (p0 < len(self.files) and p2 < len(files2)):
                if p0 == files2[p2]:
                    p0 = p0 + 1
                elif p0 > files2[p2]:
                    p2 = p2 + 1
                else:
                    result.append(p0)
                    p0 = p0 + 1
            if p2 == len(files2):
                while p0 < len(self.files):
                    result.append(p0)
                    p0 = p0 + 1
        return result

    def merge_length(self, len1, len2, op_type):
        if op_type == 'AND':
            return len1 * len2
        elif op_type == 'OR':
            return len1 + len2
        elif op_type == 'NOT':
            return len1 * len2
        return 0

    def merge_phrase(self, files1, files2):
        if files1 == []:
            return files2
        result = []
        p1 = 0
        p2 = 0
        l1 = len(files1)
        l2 = len(files2)
        while p1 < l1 and p2 < l2:
            list1 = files1[p1]
            list2 = files2[p2]
            if list1[0] == list2[0]:
                # 在一个文件下
                temp = [p1]
                t1 = 1
                t2 = 1
                ll1 = len(list1)
                ll2 = len(list2)
                while t1 < ll1 and t2 < ll2:
                    if list1[t1] + 2 == list2[t2]:
                        temp.append(list2[t2])
                        t1 = t1 + 1
                        t2 = t2 + 1
                    elif list1[t1] + 2 < list2[t2]:
                        t1 = t1 + 1
                    else:
                        t2 = t2 + 1
                if not len(temp) == 1:
                    result.append(temp)
                p1 = p1 + 1
                p2 = p2 + 1
            elif list1[0] < list2[0]:
                p1 = p1 + 1
            else:
                p2 = p2 + 1
        return result

    def phrase_length(self, p, q):
        result = self.phrase_search(p, q)
        return len(result)

    def phrase_search(self, p, q):
        if p == q:
            # 单词
            key = self.query_tokens[q][0]
            result = self.index[key]
            if result == []:
                self.empty_tokens.append(p)
            return result
        elif p + 1 == q:
            # 双词
            key = self.query_tokens[p][0] + '+' + self.query_tokens[q][0]
            result = self.index[self.query_tokens[p][0]]
            if result == []:
                self.empty_tokens.append(p)
            result = self.index[self.query_tokens[q][0]]
            if result == []:
                self.empty_tokens.append(q)  
            result = self.bi_index[key] 
            return result
        else:
            # 按序遍历
            result = []
            i = p
            while i <= q:
                if i == q:
                    files2 = self.phrase_search(i, q)
                    result = self.merge_phrase(result, files2)
                    break
                key = self.query_tokens[i][0] + '+' + self.query_tokens[i + 1][0]
                files2 = self.bi_index[key]
                result = self.merge_phrase(result, files2)
                if result == []:
                    return []
                i = i + 2
            return result

    def search(self, query):
        self.query_tokens = get_tokens(query)  # 获取查询的tokens
        self.empty_tokens = [] # 清空无效单词列表
        # print(self.query_tokens)
        result = []
        # 将查询得到的文件ID转换成文件名
        for num in self.evaluate(0, len(self.query_tokens) - 1):
            result.append(self.files[num])
        if result == []:
            self.empty_tokens = list(set(self.empty_tokens))
            # print(self.empty_tokens)
            if self.empty_tokens == []:
                return []
            print("词项不存在或拼写错误，您可能想找：")
            ifAns = False
            for i in self.empty_tokens:
                word = self.query_tokens[i][0]
                others = self.find_words(word, 10)
                if not others == []:
                    ifAns = True
                    print("<", word, ">")
                    print(others)
            if not ifAns:
                print("无拼写纠正结果")
        return result

if __name__ == "__main__":
    if not os.path.exists('index.npz'):   
        br = BoolRetrieval()
        br.build_index(url)
    else:
        br = BoolRetrieval('index.npz')
    # print(br.index)
    # print(br.bi_index)
    # print(br.tri_gram)
    # print(br.sound)      
    while True:
        query = input("请输入与查询（与||，或&&，非！）：")
        if query == "0":
            break
        result = br.search(query)
        if not result == []:
            print(result)