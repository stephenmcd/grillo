
from setuptools import setup, find_packages

from grillo import __version__


setup(

    name="chat",
    version=__version__,
    author="Stephen McDonald",
    author_email="stephen.mc@gmail.com",
    description="A terminal based chat server and client.",
    long_description=open("README.rst").read(),
    license="BSD",
    url="http://github.com/stephenmcd/grillo",
    zip_safe=False,
    py_modules=["chat"],

    entry_points="""
        [console_scripts]
        grillo=grillo:main
    """,

    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Communications :: Chat",
        "Topic :: Terminals :: Telnet",
    ]

)
