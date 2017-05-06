from setuptools import setup

setup(
    name='clipy-web',
    version='0.2',
    license='BSD',
    url='https://github.com/stav/clipy',
    download_url='https://github.com/stav/clipy/archive/master.zip',
    description='YouTube video downloader',
    long_description=open('README.md').read(),
    author='Steven Almeroth',
    author_email='sroth77@gmail.com',
    keywords='video downloader',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Utilities',
    ],
    packages=['clipy'],
    package_data={"": ["CHANGELOG", "LICENSE", "README.md", 'static/*.*']},
    include_package_data=True,
    install_requires=['aiohttp', 'aiodns', 'aiohttp_jinja2'],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'clipyd=clipy.server:main',
            'clipy=clipy.client:main',
        ],
    },
)
