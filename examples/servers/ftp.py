#
# Released as open source by NCC Group Plc - http://www.nccgroup.com/
#
# Developed by Sultan Qasim Khan, Sultan.QasimKhan@nccgroup.trust
#
# http://www.github.com/nccgroup/nOBEX
#
# Released under GPLv3, a full copy of which can be found in COPYING.
#

import os, stat, sys
from nOBEX import headers, requests, responses, server
from datetime import datetime

def unix2bluetime(unix_time):
    t = datetime.fromtimestamp(unix_time)
    return t.strftime("%Y%m%dT%H%M%S")

def gen_folder_listing(path):
    l = os.listdir(path)
    s = '<?xml version="1.0"?>\n<folder-listing>\n'

    for i in l:
        objpath = os.path.join(path, i)
        if os.path.isdir(objpath):
            args = (i, unix2bluetime(os.stat(objpath)[stat.ST_CTIME]))
            s += '  <folder name="%s" created="%s" />' % args
        else:
            args = (i, unix2bluetime(os.stat(objpath)[stat.ST_CTIME]),
                    os.stat(objpath)[stat.ST_SIZE])
            s += '  <file name="%s" created="%s" size="%s" />' % args

    s += "</folder-listing>\n"

    if sys.version_info.major < 3:
        s = unicode(s)

    return s

class FTPServer(server.Server):
    """OBEX File Transfer Profile Server"""

    def __init__(self, directory, address=None):
        super(FTPServer, self).__init__(address)
        self.directory = os.path.abspath(directory)
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

    def start_service(self, port=None):
        return super(FTPServer, self).start_service("ftp", port)

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
            if path.startswith(self.directory):
                s = gen_folder_listing(path)
                print(s)

                response = responses.Success()
                response_headers = [headers.Name(name),
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
