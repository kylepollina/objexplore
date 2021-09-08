from pathlib import Path
from setuptools import setup

from objex import version as VERSION

# The directory containing this file
cur_dir = Path(__file__).parent

# The text of the README file
README = (cur_dir / "README.md").read_text()

# This call to setup() does all the work
setup(
    name='embedmd',
    version=VERSION,
    description='Embed markdown files into html',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/kylepollina/embedmd',
    author='Kyle Pollina',
    author_email='kylepollina@pm.me',
    license='',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    packages=['embedmd'],
    include_package_data=True,
    install_requires=['markdown', 'argparse_ext'],
    entry_points={
        'console_scripts': [
            'embedmd=embedmd.core:embedmd'
        ]
    },
)
