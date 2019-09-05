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

import atexit, socket, subprocess
import xml.etree.ElementTree as ET

def BluetoothSocket():
    return socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM,
            socket.BTPROTO_RFCOMM)

BDADDR_ANY = socket.BDADDR_ANY

class SDPException(Exception):
    pass

def get_available_port(address=BDADDR_ANY):
    for c in range(1, 31):
        s = BluetoothSocket()
        try:
            s.bind((address, c))
        except OSError:
            s.close()
        else:
            s.close()
            return c

    raise SDPException("All ports are in use!")

# We are using the deprecated Bluez "Service" API instead of the new "Profile"
# API since the "Service" API works more the way I want it to.
# sdptool is the easy/lazy way to use this API without native code

adv_services = set()

def stop_all():
    while len(adv_services):
        sn = adv_services.pop()
        stop_advertising(sn, False)

# clean up whatever services we started whenever we close the server
atexit.register(stop_all)

# Python versions older than 3.5 don't have subprocess.run
# This wrapper produces equivalent functionality on old versions
def subrun(args, stdout=None):
    if hasattr(subprocess, "run"):
        return subprocess.run(args, stdout=stdout)
    else:
        class SubrunResult(object):
            def __init__(self, retcode=0, output=None):
                self.returncode = retcode
                self.output = output

        if stdout:
            try:
                output = subprocess.check_output(args)
            except subprocess.CalledProcessError as e:
                return SubrunResult(e.returncode, e.output)
            else:
                return SubrunResult(0, output)
        else:
            ret = subprocess.call(args)
            return SubrunResult(ret)

def advertise_service(name, channel):
    name = name.upper()
    if name in adv_services:
        raise SDPException("Can't re-advertise a service")

    val = subrun(["sdptool", "add", "--channel=%i" % channel, name],
            stdout=subprocess.PIPE)
    if val.returncode != 0:
        raise SDPException("sdptool add returned %i" % val.returncode)
    adv_services.add(name)

def stop_advertising(name, pop=True):
    name = name.upper()
    if pop and not name in adv_services:
        return

    h, c = _search_record(name, "local")
    val = subrun(["sdptool", "del", h], stdout=subprocess.PIPE)
    if val.returncode != 0:
        raise SDPException("sdptool del returned %i" % val.returncode)

    if pop:
        adv_services.remove(name)

def find_service(name, bdaddr):
    h, c = _search_record(name, bdaddr)
    return c

def _search_record(name, bdaddr):
    val = subrun(
            ["sdptool", "search", "--xml", "--bdaddr=%s" % bdaddr, name],
            stdout=subprocess.PIPE)
    if val.returncode != 0:
        raise SDPException("sdptool search returned %i" % val.returncode)

    # Strip out lines that are not XML
    xml_lines = []
    for line in val.stdout.splitlines():
        if line.startswith(b'<') or line.startswith(b'\t'):
            xml_lines.append(line)
    xml_str = b''.join(xml_lines)

    serv_count = xml_str.count(b'<record>')
    if serv_count < 1:
        raise SDPException("Service %s not found on %s" % (name, bdaddr))
    elif serv_count > 1:
        # take just the first occurance
        xml_str = xml_str[:xml_str.index(b'</record>') + 9]

    try:
        tree = ET.fromstring(xml_str)
    except ET.ParseError:
        raise SDPException("Error parsing XML SDP record")

    # Workaround to HF AG (0x111f) also containing HF (0x111e) class
    if name.upper() == "HF":
        serv_classes = set()
        sc_attr = _find_attr(tree, "0x0001")[0]
        for c_elem in sc_attr.findall("uuid"):
            serv_classes.add(int(c_elem.attrib["value"], 16))
        if 0x111f in serv_classes:
            raise SDPException("HF on %s is HFAG" % bdaddr)

    # this code is probably fragile
    handle = _find_attr(tree, "0x0000")[0].attrib["value"]
    channel = int(_find_attr(tree, "0x0004")[0][1][1].attrib["value"], 16)
    return handle, channel

def _find_attr(xml_tree, attr_id):
    for elem in xml_tree:
        if elem.tag == "attribute" and elem.attrib["id"] == attr_id:
            return elem
    raise SDPException("Attribute %s not found!" % attr_id)

_bluez_version_verified = False

def _verify_bluez_version():
    val = subrun(["bluetoothctl", "-v"], stdout=subprocess.PIPE)
    if val.returncode != 0:
        raise SDPException("Failed to get bluez version! Error: %i" % val.returncode)
    verstr = val.stdout[14:-1]
    smajor, sminor = verstr.split(b'.')
    major = int(smajor)
    minor = int(sminor)
    if (major < 5) or (major == 5 and minor < 49):
        raise SDPException("bluez 5.49 or newer required! you have bluez %i.%i" % (major, minor))

    global _bluez_version_verified
    _bluez_version_verified = True

def list_paired_devices():
    if not _bluez_version_verified:
        _verify_bluez_version()

    devs = set()

    val = subrun(["bluetoothctl", "paired-devices"], stdout=subprocess.PIPE)
    if val.returncode != 0:
        raise SDPException("bluetoothctl paired-devices returned %i" % val.returncode)

    # Extract the MAC addresses
    for line in val.stdout.splitlines():
        fields = line.rstrip().split()
        devs.add(fields[1].decode('latin-1'))

    return devs
