import os
from nOBEX import headers, responses, server

class OPPServer(server.PushServer):
    """OBEX Object Push Profile Server"""

    def __init__(self, address, directory):
        super(OPPServer, self).__init__(address)
        self.directory = directory

    def put(self, socket, request):
        name = b""
        length = 0
        body = b""

        while True:
            for header in request.header_data:
                if isinstance(header, headers.Name):
                    name = header.decode()
                    print("Receiving %s" % name)
                elif isinstance(header, headers.Length):
                    length = header.decode()
                    print("Length %i" % length)
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

        name = name.strip("\x00")
        name = os.path.split(name)[1]
        path = os.path.join(self.directory, name)
        print("Writing %s" % repr(path))

        open(path, "wb").write(body)
