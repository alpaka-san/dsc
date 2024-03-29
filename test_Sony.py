# uniform content loss + adaptive threshold + per_class_input + recursive G
# improvement upon cqf37
from __future__ import division
import os, scipy.io
import tensorflow as tf
import tensorflow.contrib.slim as slim
import numpy as np
import rawpy
import glob
import time
from PIL.Image import fromarray as toimage


input_dir = './dataset/Sony/short/'
gt_dir = './dataset/Sony/long/'
# checkpoint_dir = './checkpoint/Sony/'
checkpoint_dir = './result_Sony/'
result_dir = './result_Sony/'

# get test IDs
test_fns = glob.glob(gt_dir + '/1*.ARW')
# test_fns = glob.glob('test*.CR2')
test_ids = [int(os.path.basename(test_fn)[0:5]) for test_fn in test_fns]

DEBUG = 0
if DEBUG == 1:
    save_freq = 2
    test_ids = test_ids[0:5]


def lrelu(x):
    return tf.maximum(x * 0.2, x)


def upsample_and_concat(x1, x2, output_channels, in_channels):
    pool_size = 2
    deconv_filter = tf.Variable(tf.truncated_normal([pool_size, pool_size, output_channels, in_channels], stddev=0.02))
    deconv = tf.nn.conv2d_transpose(x1, deconv_filter, tf.shape(x2), strides=[1, pool_size, pool_size, 1])

    deconv_output = tf.concat([deconv, x2], 3)
    deconv_output.set_shape([None, None, None, output_channels * 2])

    return deconv_output


