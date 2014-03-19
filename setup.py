import os
from setuptools import setup, find_packages

version = '0.8'

if os.path.exists("README.rst"):
    long_description = open("README.rst").read()
else:
    long_description = "See http://www.jsonweb.net/en/latest"

setup(name='JsonWeb',
      version=version,
      description="Quickly add json serialization and deserialization to your python classes.",
      long_description=long_description,
      keywords='',
      author='Shawn Adams',
      author_email='',
      url='',
      license='BSD',
      packages=find_packages(exclude=['examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Software Development :: Libraries :: Python Modules'
      ]
      )
