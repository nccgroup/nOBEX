#!/usr/bin/env python

import bluetooth, os, sys
from servers import map as map_

def run_server(device_address, port, directory):
    # Run the server in a function so that, if the server causes an exception
    # to be raised, the server instance will be deleted properly, giving us a
    # chance to create a new one and start the service again without getting
    # errors about the address still being in use.
    server = map_.MAPServer(device_address, directory)
    socket = server.start_service(port)

    try:
        server.serve(socket)
    except IOError:
        server.stop_service(socket)


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <directory> \n" % sys.argv[0])
        return 1

    device_address = ""
    port = bluetooth.PORT_ANY
    directory = sys.argv[1]

    if not os.path.exists(directory):
        os.mkdir(directory)

    while True:
        run_server(device_address, port, directory)

    return 0


if __name__ == "__main__":
    sys.exit(main())
