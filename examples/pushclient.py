#!/usr/bin/env python3

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
from nOBEX.common import OBEXError
from clients.opp import OPPClient

def main(argv):
    if len(argv) != 3:
        sys.stderr.write("Usage: %s <device address> <file name>\n" % argv[0])
        return -1

    device_address = sys.argv[1]
    file_name = sys.argv[2]

    c = OPPClient(device_address)

    try:
        c.connect()
    except OBEXError:
        sys.stderr.write("Failed to connect.\n")
        traceback.print_exc()
        return -1

    c.put(file_name, open(file_name, 'rb').read())
    c.disconnect()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
