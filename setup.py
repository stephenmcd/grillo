
from setuptools import setup, find_packages

from chat import __version__

setup(

    name="chat",
    version=__version__,
    author="Stephen McDonald",
    author_email="stephen.mc@gmail.com",
    description="Terminal based chat server and client.",
    long_description=open("README.rst").read(),
    license="BSD",
    url="http://jupo.org/",
    zip_safe=False,
    py_modules=["chat"],

    entry_points="""
        [console_scripts]
        chat=chat:main
    """,

    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]

)
