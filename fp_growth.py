import logging
import multiprocessing

class Node():
    def __init__(self, item, count=0):
        self.item = item
        self.count = count
        self.parent = None
        self.children = {}

    def __str__(self):
        if self.item is not None:
            s = 'item: {} count: {}  '.format(self.item, self.count)
        else:
            s = 'root \n'
        s += 'children: '
        for child in self.children:
            s += str(child) + ' '

        return s

class FPTree():
    def __init__(self):
        # dict[item] = [Node1, Node2...]
        self.header_table = {}
        self.item_counter = {}
        self.root = Node(None)

    def add_tran(self, tran, weight=1):
        ptr = self.root
        for item in tran:
            if item in ptr.children:
                ptr.children[item].count += weight
                self.item_counter[item] += weight
                ptr = ptr.children[item]
            else:
                new_node = Node(item, weight)
                new_node.parent = ptr
                ptr.children[item] = new_node
                if item in self.header_table:
                    self.header_table[item].append(new_node)
                    self.item_counter[item] += weight
                else:
                    self.header_table[item] = [new_node]
                    self.item_counter[item] = weight
                ptr = new_node

        return

    def mine(self, min_cnt=1):
        """
        return:
            [list of frequent patterns, list of fp count]
        """
        fp, fp_count = [], []
        for item in self.header_table:
            if self.item_counter[item] >= min_cnt:
                fp.append([item])
                fp_count.append(self.item_counter[item])

                cond_trans, weights = self.get_conditional_tran(item, min_cnt)
                cond_tree = FPTree()
                for tran, weight in zip(cond_trans, weights):
                    assert item not in tran, (item, tran, weight)
                    cond_tree.add_tran(tran, weight)
                cond_fp, cond_fp_count = cond_tree.mine(min_cnt)
                if cond_fp:
                    cond_fp = [i + [item] for i in cond_fp]
                    fp += cond_fp
                    fp_count += cond_fp_count

        assert len(fp) == len(fp_count)
        if fp:
            fp = [sorted(i) for i in fp]
            tmp = list(zip(fp, fp_count))
            tmp = sorted(tmp, key=lambda x: (len(x[0]), x[0]))
            fp, fp_count = list(zip(*tmp))

        return fp, fp_count

    def get_conditional_tran(self, item, min_cnt=1):
        """
        excluding item
        return:
        [list of items, list of weight]
        """
        trans, weights = [], []
        for node in self.header_table[item]:
            # if node.count >= min_cnt:
            tmp_tran = []
            ptr = node.parent
            # while ptr.item: // wrong when item == 0
            while ptr.item != None:
                tmp_tran.append(ptr.item)
                ptr = ptr.parent
            if tmp_tran:
                trans.append(tmp_tran)
                weights.append(node.count)

        return trans, weights

    def print_tree(self):
        l = [self.root]
        while l:
            next_l = []
            for node in l:
                print(node)
                next_l += node.children.values()
            l = next_l
            print('----------------------------------')



class MineByItem(multiprocessing.Process):
    def __init__(self, tree, min_cnt, fp_list, queue):
        multiprocessing.Process.__init__(self)
        self.tree = tree
        self.min_cnt = min_cnt
        self.queue = queue
        self.fp_list = fp_list

    def run(self):
        while True:
            if self.queue.empty():
                break
            else:
                item = self.queue.get()
                self.fp_list.append(([item], self.tree.item_counter[item]))
                cond_trans, weights = self.tree.get_conditional_tran(item, self.min_cnt)
                cond_tree = FPTree()
                for tran, weight in zip(cond_trans, weights):
                    assert item not in tran, (item, tran, weight)
                    cond_tree.add_tran(tran, weight)
                cond_fp, cond_fp_count = cond_tree.mine(self.min_cnt)
                if cond_fp:
                    cond_fp = [i + [item] for i in cond_fp]
                    cond_fp = [sorted(fp) for fp in cond_fp]
                    self.fp_list += list(zip(cond_fp, cond_fp_count))

def parallel_mine(tree, min_cnt=1, n_jobs=4):
    mgr = multiprocessing.Manager()
    fp_list = mgr.list()
    queue = multiprocessing.Queue()

    for item in tree.header_table:
        if tree.item_counter[item] >= min_cnt:
            queue.put(item)

    process_list = [MineByItem(tree, min_cnt, fp_list, queue) for _ in range(n_jobs)]
    for process in process_list: process.start()
    for process in process_list: process.join()
    fp_list = list(fp_list)
    if fp_list:
        fp_list = sorted(fp_list, key=lambda x: (len(x[0]), x[0]))

    return fp_list


"""
1. sort items by frequency
2. build FP-tree
3. FP mining
"""
def fp_growth(trans, min_support=0.1, use_log=False, n_jobs=1):
    if use_log:
        logging.basicConfig(filename='fp_tree.log', format='%(asctime)s %(message)s',
            level=logging.DEBUG, datefmt='%Y/%m/%d %I:%M:%S %p')

    if use_log:
        logging.info('Begin to count items')
    # count and sort
    counter = {}
    min_cnt = int(min_support * len(trans))
    if min_cnt < 1: return []

    for tran in trans:
        for item in tran:
            counter[item] = counter.get(item, 0) + 1

    if use_log:
        logging.info('Counting finished')

    frequent_item = [item for item in counter if counter[item] >= min_cnt]

    # build FP-tree
    fp_tree = FPTree()
    if use_log:
        logging.info('Begin to add transactions')

    # add trans
    for tran in trans:
        tran = [item for item in tran if item in frequent_item]
        tran = list(set(tran))
        tran = sorted(tran, key=lambda x: (counter[x], x), reverse=True) # the order is very important
        if tran: fp_tree.add_tran(tran)

    if use_log:
        logging.info('Adding transactions finished')
        logging.info('Begin to mine fp')

    # mine pattern
    if n_jobs == 1:
        res = fp_tree.mine(min_cnt)
        res = list(zip(*res))
    elif n_jobs > 1:
        res = parallel_mine(fp_tree, min_cnt, n_jobs)

    if use_log:
        logging.info('Mining fp finished')

    return res
