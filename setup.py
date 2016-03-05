#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pip

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
                'celery>=3.1.19',
                'gevent>=1.0.2',
                #install fork git+https://github.com/jlmadurga/yowsup.git@issue_1181#egg=yowsup 
                'yowsup2'
                ]
test_requirements = requirements + [
                     'mock>=1.3.0'
                     ]


setup(
    name='yowsup-celery',
    version='0.2.0',
    description="Yowsup integrated in a celery architecture",
    long_description=readme + '\n\n' + history,
    author="Juan Madurga",
    author_email='jlmadurga@gmail.com',
    url='https://github.com/jlmadurga/yowsup-celery',
    packages=[
        'yowsup_celery',
    ],
    package_dir={'yowsup_celery':
                 'yowsup_celery'},
    include_package_data=True,
    install_requires= requirements,
    license="ISCL",
    zip_safe=False,
    keywords='yowsup-celery',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
