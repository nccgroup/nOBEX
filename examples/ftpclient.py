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

def _pjoin(paths):
    return "/".join(paths)

def dump_recurse(client, path, save_path=None):
    offset = len(path)
    if len(path) > 0:
        client.setpath(path[-1])

    # since some people may still be holding back progress with Python 2, I'll support
    # them for now and not use the Python 3 exist_ok option :(
    if save_path:
        try:
            os.makedirs(save_path + "/" + _pjoin(path))
        except OSError as e:
            pass

    dirs, files = client.listdir()

    # pull all the files in the current directory
    for f in files:
        print("\t"*offset + f)
        if save_path:
            _, data = client.get(f)
            fpath = _pjoin([save_path, _pjoin(path), f])
            with open(fpath, "wb") as fd:
                fd.write(data)

    # now recursively pull all the directories
    for d in dirs:
        print("\t"*offset + "> " + d)
        new_path = path + (d,)
        dump_recurse(client, new_path, save_path)

    if len(path) > 0:
        client.setpath(to_parent=True)

def main(argv):
    if not (2 <= len(argv) <= 3):
        sys.stderr.write("Usage: %s <device_address> [save_directory]\n" % argv[0])
        return -1

    device_address = argv[1]
    if len(argv) == 3:
        save_path = argv[2]
    else:
        save_path = None

    c = FTPClient(device_address)
    c.connect()

    dump_recurse(c, (), save_path)

    c.disconnect()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
