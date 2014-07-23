from setuptools import setup

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
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.4',
        'Topic :: Utilities',
    ],
    keywords='video downloader',
    install_requires=['Pafy', 'pyperclip'],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'clipy=clipy:main',
        ],
    },
)
