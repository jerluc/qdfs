#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='qdfs',
    version='0.1.0-alpha',
    description='An easily-deployable distributed file system',
    author='Jeremy Lucas',
    author_email='jeremyalucas@gmail.com',
    url='https://github.com/jerluc/qdfs',
    packages=['qdfs'],
    entry_points={
        'console_scripts': ['qdfs=qdfs.__main__:main'],
    },
    install_requires=[l.strip() for l in open('requirements.txt')],
    license='License :: OSI Approved :: Apache Software License',
)
