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
from servers import opp

def run_server(device_address, port, directory):
    # Run the server in a function so that, if the server causes an exception
    # to be raised, the server instance will be deleted properly, giving us a
    # chance to create a new one and start the service again without getting
    # errors about the address still being in use.
    try:
        push_server = opp.OPPServer(device_address, directory)
        socket = push_server.start_service(port)
        push_server.serve(socket)
    except IOError:
        push_server.stop_service(socket)


def main():
    if len(sys.argv) != 4:
        sys.stderr.write("Usage: %s <device address> <port> <directory>\n" % sys.argv[0])
        sys.exit(1)

    device_address = sys.argv[1]
    port = int(sys.argv[2])
    directory = sys.argv[3]

    if not os.path.exists(directory):
        os.mkdir(directory)

    while True:
        run_server(device_address, port, directory)

    sys.exit()


if __name__ == "__main__":
    main()
