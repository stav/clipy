from setuptools import setup, find_packages
from codecs import open  # To use a consistent encoding
from os import path

setup(
    name='clipy',
    version='0.4',
    description='YouTube video downloader',
    long_description='Command-line script for downloading videos from YouTube',
    url='https://github.com/stav/clipy',
    author='Steven Almeroth',
    author_email='sroth77@gmail.com',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='video downloader',
    # packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=['Pafy', 'pyperclip'],
    entry_points={
        'console_scripts': [
            'clipy=clipy:main',
        ],
    },
)
