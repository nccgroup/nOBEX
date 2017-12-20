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

import sys, traceback
from xml.etree import ElementTree
from nOBEX import headers
from nOBEX.common import OBEXError
from clients.pbap import PBAPClient

def main(argv):
    if not 2 <= len(argv) <= 3:
        sys.stderr.write("Usage: %s <device address> [SIM]\n" % argv[0])
        return -1
    elif len(argv) == 3:
        if argv[2] == "SIM":
            # If the SIM command line option was given, look in the SIM1
            # directory. Maybe the SIM2 directory exists on dual-SIM phones.
            prefix = "SIM1/"
        else:
            sys.stderr.write("Usage: %s <device address> [SIM]\n" % argv[0])
            return -1
    else:
        prefix = ""

    device_address = argv[1]

    c = PBAPClient(device_address)
    try:
        c.connect()
    except OBEXError:
        sys.stderr.write("Failed to connect to phone.\n")
        traceback.print_exc()
        return -1

    # Access the list of vcards in the phone's internal phone book.
    hdrs, cards = c.get(prefix+"telecom/pb", header_list=[headers.Type(b"x-bt/vcard-listing")])

    # Parse the XML response to the previous request.
    root = ElementTree.fromstring(cards)

    print("\nAvailable cards in %stelecom/pb\n" % prefix)

    # Examine each XML element, storing the file names we find in a list, and
    # printing out the file names and their corresponding contact names.
    names = []
    for card in root.findall("card"):
        print("%s: %s" % (card.attrib["handle"], card.attrib["name"]))
        names.append(card.attrib["handle"])

    print("\nCards in %stelecom/pb\n" % prefix)

    # Request all the file names obtained earlier.
    c.setpath(prefix + "telecom/pb")

    for name in names:
        hdrs, card = c.get(name, header_list=[headers.Type(b"x-bt/vcard")])
        print(card)

    # Return to the root directory.
    c.setpath(to_parent = True)
    c.setpath(to_parent = True)
    if prefix:
        c.setpath(to_parent = True)

    print("\nThe phonebook in %stelecom/pb as one vcard\n" % prefix)

    hdrs, phonebook = c.get(prefix + "telecom/pb.vcf",
                            header_list=[headers.Type(b"x-bt/phonebook")])
    print(phonebook)

    c.disconnect()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
