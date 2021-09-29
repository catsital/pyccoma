from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

requirements = [
    "bs4==0.0.1",
    "requests==2.26.0",
    "git+https://github.com/catsital/pycasso.git"
    ]

setup(
    name="pyccoma",
    version="0.0.1",
    author="catsital",
    author_email="catshital@gmail.com",
    description="Scrape and download manga from Piccoma.",
    install_requires=requirements,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/catsital/pyccoma",
    project_urls={
        "Bug Tracker": "https://github.com/catsital/pyccoma/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    zip_safe=False
)
