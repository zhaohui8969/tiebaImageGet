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

colorama.init(autoreset=True)


class ImageGet:
    """
    主要的类，实现图片下载
    """

    def __init__(self):
        """
        初始化，设置request的session
        设置http的头
        :return:
        """
        self._session = requests.session()
        self.head = {'X-Requested-With': 'XMLHttpRequest',
                     'Referer': 'http://www.baidu.com',
                     'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; '
                                   'rv:39.0) Gecko/20100101 Firefox/39.0'}
        self._session.headers.update(self.head)
        self.imageCount = 0
        self.basePWD = r'image'  # 保存目录

    def __call__(self, pID):
        """
        类的可调用方法
        :param pID:帖子的id
        :return:None
        """
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

        # 遍历每一页
        self._progressBar = Bar('进度', max=MaxPageNum)  # 显示进度条
        self._progressBar.update()
        self.savePageImages(soup)  # 第一页
        # 从第二页开始
        for pageNum in range(2, MaxPageNum + 1):
            getparams = {'pn': pageNum}
            htmlCont = self._session.get(self.pURL, params=getparams).content
            soup = BeautifulSoup(htmlCont, 'lxml')
            self.savePageImages(soup)  # 保存页面中的图片
        self._progressBar.finish()
        self._repoter()  # 显示报告

    def savePageImages(self, pageSoup):
        """
        保存页面中的图片
        :param pageSoup:页面的Soup对象
        :return:None
        """
        for item in pageSoup.findAll('img', attrs={'class': "BDE_Image"}):
            srcurl = item.get('src')  # 图片地址
            r = self._session.get(srcurl)
            if r:
                fileName = os.path.join(self.PWD, os.path.basename(srcurl))  # 拼接文件名
                if not os.path.exists(fileName):
                    self.imageCount += 1  # 本次抓取到的图片数+1
                    with open(fileName, 'w') as fopen:
                        fopen.write(r.content)  # 保存图片
        self._progressBar.next()

    def _repoter(self):
        """
        显示报告
        :return:None
        """
        print("本次共计抓图 %s%d%s 张\n保存在 %s%s" %
              (colorama.Fore.GREEN, self.imageCount, colorama.Fore.RESET,
               colorama.Fore.YELLOW, self.PWD))  # 格式化输出报告信息


def main():
    # 处理命令行参数
    if not len(sys.argv) == 2:
        print(__doc__)
        return
    pID = sys.argv[1]  # 帖子ID

    imageGetObj = ImageGet()
    try:
        imageGetObj(pID)
    except (KeyboardInterrupt, SystemExit) as e:
        # 处理Ctrl + c 退出
        print('\n\n用户取消')
        imageGetObj._repoter()


if __name__ == "__main__":
    main()
