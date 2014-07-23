from setuptools import setup

setup(
    name='clipy',
    version='0.5',
    url='https://github.com/stav/clipy',
    description='YouTube video downloader',
    long_description='''Command-line script for downloading videos from YouTube
        Command Line Interface using Python for Youtube''',
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
     dependency_links = [
        # 'http://github.com/gabrielgrant/django-ckeditor/tarball/master#egg=django-ckeditor-0.9.3',
        'git+https://github.com/np1/pafy.git@develop',
    ],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'clipy=clipy:main',
        ],
    },
)
