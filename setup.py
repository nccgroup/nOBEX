#! /usr/bin/env python

#
# Released as open source by NCC Group Plc - http://www.nccgroup.com/
#
# Developed by Sultan Qasim Khan, Sultan.QasimKhan@nccgroup.trust
#
# http://www.github.com/nccgroup/nOBEX
#
# Released under GPLv3, a full copy of which can be found in COPYING.
#

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
