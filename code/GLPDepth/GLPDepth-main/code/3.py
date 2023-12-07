# coding=utf-8
import cv2
import os
import threading
from threading import Lock, Thread

video_path = ""
pic_path = ""
filelist = os.listdir(video_path)


def video2pic(filename):
    # print(filename)
    cnt = 0
    dnt = 0
    if os.path.exists(pic_path + str(filename)):
        pass
    else:
        os.mkdir(pic_path + str(filename))
    cap = cv2.VideoCapture(video_path + str(filename))  # 读入视频
    while True:
        # get a frame
        ret, image = cap.read()
        if image is None:
            break
        # show a frame

        w = image.shape[1]
        h = image.shape[0]
        if (cnt % 80) == 0:
            cv2.imencode('.jpg', image)[1].tofile(pic_path + str(filename) + '/' + str(dnt) + '.jpg')
            print(pic_path + str(filename) + '/' + str(dnt) + '.jpg')
            dnt = dnt + 1
        cnt = cnt + 1
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()


if __name__ == '__main__':
    for filename in filelist:
        threading.Thread(target=video2pic, args=(filename,)).start()