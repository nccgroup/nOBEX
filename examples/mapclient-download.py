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

import os, sys
from xml.etree import ElementTree
from nOBEX import headers
from nOBEX.common import OBEXError
from nOBEX.xml_helper import parse_xml
from clients.map import MAPClient

def dump_xml(element, file_name):
    fd = open(file_name, 'wb')
    fd.write(b'<?xml version="1.0" encoding="utf-8" standalone="yes" ?>\n')
    fd.write(ElementTree.tostring(element, 'utf-8'))
    fd.close()

def get_file(c, src_path, dest_path, verbose=True, folder_name=None):
    if verbose:
        if folder_name is not None:
            print("Fetching %s/%s" % (folder_name, src_path))
        else:
            print("Fetching %s" % src_path)

    # include attachments, use UTF-8 encoding
    req_hdrs = [headers.Type(b'x-bt/message'),
                headers.App_Parameters(b'\x0A\x01\x01\x14\x01\x01')]
    hdrs, card = c.get(src_path, header_list=req_hdrs)
    with open(dest_path, 'wb') as f:
        f.write(card)

def dump_dir(c, src_path, dest_path):
    src_path = src_path.strip("/")

    # Access the list of vcards in the directory
    hdrs, cards = c.get(src_path, header_list=[headers.Type(b'x-bt/MAP-msg-listing')])

    # folder doesn't exist, iPhone behaves this way
    if len(cards) == 0:
        return

    # since some people may still be holding back progress with Python 2, I'll support
    # them for now and not use the Python 3 exists_ok option :(
    try:
        os.makedirs(dest_path)
    except OSError:
        pass

    # Parse the XML response to the previous request.
    # Extract a list of file names in the directory
    names = []
    root = parse_xml(cards)
    dump_xml(root, "/".join([dest_path, "mlisting.xml"]))
    for card in root.findall("msg"):
        names.append(card.attrib["handle"])

    c.setpath(src_path)

    # get all the files
    for name in names:
        get_file(c, name, "/".join([dest_path, name]), folder_name=src_path)

    # return to the root directory
    depth = len([f for f in src_path.split("/") if len(f)])
    for i in range(depth):
        c.setpath(to_parent=True)

def main():
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: %s <device address> <dest directory>\n" % sys.argv[0])
        return 1

    device_address = sys.argv[1]
    dest_dir = os.path.abspath(sys.argv[2]) + "/"

    c = MAPClient(device_address)
    c.connect()
    c.setpath("telecom")
    c.setpath("msg")

    # dump every folder
    dirs, _ = c.listdir()
    for d in dirs:
        dump_dir(c, d, dest_dir + "telecom/msg/" + d)

    c.disconnect()
    return 0

if __name__ == "__main__":
    sys.exit(main())
