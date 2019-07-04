import unittest

import numpy as np
import pandas as pd
import mlxtend
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori

from fp_growth import *

class TestFPTree(unittest.TestCase):
    def setUp(self):
        pass

    def test_add_tran(self):
        tree = FPTree()
        tree.add_tran([1, 2, 3, 4])
        tree.add_tran([1, 2, 3])
        tree.add_tran([1, 2])
        tree.add_tran([1])

        self.assertEqual(len(tree.header_table), 4)
        self.assertEqual(len(tree.item_counter), 4)

        for i in range(1, 5):
            self.assertEqual(tree.item_counter[i] + i, 5)
        for i in range(1, 5):
            self.assertEqual(len(tree.header_table[i]), 1)

        tree.add_tran([1, 3, 4], 2)
        self.assertEqual(len(tree.header_table[3]), 2)
        self.assertEqual(len(tree.header_table[4]), 2)
        self.assertEqual(tree.item_counter[1], 6)
        self.assertEqual(tree.item_counter[2], 3)

    def test_get_conditional_tran(self):# test get_conditional_tran
        tree = FPTree()
        tree.add_tran([1, 2, 3, 4])
        tree.add_tran([1, 2, 3])
        tree.add_tran([1, 2])
        tree.add_tran([1])
        tree.add_tran([1, 3, 4], 2)

        trans, weights = tree.get_conditional_tran(4, 1)
        self.assertEqual(len(trans), 2)
        self.assertEqual(weights[0], 1)
        self.assertEqual(weights[1], 2)

    def compare_with_apriori(self, dataset, test_parallel=False):
        support = 0.4
        # apriori
        te = TransactionEncoder()
        te_ary = te.fit(dataset).transform(dataset)
        df = pd.DataFrame(te_ary, columns=te.columns_)
        df = apriori(df, min_support=support, use_colnames=True)
        frequency = df.iloc[:, 0].to_numpy().tolist()
        pattern = df.iloc[:, 1].to_numpy().tolist()
        pattern = [sorted(list(i)) for i in pattern]
        apriori_result = sorted(zip(pattern, frequency), key=lambda x: (len(x[0]), x[0]))

        # fp-growth
        if test_parallel:
            fp_result = fp_growth(dataset, support, n_jobs=4)
        else:
            fp_result = fp_growth(dataset, support)

        self.assertEqual(len(apriori_result), len(fp_result))
        for idx in range(len(apriori_result)):
            self.assertEqual(apriori_result[idx][0], fp_result[idx][0])
            self.assertTrue(abs(apriori_result[idx][1] * len(dataset) - fp_result[idx][1]) <= 1) #  allow the inaccuracy in float point calculation

    def test_testify_apriori_small_dataset(self):
        dataset = [['1', '2', '3', '4', '5', '6'],
                   ['7', '2', '3', '4', '5', '6'],
                   ['1', '11', '4', '5'],
                   ['1', '10', '8', '4', '6'],
                   ['8', '2', '2', '4', '9', '5']]

        self.compare_with_apriori(dataset)
        self.compare_with_apriori(dataset, True)


    def test_testify_apriori_fake_dataset(self):
        # make fake dataset
        total_trans = 10000
        max_trans_len = 20
        dataset = []
        for _ in range(total_trans):
            tmp = [np.random.randint(max_trans_len) for __ in range(max_trans_len)]
            tmp = list(set(tmp))
            dataset.append(tmp)

#         output_lines = []
#         for tran in dataset:
#             tran = [str(i) for i in tran]
#             tran = '[' + ', '.join(tran) + ']'
#             output_lines.append(tran)

#         with open('dataset.dat', 'w') as file:
#             output_lines = '[' + ',\n'.join(output_lines) + ']'
#             file.write(output_lines)

        self.compare_with_apriori(dataset)
        self.compare_with_apriori(dataset, True)

if __name__ == '__main__':
    unittest.main()
