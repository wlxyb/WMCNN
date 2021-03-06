import tensorflow as tf
import numpy as np
import pywt


class Net:
    def __init__(self):
        self.__hps = None
        self.training = None
        self.__regularizer = None
        self.__initializer = tf.contrib.layers.xavier_initializer()
        return

    def model_fn(self, mode, features, labels, params):
        self.__hps = params
        #l2正则
        self.__regularizer = tf.contrib.layers.l2_regularizer(
            params['reg_rate'])
        self.training = mode == tf.estimator.ModeKeys.TRAIN
        logits = self.__fn(features, labels.get_shape()[1])
        predictions = {
            'classes': tf.argmax(logits, 1),
            'probabilities': tf.nn.softmax(logits, name='softmax')
        }

        if mode == tf.estimator.ModeKeys.PREDICT:
            return tf.estimator.EstimatorSpec(mode, predictions)

        loss = tf.losses.softmax_cross_entropy(labels, logits)
        loss += tf.losses.get_regularization_loss()

        if mode == tf.estimator.ModeKeys.TRAIN:
            #  对于大量数据请修改优化器加速收敛
            optimizer = tf.train.AdamOptimizer()
            update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
            with tf.control_dependencies(update_ops):
                train_op = optimizer.minimize(loss, tf.train.get_global_step())
            return tf.estimator.EstimatorSpec(
                mode, loss=loss, train_op=train_op)

        return tf.estimator.EstimatorSpec(
            mode,
            loss=loss,
            eval_metric_ops={
                'accuracy':
                tf.metrics.accuracy(
                    tf.argmax(labels, 1), predictions['classes'])
            })

        #  残差组

    def __residual_stack(self, x, n, out_channels, stride, bottleneck):
        for i in range(n):
            if i != 0:
                stride = 1
            x = self.__residual_block(x, out_channels, stride, bottleneck)
        return x

#  残差单元

    def __residual_block(self, x, out_channels, stride, bottleneck):
        in_channels = x.get_shape()[-1]
        origin_x = x
        if bottleneck:
            x = tf.layers.conv1d(
                x,
                out_channels,
                1,
                padding='same',
                strides=stride,
                kernel_regularizer=self.__regularizer,
                kernel_initializer=self.__initializer)
            x = tf.layers.batch_normalization(x, training=self.training)
            x = tf.nn.leaky_relu(x, self.__hps['leakiness'])

            x = tf.layers.conv1d(
                x,
                out_channels,
                3,
                padding='same',
                kernel_regularizer=self.__regularizer,
                kernel_initializer=self.__initializer)
            x = tf.layers.batch_normalization(x, training=self.training)
            x = tf.nn.leaky_relu(x, self.__hps['leakiness'])

            x = tf.layers.conv1d(
                x,
                out_channels * 4,
                1,
                padding='same',
                kernel_regularizer=self.__regularizer,
                kernel_initializer=self.__initializer)
            x = tf.layers.batch_normalization(x, training=self.training)
        else:
            x = tf.layers.conv1d(
                x,
                out_channels,
                3,
                padding='same',
                strides=stride,
                kernel_regularizer=self.__regularizer,
                kernel_initializer=self.__initializer)
            x = tf.layers.batch_normalization(x, training=self.training)
            x = tf.nn.leaky_relu(x, self.__hps['leakiness'])

            x = tf.layers.conv1d(
                x,
                out_channels,
                3,
                padding='same',
                kernel_regularizer=self.__regularizer,
                kernel_initializer=self.__initializer)
            x = tf.layers.batch_normalization(x, training=self.training)

        out_channels = x.get_shape()[-1]
        if in_channels != out_channels or stride != 1:
            origin_x = tf.layers.conv1d(
                origin_x,
                out_channels,
                1,
                padding='same',
                strides=stride,
                kernel_regularizer=self.__regularizer,
                kernel_initializer=self.__initializer)
            origin_x = tf.layers.batch_normalization(
                origin_x, training=self.training)

        return tf.nn.leaky_relu(x + origin_x, self.__hps['leakiness'])


#  离散小波变换

    @staticmethod
    def __dwt(x, wavelet):
        filters = wavelet.dec_lo[::-1]
        filters = np.array(filters, 'float32').reshape([-1, 1, 1])
        channels = x.get_shape()[-1]
        splits = tf.split(x, channels, -1)
        for i in range(channels):
            splits[i] = tf.nn.conv1d(splits[i], filters, 2, 'VALID')
        return tf.concat(splits, -1)

    def __resnet(self, x):
        #  残差特征提取
        x = self.__residual_stack(x, 2, 64, 1, False)

        x = self.__residual_stack(x, 2, 128, 2, False)

        x = self.__residual_stack(x, 2, 256, 2, False)

        x = self.__residual_stack(x, 2, 512, 2, False)
        #  全局平均，是否换成全连接？
        return tf.reduce_mean(x, 1)

    def __fn(self, x, classes_num):
        wavelet = pywt.Wavelet(self.__hps['wavelet'])

        x_list = [x]
        for _ in range(self.__hps['max_level']):
            x = Net.__dwt(x, wavelet)
            x_list.append(x)
        y_list = []
        for o in x_list:
            o = tf.layers.conv1d(
                o,
                64,
                wavelet.dec_len - 1,
                padding='same',
                strides=2,
                kernel_regularizer=self.__regularizer,
                kernel_initializer=self.__initializer)
            o = tf.layers.batch_normalization(o, training=self.training)
            o = tf.nn.leaky_relu(o, self.__hps['leakiness'])
            o = tf.layers.max_pooling1d(o, 3, 2, padding='same')
            y_list.append(o)
        y = tf.concat(y_list, 1)
        y = self.__resnet(y)
        #  y = tf.layers.dropout(y, training=self.training)
        return tf.layers.dense(y, classes_num)
