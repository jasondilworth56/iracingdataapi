import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="iracingdataapi",
    version="1.1.6",
    author="Jason Dilworth",
    author_email="hello@jasondilworth.co.uk",
    description="A simple wrapper around the iRacing General Data API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jasondilworth56/iracingdataapi",
    project_urls={
        "Bug Tracker": "https://github.com/jasondilworth56/iracingdataapi/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=["requests"],
)
