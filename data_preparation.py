#!/usr/bin/python
import numpy as np


def _load_data(path):
    data = np.loadtxt(path, delimiter=',')
    rng = np.random.RandomState(472943)
    idn = np.arange(data.shape[0])
    rng.shuffle(idn)
    data = data[idn]
    return data


def _slice_data(data, label, length):
    ori_num = data.shape[0]
    ori_len = data.shape[1]
    threshold = min(ori_len, length) / 2
    length = 1
    while length <= threshold:
        length <<= 1
    mul = ori_len - length + 1
    n = ori_num * mul
    new_data = np.zeros((n, length))
    new_label = np.zeros((n,), dtype=np.int_)
    for i in range(ori_num):
        for j in range(mul):
            new_data[i * mul + j, :] = data[i, j:j + length]
            new_label[i * mul + j] = label[i]
    return new_data, new_label


def _normalize(data):
    mean = data.mean(axis=1).reshape((data.shape[0], 1))
    std = data.std(axis=1).reshape((data.shape[0], 1))
    return (data - mean) / std


def get_data(train_path, test_path, valid_id=0, isNorm=True, length=1024):
    train = _load_data(train_path)
    test = _load_data(test_path)

    train_num = train.shape[0]
    if valid_id > 0:
        idn = np.arange(train_num)
        valid = train[idn[train_num *
                          (valid_id - 1) // 5:train_num * valid_id // 5]]
        idn = np.delete(idn, range(train_num * (valid_id - 1) //
                                   5, train_num * valid_id // 5))
        train = train[idn]
    else:
        valid = train.copy()

    train_label = np.int_(train[:, 0])
    train_data = train[:, 1:]

    valid_label = np.int_(valid[:, 0])
    valid_data = valid[:, 1:]

    test_label = np.int_(test[:, 0])
    test_data = test[:, 1:]

    train_data, train_label = _slice_data(train_data, train_label, length)
    valid_data, valid_label = _slice_data(valid_data, valid_label, length)
    test_data, test_label = _slice_data(test_data, test_label, length)

    if isNorm:
        train_data = _normalize(train_data)
        valid_data = _normalize(valid_data)
        test_data = _normalize(test_data)

    return ((train_label, train_data), (valid_label, valid_data), (test_label, test_data))

def _dwt(data, layer):
    lens = [data.shape[1]]


if __name__ == '__main__':
#      data = get_data('./test_data', './test_data', valid_id=2, isNorm=False)
#      train_label, train_data = data[0]
#      valid_label, valid_data = data[1]
#      test_label, test_data = data[2]
#      print(train_label)
#      print(train_data)
#      print('--------------------------------')
#      print(valid_label)
#      print(valid_data)
#      print('--------------------------------')
#      print(test_label)
#      print(test_data)
#      print('--------------------------------')
#      print(_load_data('./test_data'))
