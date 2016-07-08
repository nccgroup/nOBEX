#!/usr/bin/env python

import bluetooth, os, sys
from servers import hfp, pbap
from threading import Thread

def run_server(device_address, directory, en_hfp=False):
    # Run the server in a function so that, if the server causes an exception
    # to be raised, the server instance will be deleted properly, giving us a
    # chance to create a new one and start the service again without getting
    # errors about the address still being in use.
    server1 = pbap.PBAPServer(device_address, directory)
    socket = server1.start_service()

    # launch the dummy Hands Free Profile Server
    if en_hfp:
        server2 = hfp.HFPDummyServer(device_address)
        socket2 = server2.start_service()
        st = Thread(target=server2.serve, args=(socket2,))
        st.start()

    try:
        server1.serve(socket)
    except IOError:
        server1.stop_service(socket)


def main():
    if not (2 <= len(sys.argv) <= 3):
        sys.stderr.write("Usage: %s <directory> [hfp]\n" % sys.argv[0])
        sys.exit(1)

    en_hhp = False
    device_address = ""
    directory = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "hfp":
        en_hfp = True

    if not os.path.exists(directory):
        os.mkdir(directory)

    while True:
        run_server(device_address, directory, en_hfp)

    sys.exit()


if __name__ == "__main__":
    main()
