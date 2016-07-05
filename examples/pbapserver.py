#!/usr/bin/env python

import bluetooth, os, stat, struct, sys
from PyOBEX import headers, requests, responses, server

class PBAPServer(server.PBAPServer):
    def __init__(self, address, directory):
        server.PBAPServer.__init__(self, address)
        self.directory = os.path.abspath(directory)
        self.cur_directory = self.directory

    def process_request(self, socket, request):
        print (request, isinstance(request, requests.Get))
        if isinstance(request, requests.Get):
            self.get(socket, request)
        else:
            server.BrowserServer.process_request(self, socket, request)

    def get(self, socket, request):
        name = b''
        mimetype = b''

        for header in request.header_data:
            print(header)
            if isinstance(header, headers.Name):
                name = header.decode().strip(b'\x00')
                print("Receiving request for %s" % name)

            elif isinstance(header, headers.Type):
                mimetype = header.decode().strip(b'\x00')
                print("Type %s" % mimetype)

        path = os.path.abspath(os.path.join(self.cur_directory, name))
        if not path.startswith(self.directory):
            self._reject(socket)
            return

        if os.path.isdir(path) or mimetype == b'x-bt/vcard-listing':
            try:
                listing = open(path + "/listing.xml", 'r')
            except IOError:
                sys.stderr.write("failed to open listing for %s" % path)
                self._reject(socket)
                return
            s = listing.read()
            listing.close()

            response = responses.Success()
            response_headers = [headers.Name(name.encode("utf8")),
                    headers.Length(len(s)),
                    headers.Body(s.encode("utf8"))]
            self.send_response(socket, response, response_headers)
        elif os.path.isfile(path):
            try:
                fd = open(path, 'r')
            except IOError:
                sys.stderr.write("failed to open vcard %s" % path)
                self._reject(socket)
                return
            s = fd.read()
            fd.close()

            response = responses.Success()
            response_headers = [headers.Name(name.encode("utf8")),
                    headers.Length(len(s)),
                    headers.Body(s.encode("utf8"))]
            self.send_response(socket, response, response_headers)
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

        name = name.strip(b'\x00').encode(sys.getfilesystemencoding())
        name = os.path.split(name)[1]
        path = os.path.join(self.cur_directory, name)
        print("Writing", repr(path))

        open(path, "wb").write(body)

    def set_path(self, socket, request):
        header = request.header_data[0]
        name = header.decode().strip(b'\x00')
        path = os.path.abspath(os.path.join(self.cur_directory, name))
        if not path.startswith(self.directory):
            self._reject(socket)
            return
        print("moving to %s" % path)
        self.cur_directory = path


def run_server(device_address, port, directory):
    # Run the server in a function so that, if the server causes an exception
    # to be raised, the server instance will be deleted properly, giving us a
    # chance to create a new one and start the service again without getting
    # errors about the address still being in use.
    try:
        server = PBAPServer(device_address, directory)
        socket = server.start_service(port)
        server.serve(socket)
    except IOError:
        server.stop_service(socket)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <directory>\n" % sys.argv[0])
        sys.exit(1)

    device_address = ""
    port = bluetooth.PORT_ANY
    directory = sys.argv[1]

    if not os.path.exists(directory):
        os.mkdir(directory)

    while True:
        run_server(device_address, port, directory)

    sys.exit()
