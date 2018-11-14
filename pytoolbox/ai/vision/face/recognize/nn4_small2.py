# --------------------------------------------------------------------------------------------------
# Code taken from https://github.com/iwantooxxoox/Keras-OpenFace (with minor modifications)
# --------------------------------------------------------------------------------------------------

import tensorflow as tf
from keras import backend as K
from keras.layers import Conv2D, ZeroPadding2D, Activation, Input, concatenate
from keras.layers.core import Lambda, Flatten, Dense
from keras.layers.normalization import BatchNormalization
from keras.layers.pooling import MaxPooling2D, AveragePooling2D
from keras.models import Model

from pytoolbox.ai.vision import utils

DEFAULT_WEIGHTS = (
    'https://s3-eu-west-1.amazonaws.com/pytoolbox/ai/vision/face/recognize/'
    'nn4.small2.v1.h5')

E = 0.00001  # Epsilon


def conv2d_bn(
    x,
    layer=None,
    cv1_out=None,
    cv1_filter=(1, 1),
    cv1_strides=(1, 1),
    cv2_out=None,
    cv2_filter=(3, 3),
    cv2_strides=(1, 1),
    padding=None,
):
    num = '' if cv2_out is None else '1'
    tensor = Conv2D(cv1_out, cv1_filter, strides=cv1_strides, name=layer + '_conv' + num)(x)
    tensor = BatchNormalization(axis=3, epsilon=E, name=layer + '_bn' + num)(tensor)
    tensor = Activation('relu')(tensor)
    if padding is None:
        return tensor
    tensor = ZeroPadding2D(padding=padding)(tensor)
    if cv2_out is None:
        return tensor
    tensor = Conv2D(cv2_out, cv2_filter, strides=cv2_strides, name=layer + '_conv2')(tensor)
    tensor = BatchNormalization(axis=3, epsilon=E, name=layer + '_bn2')(tensor)
    tensor = Activation('relu')(tensor)
    return tensor


def LRN2D(x):
    return tf.nn.lrn(x, alpha=1e-4, beta=0.75)


