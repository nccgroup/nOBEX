#!/usr/bin/env python

import bluetooth, os, struct, sys
from xml.etree import ElementTree
from PyOBEX import client, headers, responses

if __name__ == "__main__":

    if not 2 <= len(sys.argv) <= 3:
        sys.stderr.write("Usage: %s <device address> [SIM]\n" % sys.argv[0])
        sys.exit(1)
    
    elif len(sys.argv) == 3:
        if sys.argv[2] == "SIM":
            # If the SIM command line option was given, look in the SIM1
            # directory. Maybe the SIM2 directory exists on dual-SIM phones.
            prefix = "SIM1/"
        else:
            sys.stderr.write("Usage: %s <device address> [SIM]\n" % sys.argv[0])
            sys.exit(1)
    else:
        prefix = ""
    
    device_address = sys.argv[1]
    
    d = bluetooth.find_service(address=device_address, uuid="1130")
    if not d:
        sys.stderr.write("No Phonebook service found.\n")
        sys.exit(1)
    
    port = d[0]["port"]
    
    # Use the generic Client class to connect to the phone.
    c = client.Client(device_address, port)
    uuid = b"\x79\x61\x35\xf0\xf0\xc5\x11\xd8\x09\x66\x08\x00\x20\x0c\x9a\x66"
    result = c.connect(header_list=[headers.Target(uuid)])
    
    if not isinstance(result, responses.ConnectSuccess):
        sys.stderr.write("Failed to connect to phone.\n")
        sys.exit(1)
    
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

    sys.exit()
