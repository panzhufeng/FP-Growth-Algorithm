class Node():
    def __init__(self, item=None, value=1):
        self.item = item
        self.value = value
        self.c_value = 0 # conditional_value
        self.tree_idx = 0
        self.parent = None
        self.children = {} # children mapper: item -> Node

    # for testing usage
    def print(self):
        print('item: {}  value: {}  c_value: {}  tree_idx: {}  parent: {}\nchildren: {}'.format(self.item,
        self.value, self.c_value, self.tree_idx, self.parent, self.children))


    def reset_conditional_value(self):
        self.c_value = 0
        ptr = self.parent
        while ptr.item:
            ptr.c_value = 0
            ptr = ptr.parent

        return

    def update_conditional_value(self):
        self.c_value = self.value
        ptr = self.parent
        while ptr.item:
            ptr.c_value += self.c_value
            ptr = ptr.parent

        return

    def mark_subtree(self, support, tree_idx):
        ptr = self.parent
        while ptr.item:
            if ptr.c_value >= support:
                ptr.tree_idx = tree_idx
            ptr = ptr.parent

        return

    # return list of items with support
    def traversal(self, tree_idx):
        item_list, conf_list = [], []
        # bfs
        queue, ptr = [self], 0

        while ptr < len(queue):
            is_leaf = 1
            for node in queue[ptr].children.values():
                if node.tree_idx == tree_idx:
                    queue.append(node)
                    is_leaf = 0
            if is_leaf:
                items, confs = queue[ptr].get_conditional_pattern()
                if len(items):
                    item_list.append(items)
                    conf_list.append(confs)
            ptr += 1

        return item_list, conf_list

    def get_conditional_pattern(self):
        pattern = []
        conf = []
        ptr = self
        while ptr.item: # root.item == None
            pattern.append(ptr.item)
            conf.append(ptr.c_value)
            ptr = ptr.parent
        # reverse pattern
        pattern = pattern[::-1]
        conf = conf[::-1]

        return pattern, conf

# transactions: iterable object of lists, each transaction represent one transaction
class FP_Tree():
    tree_idx = 0

    # from transactions, build the FP-Tree and the corresponding self.head_table
    def __init__(self, transactions, support=1, num_list=None, is_main_tree=True):
        if num_list is None:
            num_list = [1 for _ in range(len(transactions))]
        self.root = Node()
        self.support = support
        self.head_table = {}

        transactions = [list(set(tran)) for tran in transactions]
        self.counter = {}
        for idx, tran in enumerate(transactions):
            for item in tran:
                self.counter[item] = self.counter.get(item, 0) + num_list[idx]
        self.freq_item = [[item, self.counter[item]] for item in self.counter if self.counter[item] >= self.support]

        # sort transactions if it's the main FP-Tree
        if is_main_tree:

            self.sorted_freq = sorted(self.freq_item, key=lambda x:x[1], reverse=True)

            # filter non-frequent items from head_table
            # rank_map: item -> rank
            self.rank_map = {item[0]:rank for rank, item in enumerate(self.sorted_freq)}
            transactions = [[item for item in tran if item in self.rank_map] for tran in transactions]
            transactions = [sorted(tran, key=lambda x: self.rank_map[x]) for tran in transactions]
        # make head_table
        for tran in transactions:
            for item in tran:
                if item not in self.head_table:
                    self.head_table[item] = []

        for idx, tran in enumerate(transactions):
            self._add_transaction(tran, num_list[idx])

    # tran: sorted list of item, excludes self.item
    # number: int, number of repeated transaction
    def _add_transaction(self, tran, number):
        idx = 0
        ptr = self.root # current node
        while idx < len(tran):
            item = tran[idx]
            if item in ptr.children:
                ptr = ptr.children[item]
                ptr.value += number
                idx += 1
            else:
                # add a new node
                new_node = Node(item, number)
                new_node.parent = ptr
                ptr.children[item] = new_node
                # update head table
                self.head_table[item].append(new_node)
                ptr = new_node
                idx += 1

        return

    def _generate_combination(self, items, conf):
        assert len(items) == len(conf)
        if len(items) == 0:
            return [], []

        def _dfs(l1, l2):
            if len(l1) > 1:
                res_1, res_2 = _dfs(l1[1:], l2[1:])
                for i in range(len(res_1)):
                    res_1.append([l1[0]] + res_1[i])
                    res_2.append([l2[0]] + res_2[i])
                return res_1, res_2
            elif len(l1) == 1:
                return [ [l1[0]] ], [ [l2[0]] ]
            else:
                return [], []

        patterns, confs = _dfs(items, conf)
        confs = [min(i) for i in confs]

        return patterns, confs

    # return: return patterns including the given item with support
    def _make_pattern(self, item):
        # for each item in self.head_table, following steps are taken to get frequent patterns:
        # 1. reset_conditional_value, from bottom to top
        # 2. update_conditional_value, from bottom to top
        # 3. make sub FG-Tree from root by masking (marked with sub-tree index), from bottom to top
        # 4. generate transactions from sub-tree
        # 5. check if the sub-tree only exist one path, go 5-1 if yes, otherwise go 5-2
        # 5-1. generate combination patterns from one item list. Return results
        # 5-2. get transactions from sub-tree with transaction count.
        # 6. build new FP-tree and new_tree_root.get_pattern()
        # 7. append subfix patterns. Return results

        for node in self.head_table[item]:
            node.reset_conditional_value()
        for node in self.head_table[item]:
            node.update_conditional_value()

        # step 3
        FP_Tree.tree_idx += 1
        for node in self.head_table[item]:
            node.mark_subtree(self.support, FP_Tree.tree_idx) # excluding node

        # step 4
        tran_list, conf_list = self.root.traversal(FP_Tree.tree_idx)

        if len(tran_list) == 0:
            return [], []
        if len(tran_list) == 1:
            res, conf = self._generate_combination(tran_list[0], conf_list[0])
            res = [i + [item] for i in res]
        else:
            new_tree = FP_Tree(tran_list, conf_list, self.support, False)
            res, conf = new_tree.get_pattern()
            res = [i + [item] for i in res]

        return res, conf

    # get patterns with given support
    # return: list of lists [[item1, item2, ...], support_count], sorted by tuple (pattern_len, -support_count) with ascending order
    def get_pattern(self):
        patterns = [[i[0]] for i in self.freq_item]
        confs = [i[1] for i in self.freq_item]
        for item in self.head_table:
            res, conf = self._make_pattern(item)
            if len(res):
                patterns += res
                confs += conf

        return patterns, confs
