import time
import random
import cv2
import os
import numpy as np
from skimage.util import random_noise
import base64
import json
import re
from copy import deepcopy
import argparse


class DataAugmentForObjectDetection():
    # 代码中包含五中数据增强的手段(噪声，光线，改变像素点，平移，镜像，打开后的数据增强为True，取消为False)
    def __init__(self, change_light_rate=0.5,
                 add_noise_rate=0.3, random_point=0.5, flip_rate=0.5, shift_rate=0, rand_point_percent=0,
                 is_addNoise=True, is_changeLight=True, is_random_point=True, is_shift_pic_bboxes=False,
                 is_filp_pic_bboxes=True):

        self.change_light_rate = change_light_rate
        self.add_noise_rate = add_noise_rate
        self.random_point = random_point
        self.flip_rate = flip_rate
        self.shift_rate = shift_rate
        self.rand_point_percent = rand_point_percent

        # 是否使用某种增强方式
        self.is_addNoise = is_addNoise
        self.is_changeLight = is_changeLight
        self.is_random_point = is_random_point
        self.is_filp_pic_bboxes = is_filp_pic_bboxes
        self.is_shift_pic_bboxes = is_shift_pic_bboxes

    # 加噪声(随机噪声)
    def _addNoise(self, img):
        return random_noise(img, seed=int(time.time())) * 255

    # 调整亮度
    def _changeLight(self, img):
        alpha = random.uniform(0.35, 1)
        blank = np.zeros(img.shape, img.dtype)
        return cv2.addWeighted(img, alpha, blank, 1 - alpha, 0)

    # 随机的改变点的值
    def _addRandPoint(self, img):
        percent = self.rand_point_percent
        num = int(percent * img.shape[0] * img.shape[1])
        for i in range(num):
            rand_x = random.randint(0, img.shape[0] - 1)
            rand_y = random.randint(0, img.shape[1] - 1)
            if random.randint(0, 1) == 0:
                img[rand_x, rand_y] = 0
            else:
                img[rand_x, rand_y] = 255
        return img

    # 平移图像(注：需要到labelme工具上调整图像，部分平移的标注框可能会超出图像边界，对训练造成影响)
    def _shift_pic_bboxes(self, img, json_info):
        h, w, _ = img.shape
        x_min = w
        x_max = 0
        y_min = h
        y_max = 0
        shapes = json_info['shapes']
        for shape in shapes:
            points = np.array(shape['points'])
            x_min = min(x_min, points[:, 0].min())
            y_min = min(y_min, points[:, 1].min())
            x_max = max(x_max, points[:, 0].max())
            y_max = max(y_max, points[:, 0].max())
        d_to_left = x_min
        d_to_right = w - x_max
        d_to_top = y_min
        d_to_bottom = h - y_max
        x = random.uniform(-(d_to_left - 1) / 3, (d_to_right - 1) / 3)
        y = random.uniform(-(d_to_top - 1) / 3, (d_to_bottom - 1) / 3)

        M = np.float32([[1, 0, x], [0, 1, y]])
        shift_img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
        for shape in shapes:
            for p in shape['points']:
                p[0] += x
                p[1] += y
        return shift_img, json_info

    # 图像镜像翻转
    def _filp_pic_bboxes(self, img, json_info):
        h, w, _ = img.shape
        sed = random.random()
        if 0 < sed < 0.33:
            flip_img = cv2.flip(img, 0)  # _flip_x
            inver = 0
        elif 0.33 < sed < 0.66:
            flip_img = cv2.flip(img, 1)  # _flip_y
            inver = 1
        else:
            flip_img = cv2.flip(img, -1)  # flip_x_y
            inver = -1
        shapes = json_info['shapes']
        for shape in shapes:
            for p in shape['points']:
                if inver == 0:
                    p[1] = h - p[1]
                elif inver == 1:
                    p[0] = w - p[0]
                elif inver == -1:
                    p[0] = w - p[0]
                    p[1] = h - p[1]
        return flip_img, json_info

    def dataAugment(self, img, dic_info):
        change_num = 0
        while change_num < 1:
            if self.is_changeLight:
                if random.random() > self.change_light_rate:
                    change_num += 1
                    img = self._changeLight(img)

            if self.is_addNoise:
                if random.random() < self.add_noise_rate:
                    change_num += 1
                    img = self._addNoise(img)
            if self.is_random_point:
                if random.random() < self.random_point:
                    change_num += 1
                    img = self._addRandPoint(img)
            if self.is_shift_pic_bboxes:
                if random.random() < self.shift_rate:
                    change_num += 1
                    img, dic_info = self._shift_pic_bboxes(img, dic_info)
            if self.is_filp_pic_bboxes or 1:
                if random.random() < self.flip_rate:
                    change_num += 1
                    img, bboxes = self._filp_pic_bboxes(img, dic_info)
        return img, dic_info


