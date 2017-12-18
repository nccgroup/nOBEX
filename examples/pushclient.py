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

import bluetooth, os, struct, sys, traceback
from nOBEX import client, headers, responses
from nOBEX.common import OBEXError

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: %s <device address> <file name>\n" % sys.argv[0])
        sys.exit(1)

    device_address = sys.argv[1]
    file_name = sys.argv[2]

    d = bluetooth.find_service(address=device_address, uuid="1105")
    if not d:
        sys.stderr.write("No Object Push service found.\n")
        sys.exit(1)

    port = d[0]["port"]

    c = client.Client(device_address, port)
    try:
        c.connect()
    except OBEXError:
        sys.stderr.write("Failed to connect.\n")
        traceback.print_exc()
        sys.exit(1)

    c.put(file_name, open(file_name, 'rb').read())
    c.disconnect()

    sys.exit()
