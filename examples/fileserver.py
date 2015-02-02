#!/usr/bin/env python

import bluetooth, os, stat, struct, sys
from PyOBEX import headers, requests, responses, server

class FileServer(server.BrowserServer):

    def __init__(self, address, directory):
    
        server.BrowserServer.__init__(self, address)
        self.directory = os.path.abspath(directory)
    
    def process_request(self, socket, request):
    
        print (request, isinstance(request, requests.Get))
        if isinstance(request, requests.Get):
            self.get(socket, request)
        else:
            server.BrowserServer.process_request(self, socket, request)
    
    def get(self, socket, request):
    
        name = ""
        type = ""
        
        for header in request.header_data:
        
            print(header)
            if isinstance(header, headers.Name):
                name = header.decode().strip(b"\x00")
                print("Receiving request for %s" % name)
            
            elif isinstance(header, headers.Type):
                type = header.decode().strip(b"\x00")
                print("Type %s" % type)
        
        path = os.path.abspath(os.path.join(self.directory, name))
        
        if os.path.isdir(path) or type == "x-obex/folder-listing":
        
            details = {}
            
            if path.startswith(self.directory):
            
                l = os.listdir(path)
                s = '<?xml version="1.0"?>\n<folder-listing>\n'
                for i in l:
                    objpath = os.path.join(path, i)
                    if os.path.isdir(objpath):
                        details[i] = (i, os.stat(objpath)[stat.ST_CTIME])
                        s += '  <folder name="%s" created="%s" />' % details[i]
                    else:
                        details[i] = (i, os.stat(objpath)[stat.ST_CTIME], os.stat(objpath)[stat.ST_SIZE])
                        s += '  <file name="%s" created="%s" size="%s" />' % details[i]
                
                s += "</folder-listing>\n"
                print(s)
                
                response = responses.Success()
                response_headers = [headers.Name(name.encode("utf8")),
                                    headers.Length(len(s)),
                                    headers.Body(s.encode("utf8"))]
                self.send_response(socket, response, response_headers)
            
            else:
                self._reject(socket)
        else:
            self._reject(socket)
    
    def put(self, socket, request):
    
        name = ""
        length = 0
        body = ""
        
        while True:
        
            for header in request.header_data:
            
                if isinstance(header, headers.Name):
                    name = header.decode()
                    print("Receiving", name)
                elif isinstance(header, headers.Length):
                    length = header.decode()
                    print("Length", length)
                elif isinstance(header, headers.Body):
                    body += header.decode()
                elif isinstance(header, headers.End_Of_Body):
                    body += header.decode()
            
            if request.is_final():
                break
            
            # Ask for more data.
            self.send_response(socket, responses.Continue())
            
            # Get the next part of the data.
            request = self.request_handler.decode(socket)
        
        self.send_response(socket, responses.Success())
        
        name = name.strip(b"\x00").encode(sys.getfilesystemencoding())
        name = os.path.split(name)[1]
        path = os.path.join(self.directory, name)
        print("Writing", repr(path))
        
        open(path, "wb").write(body)


def run_server(device_address, port, directory):

    # Run the server in a function so that, if the server causes an exception
    # to be raised, the server instance will be deleted properly, giving us a
    # chance to create a new one and start the service again without getting
    # errors about the address still being in use.
    try:
        server = FileServer(device_address, directory)
        socket = server.start_service(port)
        server.serve(socket)
    except IOError:
        server.stop_service(socket)


if __name__ == "__main__":

    if len(sys.argv) != 4:
    
        sys.stderr.write("Usage: %s <device address> <port> <directory>\n" % sys.argv[0])
        sys.exit(1)
    
    device_address = sys.argv[1]
    port = int(sys.argv[2])
    directory = sys.argv[3]
    
    if not os.path.exists(directory):
        os.mkdir(directory)
    
    while True:
        run_server(device_address, port, directory)
    
    sys.exit()
