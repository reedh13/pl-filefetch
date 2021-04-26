from os import path
from setuptools import setup

with open(path.join(path.dirname(path.abspath(__file__)), 'README.rst')) as f:
    readme = f.read()

setup(
    name             = 'filefetch',
    version          = '0.1',
    description      = 'An app to fetch files from a GitHub repo andsubsequent plugins.',
    long_description = readme,
    author           = 'reedh13',
    author_email     = 'dev@babyMRI.org',
    url              = 'http://wiki',
    packages         = ['filefetch'],
    install_requires = ['chrisapp'],
    test_suite       = 'nose.collector',
    tests_require    = ['nose'],
    license          = 'MIT',
    zip_safe         = False,
    python_requires  = '>=3.6',
    entry_points     = {
        'console_scripts': [
            'filefetch = filefetch.__main__:main'
            ]
        }
)
