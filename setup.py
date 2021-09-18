from pathlib import Path
from setuptools import setup

from objexplore import version as VERSION

# The directory containing this file
cur_dir = Path(__file__).parent

# The text of the README file
README = (cur_dir / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="objexplore",
    version=VERSION,
    description="Interactive Python Object Explorer",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/kylepollina/objexplore",
    author="Kyle Pollina",
    author_email="kylepollina@pm.me",
    license="",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=["objexplore"],
    include_package_data=True,
    install_requires=["blessed==1.17.12", "rich==10.9.0"],
)
