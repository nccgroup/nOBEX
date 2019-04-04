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

"""
This script acts as an HFP HF (ie. it emulates a car head unit).
Your phone (HFAG) will connect to the RFCOMM socket server this script runs.
You can use this script to experiment with sending AT commands to your HFAG.

Be aware that most HFAG devices expect you to send a series of AT commands
before they allow you to use the modem to do useful things. The sequence
of AT commands below should work to initialize most HFAGs properly:

AT+BRSF=39
AT+CIND=?
AT+CIND?
AT+CMER=3,0,0,1
AT+CHLD=?
AT+CCWA=1
AT+CLIP=1
AT+NREC=0
"""

from nOBEX import bluez_helper
from threading import Thread
from sys import stdout

def print_loop(conn):
    while(True):
        b = chr(conn.recv(1)[0])
        stdout.write(b)

def main():
    port = bluez_helper.get_available_port()
    socket = bluez_helper.BluetoothSocket()
    socket.bind((bluez_helper.BDADDR_ANY, port))
    socket.listen(1)
    bluez_helper.advertise_service('hf', port)

    print("Waiting for connection on port", port)
    connection, address = socket.accept()
    print("Got connection:", address)

    t = Thread(target=print_loop, args=(connection,), daemon=True)
    t.start()

    while True:
        c = input().encode('latin-1') + b'\r\n'
        connection.send(c)

if __name__ == "__main__":
    main()
