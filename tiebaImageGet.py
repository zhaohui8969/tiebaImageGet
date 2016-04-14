# coding:utf-8
__author__ = 'natas'

import requests
import re
import os
from bs4 import BeautifulSoup


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
        self.savePageImages(soup, 1, MaxPageNum)
        for pageNum in range(2, MaxPageNum + 1):
            getparams = {'pn': 1}
            htmlCont = self._session.get(self.pURL, params=getparams).content
            soup = BeautifulSoup(htmlCont, 'lxml')
            self.savePageImages(soup, pageNum, MaxPageNum)
        print("本次共计抓图 %3d 张\n保存在 %s" % (self.imageCount, self.PWD))

    def savePageImages(self, pageSoup, jdNow, jdAll):
        for item in pageSoup.findAll('img', attrs={'class': "BDE_Image"}):
            srcurl = item.get('src')
            r = self._session.get(srcurl)
            if r:
                self.imageCount += 1
                with open(os.path.join(self.PWD, os.path.basename(srcurl)), 'w') as fopen:
                    fopen.write(r.content)
        print("进度: %3d/%3d" % (jdNow, jdAll))


def main():
    imageGetObj = ImageGet()
    imageGetObj('4071733071');
    pass


if __name__ == "__main__":
    main()
