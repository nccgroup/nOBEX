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

import os, signal, sys, traceback
from servers.hfp import HFPServer
from servers.map import MAPServer
from servers.pbap import PBAPServer
from servers.opp import OPPServer
from servers.ftp import FTPServer
from threading import Thread

def thread_serve(serv_class, arg):
    t = Thread(target=serve, args=(serv_class, arg), daemon=True)
    t.start()
    return t

def serve(serv_class, *args, **kwargs):
    server = serv_class(*args, **kwargs)
    socket = server.start_service()
    while True:
        try:
            server.serve(socket)
        except:
            traceback.print_exc()

def usage(argv):
    sys.stderr.write("Usage: %s " % argv[0])
    sys.stderr.write("[--hfp [config]] ")
    sys.stderr.write("[--pbap pbap_root] ")
    sys.stderr.write("[--map map_root] ")
    sys.stderr.write("[--ftp ftp_root] ")
    sys.stderr.write("[--opp opp_root]\n")

def signal_handler(signal, frame):
    print() # newline to move ^C onto its own line on display
    sys.exit(0)

def main(argv):
    if ("-h" in argv) or ("--help" in argv) or (len(argv) == 1):
        usage(argv)
        return -1

    en_hfp = False
    en_map = False
    en_pbap = False
    en_ftp = False
    en_opp = False
    hfp_conf = None
    map_conf = None
    pbap_conf = None
    ftp_conf = None
    opp_conf = None

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
        elif a == "--ftp":
            en_ftp = True
            ftp_conf = args.pop(0)
        elif a == "--opp":
            en_opp = True
            opp_conf = args.pop(0)
        else:
            sys.stderr.write("unknown parameter %s\n" % a)
            usage(argv)
            return -1

    signal.signal(signal.SIGINT, signal_handler)

    # obexd conflicts with our own OBEX servers
    os.system("killall obexd")

    threads = []

    if en_hfp:
        threads.append(thread_serve(HFPServer, hfp_conf))

    if en_map:
        threads.append(thread_serve(MAPServer, map_conf))

    if en_pbap:
        threads.append(thread_serve(PBAPServer, pbap_conf))

    if en_ftp:
        threads.append(thread_serve(FTPServer, ftp_conf))

    if en_opp:
        threads.append(thread_serve(OPPServer, opp_conf))

    # wait for completion (never)
    for t in threads:
        t.join()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
