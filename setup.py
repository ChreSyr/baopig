# Always prefer setuptools over distutils
from setuptools import setup

# To use a consistent encoding
from codecs import open
from os import path

# Get the version number without importing baopig
import sys
sys.path.append(".\\baopig\\version")
from version import version

# The directory containing this file
HERE = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(HERE, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# This call to setup() does all the work
setup(
    name="baopig",
    version=str(version),
    description="pygame gui",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://baopig.readthedocs.io/",
    author="Symeon Rougevin-Baville",
    author_email="dev.chresyr@gmail.com",
    license="MIT",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent"
    ],
    packages=["baopig"],
    package_data={'baopig': ['*', '*/*', '*/*/*', '*/*/*/*', '*/*/*/*/*', '*/*/*/*/*/*'], },  # TODO : find a better way
    include_package_data=True,
    install_requires=[
        "pygame",
        "httpcore",
        "httpx"
    ]
)
