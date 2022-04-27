import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name="migration-from-excel",
    version="0.0.1",
    author="cglee",
    author_email="cglee@snowpipe.co.kr",
    description="A simple tool for migration from excel",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="http://172.20.41.70:3000/SPTeam/excel_to_db.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)