#!/usr/bin/env python

# Note: This example lets you handle long connection delays by performing the
# connection in a thread. However, since the connection operation blocks, there
# is no way to terminate the operation from within the thread itself.

import bluetooth, sys, threading
from PyOBEX import client, responses
from PyOBEX.common import Socket

class CallerException(Exception):

    pass
    
class Caller:

    def __init__(self, timeout = 10):
    
        self.timeout = timeout
    
    def _call(self, fn, args):
    
        self.result = fn(*args)
        self.has_result = True
    
    def __call__(self, fn, args = ()):
    
        self.has_result = False
        thread = threading.Thread(target = self._call, args = (fn, args))
        thread.start()
        thread.join(self.timeout)
        if self.has_result:
            return self.result
        else:
            raise CallerException, "timed out"


if __name__ == "__main__":

    if len(sys.argv) != 3:
        sys.stderr.write("Usage: %s <host bluetooth address> <device bluetooth address>\n" % sys.argv[0])
        sys.exit(1)
    
    host_address = sys.argv[1]
    device_address = sys.argv[2]
    
    s = bluetooth.BluetoothSocket()
    s.bind((host_address, 0))
    
    services = bluetooth.find_service(uuid="E006", address=device_address)
    if not services:
        sys.stderr.write("No file transfer service on the device.\n")
        sys.exit(1)
    
    port = services[0]["port"]
    
    c = client.BrowserClient(device_address, port)
    c.set_socket(s)
    
    call = Caller()
    
    try:
        result = call(c.connect)
        if isinstance(result, responses.ConnectSuccess):
            print call(c.listdir)
            call(c.disconnect)
    
    except CallerException:
        sys.stderr.write("Connection timed out.\n")
    
    sys.exit()
