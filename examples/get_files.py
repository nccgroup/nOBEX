#!/usr/bin/env python

import bluetooth, os, sys
from xml.etree import ElementTree
from PyOBEX import client, responses

if __name__ == "__main__":

    if len(sys.argv) != 3:
    
        sys.stderr.write("Usage: %s <device address> <directory>\n" % sys.argv[0])
        sys.exit(1)
    
    device_address = sys.argv[1]
    path = sys.argv[2]
    
    services = bluetooth.find_service(uuid="1106", address=device_address)
    if services:
        port = services[0]["port"]
    
    c = client.BrowserClient(device_address, port)
    
    response = c.connect()
    if not isinstance(response, responses.ConnectSuccess):
        sys.stderr.write("Failed to connect.\n")
        sys.exit(1)
    
    pieces = path.split("/")
    
    for piece in pieces:
    
        response = c.setpath(piece)
        if isinstance(response, responses.FailureResponse):
            sys.stderr.write("Failed to enter directory.\n")
            sys.exit(1)
    
    sys.stdout.write("Entered directory: %s\n" % path)
    
    response = c.listdir()
    
    if isinstance(response, responses.FailureResponse):
        sys.stderr.write("Failed to list directory.\n")
        sys.exit(1)
    
    headers, data = response
    tree = ElementTree.fromstring(data)
    for element in tree.findall("file"):
    
        name = element.attrib["name"]
        
        if os.path.exists(name):
            sys.stderr.write("File already exists: %s\n" % name)
            continue
        
        sys.stdout.write("Fetching file: %s\n" % name)
        
        response = c.get(name)
        
        if isinstance(response, responses.FailureResponse):
            sys.stderr.write("Failed to get file: %s\n" % name)
        else:
            sys.stdout.write("Writing file: %s\n" % name)
            headers, data = response
            try:
                open(name, "wb").write(data)
            except IOError:
                sys.stderr.write("Failed to write file: %s\n" % name)
    
    c.disconnect()
    sys.exit()
