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

import os, struct, sys
from xml.etree import ElementTree
from xml.dom import minidom
from nOBEX import headers, responses
from nOBEX.common import OBEXError
from nOBEX.xml_helper import parse_xml
from clients.pbap import PBAPClient

def usage():
    sys.stderr.write("Usage: %s <device address> <dest directory> [SIM]\n" % sys.argv[0])

def dump_xml(element, file_name):
    rough_string = ElementTree.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_string = reparsed.toprettyxml()
    with open(file_name, 'w') as fd:
        fd.write('<?xml version="1.0"?>\n<!DOCTYPE vcard-listing SYSTEM "vcard-listing.dtd">\n')
        fd.write(pretty_string[23:]) # skip xml declaration

def get_file(c, src_path, dest_path, verbose=True, folder_name=None, book=False):
    if verbose:
        if folder_name is not None:
            print("Fetching %s/%s" % (folder_name, src_path))
        else:
            print("Fetching %s" % src_path)

    if book:
        mimetype = b'x-bt/phonebook'
    else:
        mimetype = b'x-bt/vcard'

    hdrs, card = c.get(src_path, header_list=[headers.Type(mimetype)])
    with open(dest_path, 'wb') as f:
        f.write(card)

def dump_dir(c, src_path, dest_path):
    src_path = src_path.strip("/")

    # since some people may still be holding back progress with Python 2, I'll support
    # them for now and not use the Python 3 exist_ok option :(
    try:
        os.makedirs(dest_path)
    except OSError as e:
        pass

    # Access the list of vcards in the directory
    hdrs, cards = c.get(src_path, header_list=[headers.Type(b'x-bt/vcard-listing')])

    if len(cards) == 0:
        print("WARNING: %s is empty, skipping", src_path)
        return

    # Parse the XML response to the previous request.
    # Extract a list of file names in the directory
    names = []
    root = parse_xml(cards)
    dump_xml(root, "/".join([dest_path, "listing.xml"]))
    for card in root.findall("card"):
        names.append(card.attrib["handle"])

    c.setpath(src_path)

    # get all the files
    for name in names:
        fname = "/".join([dest_path, name])
        try:
            get_file(c, name, fname, folder_name=src_path)
        except OBEXError as e:
            print("Failed to fetch", fname, e)

    # return to the root directory
    depth = len([f for f in src_path.split("/") if len(f)])
    for i in range(depth):
        c.setpath(to_parent=True)

def main(argv):
    if not 3 <= len(argv) <= 4:
        usage()
        return -1
    elif len(argv) == 4:
        if argv[3] == "SIM":
            # If the SIM command line option was given, look in the SIM1
            # directory. Maybe the SIM2 directory exists on dual-SIM phones.
            prefix = "SIM1/"
        else:
            usage()
            return -1
    else:
        prefix = ""

    device_address = argv[1]
    dest_dir = os.path.abspath(argv[2]) + "/"

    c = PBAPClient(device_address)
    c.connect()

    # dump the phone book and other folders
    dump_dir(c, prefix+"telecom/pb", dest_dir+prefix+"telecom/pb")
    dump_dir(c, prefix+"telecom/ich", dest_dir+prefix+"telecom/ich")
    dump_dir(c, prefix+"telecom/och", dest_dir+prefix+"telecom/och")
    dump_dir(c, prefix+"telecom/mch", dest_dir+prefix+"telecom/mch")
    dump_dir(c, prefix+"telecom/cch", dest_dir+prefix+"telecom/cch")

    # dump the combined vcards
    c.setpath(prefix + "telecom")
    get_file(c, "pb.vcf", dest_dir+prefix+"telecom/pb.vcf",
            folder_name=prefix+"telecom", book=True)
    get_file(c, "ich.vcf", dest_dir+prefix+"telecom/ich.vcf",
            folder_name=prefix+"telecom", book=True)
    get_file(c, "och.vcf", dest_dir+prefix+"telecom/och.vcf",
            folder_name=prefix+"telecom", book=True)
    get_file(c, "mch.vcf", dest_dir+prefix+"telecom/mch.vcf",
            folder_name=prefix+"telecom", book=True)
    get_file(c, "cch.vcf", dest_dir+prefix+"telecom/cch.vcf",
            folder_name=prefix+"telecom", book=True)

    c.disconnect()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