class ToolHelper():
    # 从json文件中提取原始标定的信息
    def parse_json(self, path):
        with open(path) as f:
            json_data = json.load(f)
        return json_data

    # 对图片进行字符编码
    def img2str(self, img_name):
        with open(img_name, "rb") as f:
            base64_data = str(base64.b64encode(f.read()))
        match_pattern = re.compile(r'b\'(.*)\'')
        base64_data = match_pattern.match(base64_data).group(1)
        return base64_data

    # 保存图片结果
    def save_img(self, save_path, img):
        cv2.imwrite(save_path, img)

    # 保持json结果
    def save_json(self, file_name, save_folder, dic_info):
        with open(os.path.join(save_folder, file_name), 'w') as f:
            json.dump(dic_info, f, indent=2)


if __name__ == '__main__':
    need_aug_num = 1  # 每张图片需要增强的次数
    toolhelper = ToolHelper()
    is_endwidth_dot = True  # 文件是否以.jpg或者png结尾
    dataAug = DataAugmentForObjectDetection()
    parser = argparse.ArgumentParser()
    parser.add_argument('--source_img_json_path', type=str,
                        default=r'F:\1')  # 需要更改的json地址
    parser.add_argument('--save_img_json_path', type=str,
                        default=r'F:\2')  # 改变后的json保存地址
    args = parser.parse_args()
    source_img_json_path = args.source_img_json_path  # 图片和json文件原始位置
    save_img_json_path = args.save_img_json_path  # 图片增强结果保存文件

    # 如果保存文件夹不存在就创建
    if not os.path.exists(save_img_json_path):
        os.mkdir(save_img_json_path)

    for parent, _, files in os.walk(source_img_json_path):
        files.sort()  # 排序一下
        for file in files:
            if file.endswith('jpg') or file.endswith('png'):
                cnt = 0
                pic_path = os.path.join(parent, file)
                json_path = os.path.join(parent, file[:-4] + '.json')
                json_dic = toolhelper.parse_json(json_path)
                # 如果图片是有后缀的
                if is_endwidth_dot:
                    # 找到文件的最后名字
                    dot_index = file.rfind('.')
                    _file_prefix = file[:dot_index]  # 文件名的前缀
                    _file_suffix = file[dot_index:]  # 文件名的后缀
                img = cv2.imread(pic_path)

                while cnt < need_aug_num:  # 继续增强
                    auged_img, json_info = dataAug.dataAugment(deepcopy(img), deepcopy(json_dic))
                    img_name = '{}_{}{}'.format(_file_prefix, cnt + 1, _file_suffix)  # 图片保存的信息
                    img_save_path = os.path.join(save_img_json_path, img_name)
                    toolhelper.save_img(img_save_path, auged_img)  # 保存增强图片

                    json_info['imagePath'] = img_name
                    base64_data = toolhelper.img2str(img_save_path)
                    json_info['imageData'] = base64_data
                    toolhelper.save_json('{}_{}.json'.format(_file_prefix, cnt + 1),
                                         save_img_json_path, json_info)  # 保存xml文件
                    print(img_name)
                    cnt += 1  # 继续增强下一张
