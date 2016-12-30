# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

console_scripts = [
    'makiki = makiki.cli:main_parser',
]

requires = [
    'blinker>=1.4',
    'gevent==1.1.2',
    'gunicorn>=19.0',
    'Jinja2>=2.8.1',
    'psycogreen>=1.0.0',
    'psycopg2>=2.6.2',
    'hug>=2.1.2',
]

setup(
    name='makiki',
    version='0.1.1',
    description='Web service utils and generator.',
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
