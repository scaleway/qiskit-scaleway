from setuptools import setup, find_packages

with open("README.md", "r") as f:
    description = f.read()

setup(
    name="qiskit_scaleway",
    version="0.1.15",
    packages=find_packages(),
    install_requires=[
        "qiskit==1.1",
        "qiskit-aer==0.14.1",
        "randomname==0.2.1",
        "httpx==0.27.0",
        "dataclasses-json==0.6.4",
        "dataclasses==0.6",
        "pytimeparse==1.1.8",
        "python-dotenv==1.0.1",
    ],
    long_description=description,
    long_description_content_type="text/markdown",
)
