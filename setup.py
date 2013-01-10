#!/usr/bin/env python

import sys
import os
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup  # NOQA

if sys.argv[-1] in ("submit", "publish"):
    os.system("python setup.py sdist upload")
    sys.exit()

packages = [
    "cfg"
]
requires = []

__version__ = ''
with open('cfg/__init__.py', 'r') as fd:
    reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
    for line in fd:
        m = reg.match(line)
        if m:
            __version__ = m.group(1)
            break

if not __version__:
    raise RuntimeError('Cannot find version information')

setup(
    name="cfg",
    version=__version__,
    description=("Control Flow Graph Generator"),
    long_description="\n\n".join([open("README.rst").read(),
                                  open("HISTORY.rst").read()]),
    license=open('LICENSE').read(),
    author="Ian Cordasco, Ashwin Panchapakesan",
    author_email="graffatcolmingov@gmail.com, ashwin.panchapakesan@gmail.com",
    url="https://github.com/sigmavirus24/cfg",
    packages=packages,
    package_data={'': ['LICENSE', 'AUTHORS.rst']},
    include_package_data=True,
    install_requires=requires,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
