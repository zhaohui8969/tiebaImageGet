# coding:utf-8
from setuptools import setup, find_packages
from tiebaImageGet import __author__, __email__, __version__

with open('requires.txt') as f:
    requirements = [l for l in f.read().splitlines() if l]

setup(
    name='tiebaImageGet',
    version=__version__,
    packages=find_packages(),
    url='https://github.com/zhaohui8969/tiebaImageGet',
    license='GPLv2',
    author=__author__,
    keywords='crawl tieba image',
    author_email=__email__,
    description=u'贴吧图楼爬图器',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'tiebaImageGet = tiebaImageGet.tiebaImageGet:main',
        ]
    },
)
