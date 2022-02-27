# flake8: noqa
from setuptools import setup

setup(
    name='ponpokoclone',
    version='1.0.0',
    description='''Port of the Pon Poko Agent to Python''',
    url='https://tracinsy.ewi.tudelft.nl/pubtrac/GeniusWeb',
    author='V.D. van de Beek',
    packages=['ponpoko'],
    install_requires=[
        "geniusweb@https://tracinsy.ewi.tudelft.nl/pubtrac/GeniusWebPython/export/82/geniuswebcore/dist/geniusweb-1.1.4.tar.gz"
    ],
    py_modules=['party'])
