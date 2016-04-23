# coding:utf-8
import requests
import os
import threadpool
from threading import Lock
import sys

__author__ = 'natas'


class Downloader:
    def __init__(self, max_thread, save_directory, _callback_image_count_add):
        self.max_thread = max_thread
        self.save_directory = save_directory
        self._is_alive = True
        self._callback_imageCountAdd = _callback_image_count_add
        # 设置线程池
        self.threadPool = threadpool.ThreadPool(self.max_thread)
        self.lock = Lock()
        # 创建文件夹
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)

    def add_task(self, url):
        with self.lock:
            self._is_alive = True
        reqs = threadpool.makeRequests(self._download, [url, ], self._callback)
        [self.threadPool.putRequest(req, timeout=1) for req in reqs]

    def _callback(self, _, image_num):
        if not image_num:
            return
        if image_num == 1:
            sys.stdout.write('+')
            self._callback_imageCountAdd(image_num)
        else:
            sys.stdout.write('-')

    def _download(self, url):
        if self.is_alive():
            r = requests.request('GET', url)
            if r:
                filename = os.path.join(self.save_directory, os.path.basename(url))  # 拼接文件名
                if not os.path.exists(filename):
                    with open(filename, 'wb') as f:
                        f.write(r.content)  # 保存图片
                    return 1
                else:
                    return -1
        else:
            return None

    def breakme(self):
        with self.lock:
            self._is_alive = False

    def is_alive(self):
        try:
            self.threadPool.poll()  # 看看有没有任务完成
        except threadpool.NoResultsPending:
            self.breakme()
        return self._is_alive
