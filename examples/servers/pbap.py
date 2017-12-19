#
# Released as open source by NCC Group Plc - http://www.nccgroup.com/
#
# Developed by Sultan Qasim Khan, Sultan.QasimKhan@nccgroup.trust
#
# http://www.github.com/nccgroup/nOBEX
#
# Released under GPLv3, a full copy of which can be found in COPYING.
#

import os, socket, sys
from nOBEX import headers, requests, responses, server

def gen_body_headers(data, csize=65500):
    """Generate a list of body headers (to encapsulate large data)"""
    hdrs = []
    i = 0
    while i < len(data):
        chunk = data[i:i+csize]
        if len(data) - i > csize:
            hdrs.append(headers.Body(chunk))
        else:
            hdrs.append(headers.End_Of_Body(chunk))
        i += csize
    return hdrs


class PBAPServer(server.Server):
    def __init__(self, directory, address=None):
        super(PBAPServer, self).__init__(address)
        self.directory = os.path.abspath(directory).rstrip(os.sep)
        self.cur_directory = self.directory

    def start_service(self, port=19):
        return super(PBAPServer, self).start_service("pbap", port)

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
                listing = open(path + "/listing.xml", 'rb')
            except IOError:
                sys.stderr.write("failed to open listing for %s\n" % path)
                self._reject(socket)
                return
            s = listing.read()
            listing.close()

            response = responses.Success()
            response_headers = [headers.Name(name), headers.Length(len(s))] + \
                    gen_body_headers(s, self._max_length() - 50)
            self.send_response(socket, response, response_headers)
        elif os.path.isfile(path):
            try:
                fd = open(path, 'rb')
            except IOError:
                sys.stderr.write("failed to open vcard %s" % path)
                self._reject(socket)
                return
            s = fd.read()
            fd.close()

            response = responses.Success()
            response_headers = [headers.Name(name), headers.Length(len(s))] + \
                    gen_body_headers(s, self._max_length() - 50)
            self.send_response(socket, response, response_headers)
        else:
            self._reject(socket)

    def put(self, socket, request):
        self.send_response(socket, responses.Bad_Request())

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
