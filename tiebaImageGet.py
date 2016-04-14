# coding:utf-8
__author__ = 'natas'

import requests
import os
from bs4 import BeautifulSoup
from progress.bar import Bar
import colorama

colorama.init(autoreset=True)


class ImageGet:
    def __init__(self):
        self._session = requests.session()
        self.head = {'X-Requested-With': 'XMLHttpRequest',
                     'Referer': 'http://www.baidu.com',
                     'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; '
                                   'rv:39.0) Gecko/20100101 Firefox/39.0'}
        self._session.headers.update(self.head)
        self.imageCount = 0
        self.basePWD = r'image'

    def __call__(self, id):
        self.pURL = r'http://tieba.baidu.com/p/' + id
        print("抓取帖子：%s\n" % self.pURL)
        # 创建文件夹
        self.PWD = os.path.join(self.basePWD, id)
        if not os.path.exists(self.PWD):
            os.makedirs(self.PWD)
        # pn Loop
        getparams = {'pn': 1}
        htmlCont = self._session.get(self.pURL, params=getparams).content
        soup = BeautifulSoup(htmlCont, 'lxml')
        pageList = soup.find('li', attrs={'class': 'l_reply_num'})
        MaxPageNum = int(pageList.contents[2].string)

        # 开始循环每一页抓图
        self._progressBar = Bar('进度', max=MaxPageNum)
        self._progressBar.update()
        self.savePageImages(soup)
        for pageNum in range(2, MaxPageNum + 1):
            getparams = {'pn': pageNum}
            htmlCont = self._session.get(self.pURL, params=getparams).content
            soup = BeautifulSoup(htmlCont, 'lxml')
            self.savePageImages(soup)
        self._progressBar.finish()
        self._repoter()

    def savePageImages(self, pageSoup):
        for item in pageSoup.findAll('img', attrs={'class': "BDE_Image"}):
            srcurl = item.get('src')
            r = self._session.get(srcurl)
            if r:
                fileName = os.path.join(self.PWD, os.path.basename(srcurl))
                if not os.path.exists(fileName):
                    self.imageCount += 1
                    with open(fileName, 'w') as fopen:
                        fopen.write(r.content)
        self._progressBar.next()

    def _repoter(self):
        print("本次共计抓图 %s%d%s 张\n保存在 %s%s" %
              (colorama.Fore.GREEN, self.imageCount, colorama.Fore.RESET,
               colorama.Fore.YELLOW, self.PWD))


def main():
    imageGetObj = ImageGet()
    try:
        imageGetObj('3421939896')
    except (KeyboardInterrupt, SystemExit) as e:
        print('\n\n用户取消')
        imageGetObj._repoter()


if __name__ == "__main__":
    main()
