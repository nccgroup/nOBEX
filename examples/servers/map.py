import os, socket, sys
from PyOBEX import headers, requests, responses, server
from .ftp import gen_folder_listing

def gen_handle():
    """Generate a random 64 bit hex handle"""
    rb = os.urandom(8)
    if sys.version_info.major >= 3:
        return "".join(["%02X" % i for i in rb])
    else:
        return "".join(["%02X" % ord(c) for c in rb])


class MAPServer(server.MAPServer):
    def __init__(self, address, directory):
        super(MAPServer, self).__init__(address)
        self.directory = os.path.abspath(directory).rstrip(os.sep)
        self.cur_directory = self.directory

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

        if os.path.isdir(path) and mimetype == b'x-bt/MAP-msg-listing':
            try:
                listing = open(path + "/mlisting.xml", 'r')
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
        elif os.path.isdir(path) and mimetype == b'x-obex/folder-listing':
            s = gen_folder_listing(path)
            response = responses.Success()
            response_headers = [headers.Name(name),
                    headers.Length(len(s)),
                    headers.Body(s.encode("utf8"))]
            self.send_response(socket, response, response_headers)
        elif os.path.isfile(path) and mimetype == b'x-bt/message':
            try:
                fd = open(path, 'r')
            except IOError:
                sys.stderr.write("failed to open message %s" % path)
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
        body = b''
        mimetype = b''

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
                elif isinstance(header, headers.Type):
                    mimetype = header.decode().strip(b'\x00')
                    print("Type %s" % mimetype)

            if request.is_final():
                break

            # Ask for more data.
            self.send_response(socket, responses.Continue())

            # Get the next part of the data.
            request = self.request_handler.decode(socket)

        if mimetype == b'x-bt/MAP-event-report':
            print("MAP event", body)
        elif mimetype == b'x-bt/MAP-NotificationRegistration':
            print("MAP register for notifications")
        elif mimetype == b'x-bt/messageStatus':
            print("set message status")
        elif mimetype == b'x-bt/message':
            name = name.strip('\x00').encode(sys.getfilesystemencoding())
            name = os.path.split(name)[1]
            path = os.path.join(self.cur_directory, name)
            path = os.path.join(path, gen_handle())
            path = os.path.abspath(path)
            print("Push message", repr(path))
            open(path, "wb").write(body)
        elif mimetype == b'x-bt/MAP-messageUpdate':
            print("MAP inbox update requested")

        self.send_response(socket, responses.Success())

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
