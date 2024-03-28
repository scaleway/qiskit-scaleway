from setuptools import setup, find_packages

with open('README.md', 'r') as f:
  description = f.read()

setup(
  name='qiskit_scaleway',
  version='0.1.3',
  packages=find_packages(),
  install_requires=[
    'qiskit==1.0.2',
    'randomname==0.2.1',
    'httpx==0.27.0',
    'dataclasses-json==0.6.4',
    'dataclasses==0.6'
  ],
  long_description=description,
  long_description_content_type='text/markdown'
)
