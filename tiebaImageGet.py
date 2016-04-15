# coding:utf-8
"""
USAGE:

python tiebaImageGet.py <pID>

:param pID: 帖子的ID

文件会保存在当前目录下的<pID>文件夹下

example：    对于 http://tieba.baidu.com/p/3421939896
            python tiebaImageGet.py 3421939896

"""
__author__ = 'natas'

import requests
import os
from bs4 import BeautifulSoup
from progress.bar import Bar
import colorama
import sys
import threading
import signal
import time
import datetime

colorama.init(autoreset=True)


class ImageGet:
    """
    主要的类，实现图片下载
    """

    def __init__(self, maxThread=10):
        """
        初始化
        :return:
        """
        self.head = {'X-Requested-With': 'XMLHttpRequest',
                     'Referer': 'http://www.baidu.com',
                     'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; '
                                   'rv:39.0) Gecko/20100101 Firefox/39.0'}
        self._session = requests.session()
        self._session.headers.update(self.head)
        self.imageCount = 0
        self._is_Exit = False  # 线程终止信号
        self.basePWD = r'image'  # 保存目录
        self.maxThread = maxThread  # 最大线程数
        signal.signal(signal.SIGINT, self.handler)  # 设置对Ctrl - c 的响应
        signal.signal(signal.SIGTERM, self.handler)
        print("%s红色有角 %sx%d %s倍速！" %
              (colorama.Fore.RED, colorama.Fore.GREEN, maxThread, colorama.Fore.RED))

    def __call__(self, pID):
        """
        类的可调用方法
        :param pID:帖子的id
        :return:None
        """
        self._start_time = datetime.datetime.now()  # 计时用
        self.pURL = r'http://tieba.baidu.com/p/' + pID
        print("抓取帖子：%s\n" % self.pURL)
        # 创建文件夹
        self.PWD = os.path.join(self.basePWD, pID)
        if not os.path.exists(self.PWD):
            os.makedirs(self.PWD)
        getparams = {'pn': 1}
        htmlCont = self._session.get(self.pURL, params=getparams).content
        soup = BeautifulSoup(htmlCont, 'lxml')
        pageList = soup.find('li', attrs={'class': 'l_reply_num'})
        MaxPageNum = int(pageList.contents[2].string)  # 总页数

        # 显示进度条
        self._progressBar = Bar('进度', max=MaxPageNum)  # 显示进度条
        self._progressBar.update()
        # 多线程任务分割
        pool = {}  # 任务池
        threadPool = []  # 线程池
        self._sessionPool = []  # session池子
        threadNum = self.maxThread  # 投入使用的线程数
        if threadNum > MaxPageNum:
            threadNum = MaxPageNum
        # 准备session池子
        for i in range(threadNum):
            _session = requests.session()
            _session.headers.update(self.head)
            self._sessionPool.append(_session)
        pagesPerThread = MaxPageNum / threadNum  # 每个线程处理的页面数
        remainPages = MaxPageNum % threadNum  # 均分后剩下的页面数
        # 计算任务的分割
        for i in range(remainPages):
            pool[i] = (i * (pagesPerThread + 1) + 1, (i + 1) * (pagesPerThread + 1) + 1)
        disJob = remainPages * (pagesPerThread + 1)
        for i in range(threadNum - remainPages):
            pool[remainPages + i] = (disJob + i * pagesPerThread + 1, disJob + (i + 1) * pagesPerThread + 1)
        # 启动所有线程
        _sessionIter = iter(self._sessionPool)  # 迭代取出session
        lock = threading.Lock()
        for i in pool.keys():
            pro = threading.Thread(target=self.savePageImages,
                                   args=(lock, _sessionIter.next(), pool[i][0], pool[i][1]))
            threadPool.append(pro)
            pro.start()
        # # 所有线程join
        # for pro in threadPool:
        #     pro.join()
        # 每隔一段时间检测一下线程的状态
        while True:
            alive = False
            for i in threadPool:
                alive = alive or i.isAlive()
            if not alive:
                break
            time.sleep(3)

        self._progressBar.finish()  # 下载完显示进度条
        self._repoter()  # 显示报告

    def savePageImages(self, lock, _session, start, end):
        """
        保存页面中的图片
        :param pageSoup:页面的Soup对象
        :return:None
        """
        for pageNum in range(start, end):
            # 判断是否终止线程
            if self._is_Exit:
                return
            getparams = {'pn': pageNum}
            htmlCont = _session.get(self.pURL, params=getparams).content
            soup = BeautifulSoup(htmlCont, 'lxml')
            for item in soup.findAll('img', attrs={'class': "BDE_Image"}):
                srcurl = item.get('src')  # 图片地址
                r = _session.get(srcurl)
                if r:
                    fileName = os.path.join(self.PWD, os.path.basename(srcurl))  # 拼接文件名
                    if not os.path.exists(fileName):
                        self.imageCount += 1  # 本次抓取到的图片数+1
                        with open(fileName, 'wb') as fopen:
                            fopen.write(r.content)  # 保存图片
            with lock:
                self._progressBar.next()

    def _repoter(self):
        """
        显示报告
        :return:None
        """
        usedTime = datetime.datetime.now() - self._start_time
        print("本次共计抓图 %s%d%s 张\n"
              "用时 %s%s%s\n"
              "保存在 %s%s" %
              (colorama.Fore.GREEN, self.imageCount, colorama.Fore.RESET,
               colorama.Fore.YELLOW, usedTime, colorama.Fore.RESET,
               colorama.Fore.YELLOW, self.PWD))  # 格式化输出报告信息

    def handler(self, signum, frame):
        self._is_Exit = True
        print("\n%s不急...准备退出...正在善后..." % colorama.Fore.RED)


def main():
    # 处理命令行参数
    lenOfArgv = len(sys.argv)
    if lenOfArgv == 1:
        print(__doc__)
        return
    pID = sys.argv[1]  # 帖子ID
    if lenOfArgv > 2:
        maxThread = int(sys.argv[2])
        imageGetObj = ImageGet(maxThread)  # 设置线程数
    else:
        imageGetObj = ImageGet()
    imageGetObj(pID)


if __name__ == "__main__":
    main()
