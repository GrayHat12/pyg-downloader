import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyg-downloader",
    version="0.0.1",
    author="GrayHat12",
    author_email="grayhathacks10@gmail.com",
    description="python download manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GrayHat12/download-manager",
    project_urls={
        "Bug Tracker": "https://github.com/GrayHat12/pyg-downloader/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
    ],
    keywords="download manager downloader file downloader",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    requires=['requests'],
    extras_require={
        'atpbar': ['atpbar']
    }
)