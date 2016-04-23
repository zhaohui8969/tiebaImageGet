# coding:utf-8

import requests
import os
from bs4 import BeautifulSoup
import colorama
import threading
import signal
import time
import datetime
from optparse import OptionParser
from downloader import Downloader

__author__ = 'natas'

colorama.init(autoreset=True)


class ImageGet:
    """
    主要的类，实现图片下载
    """

    def __init__(self, maxThread, save_directory):
        """
        初始化
        :return:None
        """
        self.head = {'X-Requested-With': 'XMLHttpRequest',
                     'Referer': 'http://www.baidu.com',
                     'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; '
                                   'rv:39.0) Gecko/20100101 Firefox/39.0'}
        self._session = requests.session()
        self._session.headers.update(self.head)
        self.imageCount = 0
        self.lock_imageCount = threading.Lock()
        self._is_Exit = False  # 线程终止信号
        self.maxThread = maxThread  # 最大线程数
        self.save_directory = save_directory  # 保存位置
        signal.signal(signal.SIGINT, self.handler)  # 设置对Ctrl - c 的响应
        signal.signal(signal.SIGTERM, self.handler)

    def __call__(self, pID):
        """
        开始下载
        :param pID:     帖子的ID
        :param maxThread:    最大线程数
        :return:None
        """
        self._start_time = datetime.datetime.now()  # 计时用
        self.PWD = os.path.join(self.save_directory, str(pID))
        self.downloader = Downloader(self.maxThread, self.PWD, self._callback_imageCountAdd)  # 设置图片下载器
        print(u"%s红色有角 %sx%d %s倍速！" %
              (colorama.Fore.RED, colorama.Fore.GREEN, self.maxThread, colorama.Fore.RED))
        self.pURL = r'http://tieba.baidu.com/p/' + str(pID)
        print(u"抓取帖子：%s\n" % self.pURL)

        getparams = {'pn': 1}
        htmlCont = requests.get(self.pURL, params=getparams).content
        soup = BeautifulSoup(htmlCont, 'lxml')
        pageList = soup.find('li', attrs={'class': 'l_reply_num'})
        MaxPageNum = int(pageList.contents[2].string)  # 总页数

        # # 显示进度条
        # self._progressBar = Bar(u'进度', max=MaxPageNum)  # 显示进度条
        # self._progressBar.update()

        # 网页抓取部分的多线程任务分割
        pool = {}  # 任务池
        threadPool = []  # 线程池
        threadNum = self.maxThread  # 投入使用的线程数
        if threadNum > MaxPageNum:
            threadNum = MaxPageNum

        pagesPerThread = MaxPageNum / threadNum  # 每个线程处理的页面数
        remainPages = MaxPageNum % threadNum  # 均分后剩下的页面数

        # 计算任务的分割
        for i in range(remainPages):
            pool[i] = (i * (pagesPerThread + 1) + 1, (i + 1) * (pagesPerThread + 1) + 1)
        disJob = remainPages * (pagesPerThread + 1)
        for i in range(threadNum - remainPages):
            pool[remainPages + i] = (disJob + i * pagesPerThread + 1, disJob + (i + 1) * pagesPerThread + 1)

        # 启动所有线程
        lock = threading.Lock()
        for i in pool.keys():
            pro = threading.Thread(target=self.savePageImages,
                                   args=(lock, pool[i][0], pool[i][1]))
            threadPool.append(pro)
            pro.start()
        # 处理线程的退出
        while True:
            alive = False
            for i in threadPool:
                alive = alive or i.isAlive()
            alive = alive or self.downloader.is_alive()
            if not alive:
                break
            time.sleep(0.5)

        # self._progressBar.finish()  # 下载完显示进度条
        self._repoter()  # 显示报告

    def _callback_imageCountAdd(self, imageNum):
        """
        一个回调，下载线程返回下载的图片统计，在这里被汇总统计
        :param imageNum:
        :return:
        """
        with self.lock_imageCount:
            self.imageCount += imageNum

    def savePageImages(self, lock, start, end):
        """
        保存图片到文件
        :param lock: 线程锁
        :param start: 页数开始数字
        :param end: 页数结束数字
        :return:None
        """
        for pageNum in range(start, end):
            # 判断是否终止线程
            if self._is_Exit:
                return
            getparams = {'pn': pageNum}
            htmlCont = requests.get(self.pURL, params=getparams).content
            soup = BeautifulSoup(htmlCont, 'lxml')
            for item in soup.findAll('img', attrs={'class': "BDE_Image"}):
                srcurl = item.get('src')  # 图片地址
                if not self._is_Exit:
                    self.downloader.add_task(srcurl)
                    # with lock:
                    #     self._progressBar.next()

    def _repoter(self):
        """
        显示报告
        :return:None
        """
        usedTime = datetime.datetime.now() - self._start_time
        print(u"\n本次共计抓图 %s%d%s 张\n"
              u"用时 %s%s%s\n"
              u"保存在 %s%s" %
              (colorama.Fore.GREEN, self.imageCount, colorama.Fore.RESET,
               colorama.Fore.YELLOW, usedTime, colorama.Fore.RESET,
               colorama.Fore.YELLOW, self.PWD))  # 格式化输出报告信息

    def handler(self, _, _):
        self._is_Exit = True
        self.downloader._break()
        print(u"\n%s不急...准备退出...正在善后..." % colorama.Fore.RED)


def main():
    # 处理命令行参数
    usage = u"%prog <-p 帖子ID> [-t 线程数]"
    parser = OptionParser(usage=usage)
    parser.add_option('-p', dest='pid', type='int', help=u'设置帖子ID')
    parser.add_option('-t', dest='max_thread_num', type='int', help=u'设置使用的线程数', default=10)
    parser.add_option('-d', dest='save_directory', type='string', help=u'设置图片的保存目录', default=u'.')
    args, _ = parser.parse_args()
    # 未设置关键参数时显示帮助
    if not args.pid:
        parser.print_help()
        return
    parser.print_version()
    # 有异常？不管
    try:
        imageGetObj = ImageGet(args.max_thread_num, args.save_directory)
        imageGetObj(args.pid)
    except Exception as e:
        print(u'\n出了一些问题, 你可以自己去main()里的try块改改自己看看bug\n')


if __name__ == "__main__":
    main()
