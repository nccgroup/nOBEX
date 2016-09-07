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

import bluetooth, os, struct, sys
from nOBEX import client, headers, responses

if __name__ == "__main__":

    if len(sys.argv) != 4:
    
        sys.stderr.write("Usage: %s <device address> <port> <file name>\n" % sys.argv[0])
        sys.exit(1)
    
    device_address = sys.argv[1]
    port = int(sys.argv[2])
    file_name = sys.argv[3]
    
    c = client.Client(device_address, port)
    r = c.connect(header_list=(headers.Target(b"OBEXObjectPush"),))
    
    if not isinstance(r, responses.ConnectSuccess):
        sys.stderr.write("Failed to connect.\n")
        sys.exit(1)
    
    c.put(file_name, open(file_name).read())
    c.disconnect()

    sys.exit()
