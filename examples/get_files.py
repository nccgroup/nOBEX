#!/usr/bin/env python

#
# Released as open source by NCC Group Plc - http://www.nccgroup.com/
#
# Developed by Sultan Qasim Khan, Sultan.QasimKhan@nccgroup.trust
#
# http://www.github.com/nccgroup/nOBEX
#
# Released under GPLv3, a full copy of which can be found in COPYING.
#

import os, sys, traceback
from xml.etree import ElementTree
from clients.ftp import FTPClient

def main(argv):
    if len(argv) != 3:
        sys.stderr.write("Usage: %s <device address> <directory>\n" % argv[0])
        return -1

    device_address = argv[1]
    path = argv[2]

    c = FTPClient(device_address)
    try:
        c.connect()
    except:
        sys.stderr.write("Failed to connect.\n")
        traceback.print_exc()
        return -1

    pieces = path.split("/")

    for piece in pieces:
        try:
            c.setpath(piece)
        except:
            sys.stderr.write("Failed to enter directory.\n")
            traceback.print_exc()
            return -1

    sys.stdout.write("Entered directory: %s\n" % path)

    try:
        data = c.listdir()
    except:
        sys.stderr.write("Failed to list directory.\n")
        traceback.print_exc()
        return -1

    tree = ElementTree.fromstring(data)
    for element in tree.findall("file"):
        name = element.attrib["name"]

        if os.path.exists(name):
            sys.stderr.write("File already exists: %s\n" % name)
            continue

        sys.stdout.write("Fetching file: %s\n" % name)

        headers, data = c.get(name)

        try:
            open(name, "wb").write(data)
        except IOError:
            sys.stderr.write("Failed to write file: %s\n" % name)

    c.disconnect()
    sys.exit()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
