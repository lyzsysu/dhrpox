#!/usr/bin/env python
'''Setuptools params'''

from setuptools import setup, find_packages

setup(
    name='mininet platform',
    version='0.0.0',
    description='Implementation of Dynamic Hybrid Routing',
    author='Eugene Lee',
    author_email='Eugene Lee, 460893751@qq.com',
    packages=find_packages(exclude='test'),
    long_description="""\
For Dynamic Hybrid Routing, Based on Stanford CS244 Spring 2015 lab 3. Build on top of Brandon Heller's RIPL and RIPLPOX libraries
      """,
      classifiers=[
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Programming Language :: Python",
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "Topic :: Internet",
      ],
      keywords='networking protocol Internet OpenFlow data center datacenter',
      license='GPL',
      install_requires=[
        'setuptools',
        'networkx'
      ])
