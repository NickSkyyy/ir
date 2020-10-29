import contextlib
import heapq
import InvertedIndex as ii
import math
import os
import pickle as pkl
import util
from operator import itemgetter
from string import punctuation

# Do not make any changes here, they will be overwritten while grading
class BSBIIndex:
    """ 
    Attributes
    ----------
    term_id_map(IdMap): For mapping terms to termIDs
    doc_id_map(IdMap): For mapping relative paths of documents (eg 
        0/3dradiology.stanford.edu_) to docIDs
    data_dir(str): Path to data
    output_dir(str): Path to output index files
    index_name(str): Name assigned to index
    postings_encoding: Encoding used for storing the postings.
        The default (None) implies UncompressedPostings
    """
    def __init__(self, data_dir, output_dir, index_name = "BSBI", 
                 postings_encoding = None):
        self.term_id_map = util.IdMap()
        self.doc_id_map = util.IdMap()
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.index_name = index_name
        self.postings_encoding = postings_encoding

        # Stores names of intermediate indices
        self.intermediate_indices = []
        
    def save(self):
        """Dumps doc_id_map and term_id_map into output directory"""
        
        with open(os.path.join(self.output_dir, 'terms.dict'), 'wb') as f:
            pkl.dump(self.term_id_map, f)
        with open(os.path.join(self.output_dir, 'docs.dict'), 'wb') as f:
            pkl.dump(self.doc_id_map, f)
    
    def load(self):
        """Loads doc_id_map and term_id_map from output directory"""
        
        with open(os.path.join(self.output_dir, 'terms.dict'), 'rb') as f:
            self.term_id_map = pkl.load(f)
        with open(os.path.join(self.output_dir, 'docs.dict'), 'rb') as f:
            self.doc_id_map = pkl.load(f)
            
    def index(self):
        """Base indexing code
        
        This function loops through the data directories, 
        calls parse_block to parse the documents
        calls invert_write, which inverts each block and writes to a new index
        then saves the id maps and calls merge on the intermediate indices
        """
        for block_dir_relative in sorted(next(os.walk(self.data_dir))[1]):
            td_pairs = self.parse_block(block_dir_relative)
            index_id = 'index_'+block_dir_relative
            self.intermediate_indices.append(index_id)
            with ii.InvertedIndexWriter(index_id, directory=self.output_dir, 
                                     postings_encoding=
                                     self.postings_encoding) as index:
                self.invert_write(td_pairs, index)
                td_pairs = None
        self.save()
        with ii.InvertedIndexWriter(self.index_name, directory=self.output_dir, 
                                 postings_encoding=
                                 self.postings_encoding) as merged_index:
            with contextlib.ExitStack() as stack:
                indices = [stack.enter_context(
                    ii.InvertedIndexIterator(index_id, 
                                          directory=self.output_dir, 
                                          postings_encoding=
                                          self.postings_encoding)) 
                 for index_id in self.intermediate_indices]
                self.merge(indices, merged_index)

    def invert_write(self, td_pairs, index):
        """Inverts td_pairs into postings_lists and writes them to the given index
        
        Parameters
        ----------
        td_pairs: List[Tuple[Int, Int]]
            List of termID-docID pairs
        index: InvertedIndexWriter
            Inverted index on disk corresponding to the block       
        """
        ### Begin your code
        td_pairs.sort(key=itemgetter(0, 1))
        term = td_pairs[0][0]
        plist = [td_pairs[0][1]]
        for i in range(1, len(td_pairs)):
            if td_pairs[i][0] == term:
                plist.append(td_pairs[i][1])
            else:            
                # print(term, " ", plist)
                index.append(term, plist)
                term = td_pairs[i][0]
                plist = [td_pairs[i][1]]
        # print(term, " ", plist)
        index.append(term, plist)
        ### End your code
        
    def merge(self, indices, merged_index):
        """Merges multiple inverted indices into a single index
        
        Parameters
        ----------
        indices: List[InvertedIndexIterator]
            A list of InvertedIndexIterator objects, each representing an
            iterable inverted index for a block
        merged_index: InvertedIndexWriter
            An instance of InvertedIndexWriter object into which each merged 
            postings list is written out one at a time
        """
        ### Begin your code
        term = -1
        plist = []
        for item in heapq.merge(*indices, key=lambda x: x[0]):
            # print(item)
            if item[0] == term:
                plist.append(item[1])
            else:
                if not plist == []:
                    # print(list(heapq.merge(*plist)))
                    merged_index.append(term, list(heapq.merge(*plist)))
                term = item[0]
                plist = [item[1]]

        ### End your code

    def parse_block(self, block_dir_relative):
        """Parses a tokenized text file into termID-docID pairs
        
        Parameters
        ----------
        block_dir_relative : str
            Relative Path to the directory that contains the files for the block
        
        Returns
        -------
        List[Tuple[Int, Int]]
            Returns all the td_pairs extracted from the block
        
        Should use self.term_id_map and self.doc_id_map to get termIDs and docIDs.
        These persist across calls to parse_block
        """
        ### Begin your code
        result = []
        url = os.path.join(self.data_dir, block_dir_relative)
        docs = []
        for home, dirs, files in os.walk(url):
            for filename in files:
                # print(block_dir_relative + '/' + filename)
                docs.append(block_dir_relative + '/' + filename) 

        for doc in docs:
            f = open(self.data_dir + '/' + doc, encoding='utf-8')
            words = f.read().split()
            words = list(set(words))
            for i in range(0, len(words)):
                tid = self.term_id_map.__getitem__(words[i])
                did = self.doc_id_map.__getitem__(doc)
                result.append([tid, did])
        #print(result)
        #print(self.term_id_map.__getitem__('you'))
        #print(url + " finished")
        return result
        ### End your code
    
    def sorted_intersect(self, list1, list2):
        """Intersects two (ascending) sorted lists and returns the sorted result
    
        Parameters
        ----------
        list1: List[Comparable]
        list2: List[Comparable]
            Sorted lists to be intersected
        
        Returns
        -------
        List[Comparable]
            Sorted intersection        
        """
        ### Begin your code
        result = []
        p1 = 0
        p2 = 0
        s1 = int(math.sqrt(len(list1)))
        s2 = int(math.sqrt(len(list2)))
        while (p1 < len(list1) and p2 < len(list2)):
            if list1[p1] == list2[p2]:
                result.append(list1[p1])
                p1 = p1 + 1
                p2 = p2 + 1
            elif list1[p1] < list2[p2]:
                if (p1 + s1 >= len(list1) or list1[p1 + s1] > list2[p2]):
                    p1 = p1 + 1
                else:
                    p1 = p1 + s1
            else:
                if (p2 + s2 >= len(list2) or list2[p2 + s2] > list2[p2]):
                    p2 = p2 + 1
                else:
                    p2 = p2 + s2
        # print(result)
        return result
        ### End your code
    
    def retrieve(self, query, posting_encodings=util.CompressedPostings):
        """Retrieves the documents corresponding to the conjunctive query
        
        Parameters
        ----------
        query: str
            Space separated list of query tokens


        Result
        ------
        List[str]
            Sorted list of documents which contains each of the query tokens. 
            Should be empty if no documents are found.
        
        Should NOT throw errors for terms not in corpus
        """
        if len(self.term_id_map) == 0 or len(self.doc_id_map) == 0:
            self.load()

        ### Begin your code
        words = query.split()
        iim = ii.InvertedIndexMapper('data', directory=self.output_dir, postings_encoding=posting_encodings)
        tid = self.term_id_map.__getitem__(words[0])
        ans = iim.__getitem__(tid)
        for i in range(1, len(words)):
            tid = self.term_id_map.__getitem__(words[i])
            ans = self.sorted_intersect(ans, iim.__getitem__(tid))
        for i in range(0, len(ans)):
            ans[i] = self.doc_id_map.__getitem__(ans[i])
        return ans
        ### End your code