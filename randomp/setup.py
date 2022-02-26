# flake8: noqa
from setuptools import setup

setup(
    name='randomparty-exercise',
    version='1.0.0',
    description=
    '''A python3 party that places random bids with sufficient utility.
    Slightly modified to follow the GeniusWeb beginner guide
    (https://tracinsy.ewi.tudelft.nl/pubtrac/GeniusWeb/export/HEAD/tutorials/SAOP/tutorial.pdf)''',
    url='https://tracinsy.ewi.tudelft.nl/pubtrac/GeniusWeb',
    author='W.Pasman',
    packages=['randomparty'],
    install_requires=[
        "geniusweb@https://tracinsy.ewi.tudelft.nl/pubtrac/GeniusWebPython/export/82/geniuswebcore/dist/geniusweb-1.1.4.tar.gz"
    ],
    py_modules=['party'])
