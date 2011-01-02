========
Overview
========

Grillo is a terminal based chat server and client. It was originally 
written as an `chat server entry`_ for the `Rossetta Code Project`_. 
It was then extended further into reusable threaded classes for the 
server and client, with command line options and some basic in-chat 
commands.

Grillo is named after the `Italian phone`_ of the same name, 
developed in 1965. They both share the common theme of being a very 
small communications device for their class, while being implemented 
with relatively basic technology.

Given that there are many richer and more powerful applications 
available for implementing the features Grillo provides, its best 
use at the least is to serve as a good example of how to do basic 
socket programming in Python, as well as a demonstrating some simple 
tricks for controlling threads.

Installation
============

Assuming you have `setuptools`_ installed, the easiest method is to 
install directly from pypi by running the following command::

    $ easy_install -U grillo

Otherwise you can download Grillo and install it directly from 
source::

    $ python setup.py install
    
Usage
=====
    
Once installed, the command ``grillo`` should be available which can 
be used for starting a server, client, or both at once (the default)::

    $ chat --bind host:port [--server-only|--client-only]

Note that the Grillo does not need to be installed in order to 
connect to a Grillo server, as the telnet command available on most 
modern systems can be used::

    $ telnet host port

.. _`chat server entry`: http://rosettacode.org/wiki/Chat_server#Python
.. _`Rosetta Code`: http://rosettacode.org/
.. _`Italian phone`: <http://en.wikipedia.org/wiki/Grillo_telephone>
.. _`setuptools`: http://pypi.python.org/pypi/setuptools
