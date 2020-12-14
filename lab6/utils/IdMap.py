class IdMap:
    """字符串映射表"""
    def __init__(self):
        self.str_to_id = {}
        self.id_to_str = []
        
    def __len__(self):
        return len(self.id_to_str)
        
    def _get_str(self, i):
        return self.id_to_str[i]
        
    def _get_id(self, s):
        ans = self.str_to_id.get(s)
        if ans == None:
            p = self.__len__()
            self.id_to_str.append(s)
            self.str_to_id.setdefault(s, p)
            return p
        else:
            return ans
            
    def __getitem__(self, key):
        """获取key对应的str/id"""
        if type(key) is int:
            return self._get_str(key)
        elif type(key) is str:
            return self._get_id(key)
        else:
            raise TypeError

    def __have__(self, s):
        """判断是否存在字符串s"""
        return self.str_to_id.get(s)