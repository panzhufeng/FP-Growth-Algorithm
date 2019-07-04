import sys
import time

import matplotlib.pyplot as plt

import mlxtend
import numpy as np
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori

from fp_growth import *

running_time = []
for total_trans in [i * 5000 for i in range(1, 14)]:
    print(total_trans)
    min_support = 0.01
#     if min_support * len(total_trans) < 100: min_support = 100 / len(total_trans)
        
    one_pass_time = []
    
    
    with open('../data/test.txt', 'r') as file:
        lines = file.readlines()
    # prepare dataset
    sents = []
    lines = [line.strip('\n').strip('0\t').strip('1\t') for line in lines]
    for line in lines: sents += line.split('\t')
    sents = [sent.split(' ') for sent in sents]   
    print(len(lines), len(sents))
    
#     total_trans= int(total_trans)
#     max_trans_len = 50
#     items_num = 1000000
#     dataset = []
#     for _ in range(total_trans):
#         tmp = [np.random.randint(items_num) for __ in range(np.random.randint(max_trans_len))]
#         tmp = list(set(tmp))
#         dataset.append(tmp)
        

    dataset = sents[:total_trans]

    # fp-tree sequential
    start = time.time()
    pattern = fp_growth(dataset, min_support, True, n_jobs=1)
    elapsed = time.time() - start
    one_pass_time.append(elapsed)


    #fp-tree parallel
    start = time.time()
    pattern = fp_growth(dataset, min_support, True, n_jobs=4)
    elapsed = time.time() - start
    one_pass_time.append(elapsed)
    
    
    # apriori 
    te = TransactionEncoder()
    te_ary = te.fit(dataset).transform(dataset)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    start = time.time()
    fp = apriori(df, min_support=min_support)
    elapsed = time.time() - start
    one_pass_time.append(elapsed)
    
    running_time.append(one_pass_time)


names = ['fp-growth', 'fp-growth-parallel', 'apriori']
dataset_size = [i * 5000 for i in range(1, 14)]
running_time = np.asarray(running_time)
for idx in range(len(names)): plt.plot(dataset_size, running_time[:, idx], label=names[idx])
plt.legend()
plt.xlabel('dataset size')
plt.ylabel('time (s)')
plt.savefig('run_time.png', dpi=300)
# plt.show()