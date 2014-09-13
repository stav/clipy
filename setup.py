from setuptools import setup

setup(
    name='clipy-dl',
    version='0.9.7',
    license='BSD',
    url='https://github.com/stav/clipy',
    download_url='https://github.com/stav/clipy/archive/master.zip',
    description='YouTube video downloader',
    long_description=open("README.rst").read(),
    author='Steven Almeroth',
    author_email='sroth77@gmail.com',
    keywords='video downloader',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Utilities',
    ],
    packages=['clipy'],
    package_data={"": ["CHANGELOG", "LICENSE", "README.rst"]},
    install_requires=['aiohttp', 'pyperclip'],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'clipy=clipy:main',
        ],
    },
)
