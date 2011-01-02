========
Overview
========

A terminal based chat server and client.

Installation
============

Assuming you have `setuptools`_ installed, the easiest method is to install 
directly from pypi by running the following command::

    $ easy_install -U chat

Otherwise you can download Mezzanine and install it directly from source::

    $ python setup.py install
    
Once installed, the command ``chat`` should be available which can be used 
for starting a server, client, or both at once::

    $ chat -b host:port [-s|-c]

.. _`setuptools`: http://pypi.python.org/pypi/setuptools
