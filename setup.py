from setuptools import find_packages
from setuptools import setup


with open("README.md") as f:
    LONG_DESCRIPTION = f.read()


# def get_install_requires():
#     with open("requirements.txt") as f:
#         return [line.strip() for line in f.readlines() if not line.startswith("-")]


setup(
    name="klayout_pyxs",
    version="0.1.9",
    url="https://github.com/dimapu/klayout_pyxs",
    license="MIT",
    author="Dima Pustakhod",
    description="python port of the Klayout xsection project",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=("tests",)),
    # install_requires=get_install_requires(),
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python",
    ],
)
