#!/usr/bin/env python

import bluetooth, os, sys
from servers import hfp, pbap
from servers import map as map_
from threading import Thread

def serve_hfp(beast_file=None):
    while True:
        server = hfp.HFPServer(beast_file)
        socket = server.start_service()
        try:
            server.serve(socket)
        except:
            server.stop_service(socket)


def serve_pbap(folder):
    while True:
        server = pbap.PBAPServer("", folder)
        socket = server.start_service()
        try:
            server.serve(socket)
        except:
            server.stop_service(socket)


def serve_map(folder):
    while True:
        server = map_.MAPServer("", folder)
        socket = server.start_service()
        try:
            server.serve(socket)
        except:
            server.stop_service(socket)


def main(argv):
    if ("-h" in argv) or ("--help" in argv):
        sys.stderr.write("Usage: %s [--hfp [config]] [--pbap pbap_root] [--map map_root]\n" % argv[0])
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
            return -1

    t = None

    if en_hfp:
        hfp_thread = Thread(target=serve_hfp, args=(hfp_conf,))
        hfp_thread.start()
        t = hfp_thread

    if en_map:
        map_thread = Thread(target=serve_map, args=(map_conf,))
        map_thread.start()
        t = map_thread

    if en_pbap:
        pbap_thread = Thread(target=serve_pbap, args=(pbap_conf,))
        pbap_thread.start()
        t = pbap_thread

    if t is not None:
        t.join()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
