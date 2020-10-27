import array

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
        # print(ans)
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
        return decoded_postings_list.tolist()