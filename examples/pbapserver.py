#!/usr/bin/env python

import bluetooth, os, stat, struct, sys
from PyOBEX import headers, requests, responses, server
from threading import Thread

class PBAPServer(server.PBAPServer):
    def __init__(self, address, directory):
        server.PBAPServer.__init__(self, address)
        self.directory = os.path.abspath(directory).rstrip(os.sep)
        self.cur_directory = self.directory

    def process_request(self, socket, request):
        print (request, isinstance(request, requests.Get))
        if isinstance(request, requests.Get):
            self.get(socket, request)
        else:
            server.BrowserServer.process_request(self, socket, request)

    def get(self, socket, request):
        name = ''
        mimetype = b''

        for header in request.header_data:
            print(header)
            if isinstance(header, headers.Name):
                name = header.decode().strip('\x00')
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
            response_headers = [headers.Name(name),
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
            response_headers = [headers.Name(name),
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

        name = name.strip('\x00').encode(sys.getfilesystemencoding())
        name = os.path.split(name)[1]
        path = os.path.join(self.cur_directory, name)
        print("Writing", repr(path))

        open(path, "wb").write(body)

    def set_path(self, socket, request):
        if request.flags & requests.Set_Path.NavigateToParent:
            path = os.path.dirname(self.cur_directory)
        else:
            header = request.header_data[0]
            name = header.decode().strip('\x00')
            if len(name) == 0 and (
                    request.flags & requests.Set_Path.DontCreateDir):
                # see bluetooth PBAP spec section 5.3 PullvCardListing Function
                path = self.directory
            else:
                path = os.path.abspath(os.path.join(self.cur_directory, name))

        path = path.rstrip(os.sep)
        if not path.startswith(self.directory):
            self._reject(socket)
            return

        print("moving to %s" % path)
        self.cur_directory = path
        self.send_response(socket, responses.Success())


def run_server(device_address, port, directory, hfp=False):
    # Run the server in a function so that, if the server causes an exception
    # to be raised, the server instance will be deleted properly, giving us a
    # chance to create a new one and start the service again without getting
    # errors about the address still being in use.
    server_ = PBAPServer(device_address, directory)
    socket = server_.start_service(port)

    # launch the dummy Hands Free Profile Server
    if hfp:
        server2 = server.HFPDummyServer(device_address)
        socket2 = server2.start_service(port)
        st = Thread(target=server2.serve, args=(socket2,))
        st.start()

    try:
        server_.serve(socket)
    except IOError:
        server_.stop_service(socket)


if __name__ == "__main__":
    if not (2 <= len(sys.argv) <= 3):
        sys.stderr.write("Usage: %s <directory> [hfp]\n" % sys.argv[0])
        sys.exit(1)

    hfp = False
    device_address = ""
    port = bluetooth.PORT_ANY
    directory = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "hfp":
        hfp = True

    if not os.path.exists(directory):
        os.mkdir(directory)

    while True:
        run_server(device_address, port, directory, hfp)

    sys.exit()