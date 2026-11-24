from setuptools import setup, find_packages

setup(
    name="vscu-python-sdk",
    version="1.0.0",
    description="Python SDK for KRA eTIMS VSCU (Virtual Sales Control Unit) integration",
    author="ongudidan",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
    ],
    python_requires=">=3.8",
)
