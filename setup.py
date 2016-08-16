#! /usr/bin/env python

from distutils.core import setup

from nOBEX import __version__

setup(
    name         = "nOBEX",
    description  = "A package implementing aspects of the Object Exchange (OBEX) protocol.",
    author       = "David Boddie an Sultan Khan",
    author_email = "Sultan.QasimKhan@nccgroup.trust",
    url          = "https://github.com/nccgroup/nOBEX",
    version      = __version__,
    packages     = ["nOBEX"]
    )
