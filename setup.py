# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

console_scripts = [
    'makiki = makiki.cli:main_parser',
]

requires = [
    'blinker>=1.4',
    'gevent>=1.1',
    'gunicorn>=19.0',
    'Jinja2>=2.8.1',
]

setup(
    name='makiki',
    version='0.0.1',
    description='',
    long_description='',
    author='Wang Yanqing',
    author_email='me@oreki.moe',
    packages=find_packages(),
    url='http://github.com/faith0811/makiki',
    include_package_data=True,
    entry_points={
        'console_scripts': console_scripts,
    },
    zip_safe=False,
    install_requires=requires,
)
