#!/usr/bin/env python

from servers import hfp

def run_server(device_address):
    # Run the server in a function so that, if the server causes an exception
    # to be raised, the server instance will be deleted properly, giving us a
    # chance to create a new one and start the service again without getting
    # errors about the address still being in use.
    server = hfp.HFPServer(device_address)
    socket = server.start_service()

    try:
        server.serve(socket)
    except IOError:
        server.stop_service(socket)


if __name__ == "__main__":
    while True:
        run_server("")
