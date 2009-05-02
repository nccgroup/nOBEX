#! /usr/bin/env python

from distutils.core import setup

from PyOBEX import __version__

setup(
    name         = "PyOBEX",
    description  = "A package implementing aspects of the Object Exchange (OBEX) protocol.",
    author       = "David Boddie",
    author_email = "david@boddie.org.uk",
    url          = "http://www.boddie.org.uk/david/Projects/Python/PyOBEX/",
    version      = __version__,
    packages     = ["PyOBEX"]
    )
