from setuptools import setup, find_packages

with open('README.md', 'r') as f:
  description = f.read()

setup(
  name='qiskit_scaleway',
  version='0.1.2',
  packages=find_packages(),
  install_requires=[
    'qiskit==1.0.2',
    'randomname==0.2.1'
  ],
  long_description=description,
  long_description_content_type='text/markdown'
)
