import copy

class Node():
    def __init__(self, item=None):
        self.item = item
        self.value = 0
        self.c_value = 0 # conditional_value
        self.parent = None
        self.children = {} # children mapper: item -> Node

    # return the child Node of item
    def _get_child(self, item):
        global head_table
        assert item in head_table, "Not found error, the item should be in head_table"

        if item in self.children:
            return self.children[item]

        # add a new node
        new_child = Node(item)
        new_child.parent = self
        self.children[item] = new_child
        head_table[item].append(new_child)

        return new_child

    # tran: sorted list of item, excludes self.item
    # return the node at end of the transaction
    def add_transaction(self, tran):
        self.value += 1
        # if current node is a leaf node
        if len(tran) == 0:
            return self
        child_node = self._get_child(tran[0])

        return child_node.add_transaction(tran[1:])

    def reset_conditional_value(self):
        self.c_value = 0
        ptr = self.parent
        while ptr:
            ptr.c_value = 0
            ptr = ptr.parent

        return

    def update_conditional_value(self):
        self.c_value = self.value
        ptr = self.parent
        while ptr:
            ptr.c_value += self.c_value
            ptr = ptr.parent

        return

    def get_conditional_pattern(self, confidence):
        pattern = []
        ptr = self.parent
        while ptr.item: # root.item == None
            if ptr.c_value >= confidence:
                pattern.append(ptr.item)
            ptr = ptr.parent
        # reverse pattern by frequency
        pattern = pattern[::-1]

        return pattern

def test_node():
    root = Node()
    root.add_transaction([1,2,3])
    root.add_transaction([1,2,3,4,5])
    root.add_transaction([1,2])

head_table = None

# transactions: iterable object of lists, each transaction represent one transaction
class FG_Growth():
    def __init__(self, transactions, confidence=10):
        global head_table

        self.root = Node()
        self.confidence = confidence
        self.transactions = [list(set(tran)) for tran in transactions]
        self.counter = {}

        for tran in self.transactions:
            for item in tran:
                self.counter[item] = self.counter.get(item, 0) + 1

        self.freq_item = [[item, self.counter[item]] for item in self.counter if self.counter[item] >= self.confidence]
        self.sorted_freq = sorted(self.freq_item, key=lambda x:x[1], reverse=True)

        # rank_map: item -> rank
        self.rank_map = {item[0]:rank for rank, item in self.sorted_freq}
        # make head_table
        head_table = {item[0]:[] for item in self.freq_item}

        for tran in self.transactions:
            self.root.add_transaction(tran)

    # l: [[item_1, imte_2], ...]
    def _make_pattern(self, l):
        res = copy.deepcopy(l)
        buffer = copy.deepcopy(l)
        lenght = 1
        while buffer:
            lenght += 1
            buffer_set = set()
            for i in range(len(buffer)):
                for j in range(i + 1, len(buffer)):
                    tmp = tuple(set(buffer[i] + buffer[j]))
                    if len(tmp) == lenght and tmp not in buffer_set:
                        buffer_set.add(tmp)
                        res.append(tmp)
            buffer = list(buffer_set)
        res = [list(i) for i in res]
        
        return res

    def get_fp(self):
        global head_table

        patterns = []
        for item in head_table:
            for ptr in head_table[item]:
                ptr.reset_conditional_value()
            for ptr in head_table[item]:
                ptr.update_conditional_value()
            c_pattern = []
            for ptr in head_table[item]:
                tmp = ptr.get_conditional_pattern(self.confidence)
                tmp = [[i] for i in tmp]
                tmp = self._make_pattern(tmp)
                if len(tmp) > 0:
                    tmp = [i + [ptr.item] for i in tmp]
                    c_pattern += tmp