def network(input):
    conv1 = slim.conv2d(input, 32, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv1_1')
    conv1 = slim.conv2d(conv1, 32, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv1_2')
    pool1 = tf.space_to_depth(conv1, 2)

    conv2 = slim.conv2d(pool1, 64, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv2_1')
    conv2 = slim.conv2d(conv2, 64, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv2_2')
    pool2 = tf.space_to_depth(conv2, 2)

    conv3 = slim.conv2d(pool2, 128, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv3_1')
    conv3 = slim.conv2d(conv3, 128, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv3_2')
    pool3 = tf.space_to_depth(conv3, 2)

    conv4 = slim.conv2d(pool3, 256, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv4_1')
    conv4 = slim.conv2d(conv4, 256, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv4_2')
    pool4 = tf.space_to_depth(conv4, 2)

    conv5 = slim.conv2d(pool4, 512, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv5_1')
    conv5 = slim.conv2d(conv5, 512, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv5_2')

    # up6 = tf.concat([conv5, conv4], 3)
    up6 = tf.concat([conv5, pool4], 3)
    up6 = tf.depth_to_space(up6, 2)
    conv6 = slim.conv2d(up6, 256, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv6_1')
    conv6 = slim.conv2d(conv6, 256, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv6_2')

    # up7 = tf.concat([conv6, conv3], 3)
    up7 = tf.concat([conv6, pool3], 3)
    up7 = tf.depth_to_space(up7, 2)
    conv7 = slim.conv2d(up7, 128, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv7_1')
    conv7 = slim.conv2d(conv7, 128, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv7_2')

    # up8 = tf.concat([conv7, conv2], 3)
    up8 = tf.concat([conv7, pool2], 3)
    up8 = tf.depth_to_space(up8, 2)
    conv8 = slim.conv2d(up8, 64, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv8_1')
    conv8 = slim.conv2d(conv8, 64, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv8_2')

    # up9 = tf.concat([conv8, conv1], 3)
    up9 = tf.concat([conv8, pool1], 3)
    up9 = tf.depth_to_space(up9, 2)
    conv9 = slim.conv2d(up9, 32, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv9_1')
    conv9 = slim.conv2d(conv9, 32, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv9_2')

    conv10 = slim.conv2d(conv9, 12, [1, 1], rate=1, activation_fn=None, scope='g_conv10')
    out = tf.depth_to_space(conv10, 2)
    return out
# def network(input):
#     conv1 = slim.conv2d(input, 4, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv1')
#     s2d_2 = tf.space_to_depth(conv1, 2)
#     conv3 = slim.conv2d(conv1, 16, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv3')
#     d2s_4 = tf.space_to_depth(conv3, 2)
#     conv4 = slim.conv2d(d2s_4, 64, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv4')
#     d2s_5 = tf.space_to_depth(conv4, 2)
#     conv5 = slim.conv2d(d2s_5, 256, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv5')
#     d2s_6 = tf.space_to_depth(conv5, 2)
#     conv6 = slim.conv2d(d2s_6, 512, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv6')
# 
#     d2s_6_2 = tf.depth_to_space(conv6, 2)
#     conv5_2 = slim.conv2d(d2s_6_2, 256, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv5_2')
#     d2s_5_2 = tf.depth_to_space(conv5_2, 2)
#     conv4_2 = slim.conv2d(d2s_5_2, 64, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv4_2')
#     ups_4 = tf.concat([d2s_4, conv4_2], 3)
#     # d2s_4_2 = tf.depth_to_space(conv4_2, 2)
#     d2s_4_2 = tf.depth_to_space(ups_4, 2)
#     conv3_2 = slim.conv2d(d2s_4_2, 16, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv3_2')
#     # d2s_3_2 = tf.depth_to_space(conv3_2, 2)
#     # conv2_2 = slim.conv2d(d2s_3_2, 4, [3, 3], rate=1, activation_fn=lrelu, scope='g_conv2_2')
#     hidden1 = conv1
#     hidden2_2 = conv3_2
#     ups_5 = tf.concat([input, conv3_2], 3) 
# 
#     conv6_2 = slim.conv2d(ups_5, 12, [1, 1], rate=1, activation_fn=None, scope='g_conv6_2')
#     hidden2 = conv6_2
#     out = tf.depth_to_space(conv6_2, 2)
#     return hidden1,hidden2,out

def pack_raw(raw):
    # pack Bayer image to 4 channels
    im = raw.raw_image_visible.astype(np.float32)
    im = np.maximum(im - 512, 0) / (16383 - 512)  # subtract the black level

    im = np.expand_dims(im, axis=2)
    img_shape = im.shape
    H = img_shape[0]
    W = img_shape[1]

    out = np.concatenate((im[0:H:2, 0:W:2, :],
                          im[0:H:2, 1:W:2, :],
                          im[1:H:2, 1:W:2, :],
                          im[1:H:2, 0:W:2, :]), axis=2)
    return out


sess = tf.Session()
in_image = tf.placeholder(tf.float32, [None, None, None, 4])
gt_image = tf.placeholder(tf.float32, [None, None, None, 3])
out_image = network(in_image)

saver = tf.train.Saver()
sess.run(tf.global_variables_initializer())
ckpt = tf.train.get_checkpoint_state(checkpoint_dir)
if ckpt:
    print('loaded ' + ckpt.model_checkpoint_path)
    saver.restore(sess, ckpt.model_checkpoint_path)

if not os.path.isdir(result_dir + 'final/'):
    os.makedirs(result_dir + 'final/')

for test_id in test_ids:
    # test the first image in each sequence
    in_files = glob.glob(input_dir + '%05d_00*.ARW' % test_id)
    for k in range(len(in_files)):
        print("====== routine start ! ========")
        in_path = in_files[k]
        in_fn = os.path.basename(in_path)
        print(in_fn)
        gt_files = glob.glob(gt_dir + '%05d_00*.ARW' % test_id)
        gt_path = gt_files[0]
        gt_fn = os.path.basename(gt_path)
        in_exposure = float(in_fn[9:-5])
        gt_exposure = float(gt_fn[9:-5])
        ratio = min(gt_exposure / in_exposure, 300)

        print("read raw image")
        raw = rawpy.imread(in_path)
        print("preprocess start")
        time_start = time.time()

        input_full = np.expand_dims(pack_raw(raw), axis=0) * ratio

        im = raw.postprocess(use_camera_wb=True, half_size=False, no_auto_bright=True, output_bps=16)
        # scale_full = np.expand_dims(np.float32(im/65535.0),axis = 0)*ratio
        scale_full = np.expand_dims(np.float32(im / 65535.0), axis=0)
        preprocess_time = time.time() - time_start

        input_full = np.minimum(input_full, 1.0)

        time_preprocess = time.time() - time_start
        print("Total preprocess time="+str(time_preprocess))

        print("=== sess.run start ===")
        print("k="+str(k))
        time_start = time.time()
        
        output = sess.run(out_image, feed_dict={in_image: input_full})
        process_time = time.time() - time_start
        print("Total time="+str(process_time))
        print("=== sess.run end ===")
        output = np.minimum(np.maximum(output, 0), 1)

        gt_raw = rawpy.imread(gt_path)
        im = gt_raw.postprocess(use_camera_wb=True, half_size=False, no_auto_bright=True, output_bps=16)
        gt_full = np.expand_dims(np.float32(im / 65535.0), axis=0)

        output = output[0, :, :, :]
        gt_full = gt_full[0, :, :, :]
        scale_full = scale_full[0, :, :, :]
        import pdb;pdb.set_trace()
        scale_full = scale_full * np.mean(gt_full) / np.mean(
            scale_full)  # scale the low-light image to the same mean of the groundtruth

        print("=== save image start ===")
        toimage(np.uint8(output * 255)).save(
            result_dir + 'final/%5d_00_%d_out.png' % (test_id, ratio))
        toimage(np.uint8(scale_full * 255)).save(
            result_dir + 'final/%5d_00_%d_scale.png' % (test_id, ratio))
        toimage(np.uint8(gt_full * 255)).save(
            result_dir + 'final/%5d_00_%d_gt.png' % (test_id, ratio))
        print("=== successfully saved image ===")
#         scipy.misc.toimage(output * 255, high=255, low=0, cmin=0, cmax=255).save(
#             result_dir + 'final/%5d_00_%d_out.png' % (test_id, ratio))
#         scipy.misc.toimage(scale_full * 255, high=255, low=0, cmin=0, cmax=255).save(
#             result_dir + 'final/%5d_00_%d_scale.png' % (test_id, ratio))
#         scipy.misc.toimage(gt_full * 255, high=255, low=0, cmin=0, cmax=255).save(
#             result_dir + 'final/%5d_00_%d_gt.png' % (test_id, ratio))
