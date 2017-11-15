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

import bluetooth, os, signal, sys, traceback
from servers import hfp, pbap
from servers import map as map_
from threading import Thread

def serve_hfp(beast_file=None):
    server = hfp.HFPServer(beast_file)
    socket = server.start_service()
    while True:
        try:
            server.serve(socket)
        except:
            traceback.print_exc()


def serve_pbap(folder):
    server = pbap.PBAPServer("", folder)
    socket = server.start_service()
    while True:
        try:
            server.serve(socket)
        except:
            traceback.print_exc()


def serve_map(folder):
    server = map_.MAPServer("", folder)
    socket = server.start_service()
    while True:
        try:
            server.serve(socket)
        except:
            traceback.print_exc()

def usage(argv):
    sys.stderr.write("Usage: %s [--hfp [config]] [--pbap pbap_root] [--map map_root]\n" % argv[0])

def signal_handler(signal, frame):
    sys.exit(0)

def main(argv):
    if ("-h" in argv) or ("--help" in argv) or (len(argv) == 1):
        usage(argv)
        return -1

    en_hfp = False
    en_map = False
    en_pbap = False
    hfp_conf = None
    map_conf = None
    pbap_conf = None

    args = argv[1:]
    while len(args):
        a = args.pop(0)
        if a == "--hfp":
            en_hfp = True
            if len(args) and not args[0].startswith("--"):
                hfp_conf = args.pop(0)
        elif a == "--map":
            en_map = True
            map_conf = args.pop(0)
        elif a == "--pbap":
            en_pbap = True
            pbap_conf = args.pop(0)
        else:
            sys.stderr.write("unknown parameter %s\n" % a)
            usage(argv)
            return -1

    signal.signal(signal.SIGINT, signal_handler)

    # obexd conflicts with our own OBEX servers
    if en_map or en_pbap:
        os.system("killall obexd")

    if en_hfp:
        hfp_thread = Thread(target=serve_hfp, args=(hfp_conf,))
        hfp_thread.start()

    if en_map:
        map_thread = Thread(target=serve_map, args=(map_conf,))
        map_thread.start()

    if en_pbap:
        pbap_thread = Thread(target=serve_pbap, args=(pbap_conf,))
        pbap_thread.start()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
