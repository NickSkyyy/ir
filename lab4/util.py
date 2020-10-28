import array

class CompressedPostings:
    #If you need any extra helper methods you can add them here 
    ### Begin your code
    def getBin(self, num):
        if num == 0:
            return ['10000000']
        result = []
        isEnd = True
        while not num == 0:
            ans = num % (1 << 7)
            if isEnd:
                result.append('1{:07b}'.format(ans))
                isEnd = False
            else:
                result.insert(0, '{:08b}'.format(ans))
            num = num >> 7
        return result
    ### End your code
    
    @staticmethod
    def encode(postings_list):
        """Encodes `postings_list` using gap encoding with variable byte 
        encoding for each gap
        
        Parameters
        ----------
        postings_list: List[int]
            The postings list to be encoded
        
        Returns
        -------
        bytes: 
            Bytes reprsentation of the compressed postings list 
            (as produced by `array.tobytes` function)
        """
        ### Begin your code
        if postings_list == []:
            return array.array('B', []).tobytes()
        result = []
        pre = postings_list[0]
        for item in CompressedPostings().getBin(pre):
            result.append(int(item, 2))
        for i in range(1, len(postings_list)):
            p = postings_list[i] - pre
            for item in CompressedPostings().getBin(p):
                result.append(int(item, 2))
            pre = pre + p
        return array.array('B', result).tobytes()
        ### End your code

        
    @staticmethod
    def decode(encoded_postings_list):
        """Decodes a byte representation of compressed postings list
        
        Parameters
        ----------
        encoded_postings_list: bytes
            Bytes representation as produced by `CompressedPostings.encode` 
            
        Returns
        -------
        List[int]
            Decoded postings list (each posting is a docIds)
        """
        ### Begin your code
        decoded_postings_list = array.array('B')
        decoded_postings_list.frombytes(encoded_postings_list)
        #print(decoded_postings_list.tolist())
        result = []
        temp = 0
        for i in range(0, len(decoded_postings_list)):
            mark = decoded_postings_list[i] >> 7
            temp = (temp << 7) + decoded_postings_list[i] % (1 << 7)
            if mark == 1:
                result.append(temp)
                temp = 0 
        for i in range(1, len(result)):
            result[i] = result[i - 1] + result[i]             
        return result
        ### End your code

class IdMap:
    """Helper class to store a mapping from strings to ids."""
    def __init__(self):
        self.str_to_id = {}
        self.id_to_str = []
        
    def __len__(self):
        """Return number of terms stored in the IdMap"""
        return len(self.id_to_str)
        
    def _get_str(self, i):
        """Returns the string corresponding to a given id (`i`)."""
        ### Begin your code
        return self.id_to_str[i]
        ### End your code
        
    def _get_id(self, s):
        """Returns the id corresponding to a string (`s`). 
        If `s` is not in the IdMap yet, then assigns a new id and returns the new id.
        """
        ### Begin your code
        ans = self.str_to_id.get(s)
        #print(ans)
        if ans == None:
            p = self.__len__()
            self.id_to_str.append(s)
            self.str_to_id.setdefault(s, p)
            return p
        else:
            return ans
        ### End your code
            
    def __getitem__(self, key):
        """If `key` is a integer, use _get_str; 
           If `key` is a string, use _get_id;"""
        if type(key) is int:
            return self._get_str(key)
        elif type(key) is str:
            return self._get_id(key)
        else:
            raise TypeError

class UncompressedPostings:
    
    @staticmethod
    def encode(postings_list):
        """Encodes postings_list into a stream of bytes
        
        Parameters
        ----------
        postings_list: List[int]
            List of docIDs (postings)
            
        Returns
        -------
        bytes
            bytearray representing integers in the postings_list
        """
        return array.array('L', postings_list).tobytes()
        
    @staticmethod
    def decode(encoded_postings_list):
        """Decodes postings_list from a stream of bytes
        
        Parameters
        ----------
        encoded_postings_list: bytes
            bytearray representing encoded postings list as output by encode 
            function
            
        Returns
        -------
        List[int]
            Decoded list of docIDs from encoded_postings_list
        """
        
        decoded_postings_list = array.array('L')
        decoded_postings_list.frombytes(encoded_postings_list)
        #print(decoded_postings_list.tolist())
        return decoded_postings_list.tolist()