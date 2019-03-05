from setuptools import setup, find_packages

setup(
    name="SinFactory",
    version="0.0.1",
    author="SINTEF Energy",
    description="Program for using powerfactory for power system analysis",
    packages=find_packages(exclude=["tests"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: custom",
        "Operating System :: OS Independent",
    ],
)
