from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

requirements = [
    "lxml>=4.7.1",
    "requests==2.26.0",
    "image-scramble==2.0.1"
]

setup(
    name="pyccoma",
    version="0.6.1",
    author="catsital",
    author_email="catshital@gmail.com",
    description="Scrape and download from Piccoma Japan and France.",
    python_requires=">=3.11, <3.12",
    entry_points={"console_scripts": ["pyccoma=pyccoma.__main__:main"],},
    install_requires=requirements,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/catsital/pyccoma",
    project_urls={
        "Bug Tracker": "https://github.com/catsital/pyccoma/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    zip_safe=False
)
