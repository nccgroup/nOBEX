"""
bluez_helper.py - functions for creating sockets and using SDP

Copyright (C) 2017 Sultan Qasim Khan <Sultan.QasimKhan@nccgroup.trust>

This file is part of the nOBEX Python package.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import atexit, socket, subprocess, sys
import xml.etree.ElementTree as ET

def BluetoothSocket():
    return socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM,
            socket.BTPROTO_RFCOMM)

BDADDR_ANY = socket.BDADDR_ANY

# We are using the deprecated Bluez "Service" API instead of the new "Profile"
# API since the "Service" API works more the way I want it to.
# sdptool is the easy/lazy way to use this API without native code

class SDPException(Exception):
    pass

adv_services = set()

def stop_all():
    while len(adv_services):
        sn = adv_services.pop()
        stop_advertising(sn, False)

# clean up whatever services we started whenever we close the server
atexit.register(stop_all)

def advertise_service(name, channel):
    name = name.upper()
    if name in adv_services:
        raise SDPException("Can't re-advertise a service")

    val = subprocess.run(["sdptool", "add", "--channel=%i" % channel, name],
            stdout=subprocess.PIPE)
    if val.returncode != 0:
        raise SDPException("sdptool add returned %i" % val.returncode)
    adv_services.add(name)

def stop_advertising(name, pop=True):
    name = name.upper()
    if pop and not name in adv_services:
        return

    h, c = _search_record(name, "local")
    val = subprocess.run(["sdptool", "del", h], stdout=subprocess.PIPE)
    if val.returncode != 0:
        raise SDPException("sdptool del returned %i" % val.returncode)

    if pop:
        adv_services.remove(name)

def find_service(name, bdaddr):
    h, c = _search_record(name, bdaddr)
    return c

def _search_record(name, bdaddr):
    val = subprocess.run(
            ["sdptool", "search", "--xml", "--bdaddr=%s" % bdaddr, name],
            stdout=subprocess.PIPE)
    if val.returncode != 0:
        raise SDPException("sdptool search returned %i" % val.returncode)

    # Strip out first line that's not XML
    xml_str = b'\n'.join(val.stdout.splitlines()[1:])
    try:
        tree = ET.fromstring(xml_str)
    except ET.ParseError:
        raise SDPException("Service %s not found on %s" % (name, bdaddr))

    # this code is probably fragile
    handle = _find_attr(tree, "0x0000")[0].attrib["value"]
    channel = int(_find_attr(tree, "0x0004")[0][1][1].attrib["value"], 16)
    return handle, channel

def _find_attr(xml_tree, attr_id):
    for elem in xml_tree:
        if elem.tag == "attribute" and elem.attrib["id"] == attr_id:
            return elem
    raise SDPException("Attribute %s not found!" % attr_id)