def create_model():

    inputs = Input(shape=(96, 96, 3))

    x = ZeroPadding2D(padding=(3, 3), input_shape=(96, 96, 3))(inputs)
    x = Conv2D(64, (7, 7), strides=(2, 2), name='conv1')(x)
    x = BatchNormalization(axis=3, epsilon=E, name='bn1')(x)
    x = Activation('relu')(x)
    x = ZeroPadding2D(padding=(1, 1))(x)
    x = MaxPooling2D(pool_size=3, strides=2)(x)
    x = Lambda(LRN2D, name='lrn_1')(x)
    x = Conv2D(64, (1, 1), name='conv2')(x)
    x = BatchNormalization(axis=3, epsilon=E, name='bn2')(x)
    x = Activation('relu')(x)
    x = ZeroPadding2D(padding=(1, 1))(x)
    x = Conv2D(192, (3, 3), name='conv3')(x)
    x = BatchNormalization(axis=3, epsilon=E, name='bn3')(x)
    x = Activation('relu')(x)
    x = Lambda(LRN2D, name='lrn_2')(x)
    x = ZeroPadding2D(padding=(1, 1))(x)
    x = MaxPooling2D(pool_size=3, strides=2)(x)

    # Inception 3a

    Norm = BatchNormalization

    inception_3a_3x3 = Conv2D(96, (1, 1), name='inception_3a_3x3_conv1')(x)
    inception_3a_3x3 = Norm(axis=3, epsilon=E, name='inception_3a_3x3_bn1')(inception_3a_3x3)
    inception_3a_3x3 = Activation('relu')(inception_3a_3x3)
    inception_3a_3x3 = ZeroPadding2D(padding=(1, 1))(inception_3a_3x3)
    inception_3a_3x3 = Conv2D(128, (3, 3), name='inception_3a_3x3_conv2')(inception_3a_3x3)
    inception_3a_3x3 = Norm(axis=3, epsilon=E, name='inception_3a_3x3_bn2')(inception_3a_3x3)
    inception_3a_3x3 = Activation('relu')(inception_3a_3x3)

    inception_3a_5x5 = Conv2D(16, (1, 1), name='inception_3a_5x5_conv1')(x)
    inception_3a_5x5 = Norm(axis=3, epsilon=E, name='inception_3a_5x5_bn1')(inception_3a_5x5)
    inception_3a_5x5 = Activation('relu')(inception_3a_5x5)
    inception_3a_5x5 = ZeroPadding2D(padding=(2, 2))(inception_3a_5x5)
    inception_3a_5x5 = Conv2D(32, (5, 5), name='inception_3a_5x5_conv2')(inception_3a_5x5)
    inception_3a_5x5 = Norm(axis=3, epsilon=E, name='inception_3a_5x5_bn2')(inception_3a_5x5)
    inception_3a_5x5 = Activation('relu')(inception_3a_5x5)

    inception_3a_pool = MaxPooling2D(pool_size=3, strides=2)(x)
    inception_3a_pool = Conv2D(32, (1, 1), name='inception_3a_pool_conv')(inception_3a_pool)
    inception_3a_pool = Norm(axis=3, epsilon=E, name='inception_3a_pool_bn')(inception_3a_pool)
    inception_3a_pool = Activation('relu')(inception_3a_pool)
    inception_3a_pool = ZeroPadding2D(padding=((3, 4), (3, 4)))(inception_3a_pool)

    inception_3a_1x1 = Conv2D(64, (1, 1), name='inception_3a_1x1_conv')(x)
    inception_3a_1x1 = Norm(axis=3, epsilon=E, name='inception_3a_1x1_bn')(inception_3a_1x1)
    inception_3a_1x1 = Activation('relu')(inception_3a_1x1)

    inception_3a = concatenate([
        inception_3a_3x3,
        inception_3a_5x5,
        inception_3a_pool,
        inception_3a_1x1
    ], axis=3)

    # Inception 3b

    inception_3b_3x3 = Conv2D(96, (1, 1), name='inception_3b_3x3_conv1')(inception_3a)
    inception_3b_3x3 = Norm(axis=3, epsilon=E, name='inception_3b_3x3_bn1')(inception_3b_3x3)
    inception_3b_3x3 = Activation('relu')(inception_3b_3x3)
    inception_3b_3x3 = ZeroPadding2D(padding=(1, 1))(inception_3b_3x3)
    inception_3b_3x3 = Conv2D(128, (3, 3), name='inception_3b_3x3_conv2')(inception_3b_3x3)
    inception_3b_3x3 = Norm(axis=3, epsilon=E, name='inception_3b_3x3_bn2')(inception_3b_3x3)
    inception_3b_3x3 = Activation('relu')(inception_3b_3x3)

    inception_3b_5x5 = Conv2D(32, (1, 1), name='inception_3b_5x5_conv1')(inception_3a)
    inception_3b_5x5 = Norm(axis=3, epsilon=E, name='inception_3b_5x5_bn1')(inception_3b_5x5)
    inception_3b_5x5 = Activation('relu')(inception_3b_5x5)
    inception_3b_5x5 = ZeroPadding2D(padding=(2, 2))(inception_3b_5x5)
    inception_3b_5x5 = Conv2D(64, (5, 5), name='inception_3b_5x5_conv2')(inception_3b_5x5)
    inception_3b_5x5 = Norm(axis=3, epsilon=E, name='inception_3b_5x5_bn2')(inception_3b_5x5)
    inception_3b_5x5 = Activation('relu')(inception_3b_5x5)

    inception_3b_pool = AveragePooling2D(pool_size=(3, 3), strides=(3, 3))(inception_3a)
    inception_3b_pool = Conv2D(64, (1, 1), name='inception_3b_pool_conv')(inception_3b_pool)
    inception_3b_pool = Norm(axis=3, epsilon=E, name='inception_3b_pool_bn')(inception_3b_pool)
    inception_3b_pool = Activation('relu')(inception_3b_pool)
    inception_3b_pool = ZeroPadding2D(padding=(4, 4))(inception_3b_pool)

    inception_3b_1x1 = Conv2D(64, (1, 1), name='inception_3b_1x1_conv')(inception_3a)
    inception_3b_1x1 = Norm(axis=3, epsilon=E, name='inception_3b_1x1_bn')(inception_3b_1x1)
    inception_3b_1x1 = Activation('relu')(inception_3b_1x1)

    inception_3b = concatenate([
        inception_3b_3x3,
        inception_3b_5x5,
        inception_3b_pool,
        inception_3b_1x1
    ], axis=3)

    # Inception 3c

    inception_3c_3x3 = conv2d_bn(
        inception_3b,
        layer='inception_3c_3x3',
        cv1_out=128,
        cv1_filter=(1, 1),
        cv2_out=256,
        cv2_filter=(3, 3),
        cv2_strides=(2, 2),
        padding=(1, 1))

    inception_3c_5x5 = conv2d_bn(
        inception_3b,
        layer='inception_3c_5x5',
        cv1_out=32,
        cv1_filter=(1, 1),
        cv2_out=64,
        cv2_filter=(5, 5),
        cv2_strides=(2, 2),
        padding=(2, 2))

    inception_3c_pool = MaxPooling2D(pool_size=3, strides=2)(inception_3b)
    inception_3c_pool = ZeroPadding2D(padding=((0, 1), (0, 1)))(inception_3c_pool)

    inception_3c = concatenate([
        inception_3c_3x3,
        inception_3c_5x5,
        inception_3c_pool
    ], axis=3)

    # Inception 4a

    inception_4a_3x3 = conv2d_bn(
        inception_3c,
        layer='inception_4a_3x3',
        cv1_out=96,
        cv1_filter=(1, 1),
        cv2_out=192,
        cv2_filter=(3, 3),
        cv2_strides=(1, 1),
        padding=(1, 1))

    inception_4a_5x5 = conv2d_bn(
        inception_3c,
        layer='inception_4a_5x5',
        cv1_out=32,
        cv1_filter=(1, 1),
        cv2_out=64,
        cv2_filter=(5, 5),
        cv2_strides=(1, 1),
        padding=(2, 2))

    inception_4a_pool = AveragePooling2D(pool_size=(3, 3), strides=(3, 3))(inception_3c)

    inception_4a_pool = conv2d_bn(
        inception_4a_pool,
        layer='inception_4a_pool',
        cv1_out=128,
        cv1_filter=(1, 1),
        padding=(2, 2))

    inception_4a_1x1 = conv2d_bn(
        inception_3c,
        layer='inception_4a_1x1',
        cv1_out=256,
        cv1_filter=(1, 1))

    inception_4a = concatenate([
        inception_4a_3x3,
        inception_4a_5x5,
        inception_4a_pool,
        inception_4a_1x1
    ], axis=3)

    # Inception 4e

    inception_4e_3x3 = conv2d_bn(
        inception_4a,
        layer='inception_4e_3x3',
        cv1_out=160,
        cv1_filter=(1, 1),
        cv2_out=256,
        cv2_filter=(3, 3),
        cv2_strides=(2, 2),
        padding=(1, 1))

    inception_4e_5x5 = conv2d_bn(
        inception_4a,
        layer='inception_4e_5x5',
        cv1_out=64,
        cv1_filter=(1, 1),
        cv2_out=128,
        cv2_filter=(5, 5),
        cv2_strides=(2, 2),
        padding=(2, 2))

    inception_4e_pool = MaxPooling2D(pool_size=3, strides=2)(inception_4a)
    inception_4e_pool = ZeroPadding2D(padding=((0, 1), (0, 1)))(inception_4e_pool)

    inception_4e = concatenate([
        inception_4e_3x3,
        inception_4e_5x5,
        inception_4e_pool
    ], axis=3)

    # Inception 5a

    inception_5a_3x3 = conv2d_bn(
        inception_4e,
        layer='inception_5a_3x3',
        cv1_out=96,
        cv1_filter=(1, 1),
        cv2_out=384,
        cv2_filter=(3, 3),
        cv2_strides=(1, 1),
        padding=(1, 1))

    inception_5a_pool = AveragePooling2D(pool_size=(3, 3), strides=(3, 3))(inception_4e)

    inception_5a_pool = conv2d_bn(
        inception_5a_pool,
        layer='inception_5a_pool',
        cv1_out=96,
        cv1_filter=(1, 1),
        padding=(1, 1))

    inception_5a_1x1 = conv2d_bn(
        inception_4e,
        layer='inception_5a_1x1',
        cv1_out=256,
        cv1_filter=(1, 1))

    inception_5a = concatenate([
        inception_5a_3x3,
        inception_5a_pool,
        inception_5a_1x1
    ], axis=3)

    # Inception 5b

    inception_5b_3x3 = conv2d_bn(
        inception_5a,
        layer='inception_5b_3x3',
        cv1_out=96,
        cv1_filter=(1, 1),
        cv2_out=384,
        cv2_filter=(3, 3),
        cv2_strides=(1, 1),
        padding=(1, 1))

    inception_5b_pool = MaxPooling2D(pool_size=3, strides=2)(inception_5a)

    inception_5b_pool = conv2d_bn(
        inception_5b_pool,
        layer='inception_5b_pool',
        cv1_out=96,
        cv1_filter=(1, 1))

    inception_5b_pool = ZeroPadding2D(padding=(1, 1))(inception_5b_pool)

    inception_5b_1x1 = conv2d_bn(
        inception_5a,
        layer='inception_5b_1x1',
        cv1_out=256,
        cv1_filter=(1, 1))

    inception_5b = concatenate([
        inception_5b_3x3,
        inception_5b_pool,
        inception_5b_1x1
    ], axis=3)

    # Outputs

    reshape_layer = Flatten()(AveragePooling2D(pool_size=(3, 3), strides=(1, 1))(inception_5b))
    dense_layer = Dense(128, name='dense_layer')(reshape_layer)

    outputs = Lambda(lambda x: K.l2_normalize(x, axis=1), name='norm_layer')(dense_layer)

    return Model(inputs=[inputs], outputs=outputs)


def load_model(weights=DEFAULT_WEIGHTS):
    model = create_model()
    if weights:
        model.load_weights(utils.load_to_file(weights))
    return model
