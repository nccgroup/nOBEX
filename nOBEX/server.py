#!/usr/bin/env python

"""
server.py - Server classes for handling OBEX requests and sending responses.

Copyright (C) 2007 David Boddie <david@boddie.org.uk>

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

from nOBEX.common import OBEX_Version
from nOBEX import bluez_helper
from nOBEX import headers
from nOBEX import requests
from nOBEX import responses

class Server(object):
    def __init__(self, address=None):
        if address is None:
            address = bluez_helper.BDADDR_ANY

        self.address = address
        self.max_packet_length = 0xffff
        self.obex_version = OBEX_Version()
        self.request_handler = requests.RequestHandler()

    def start_service(self, name, port=None):
        if port is None:
            port = bluez_helper.get_available_port(self.address)

        socket = bluez_helper.BluetoothSocket()
        socket.bind((self.address, port))
        socket.listen(1)

        print("Starting server for %s on port %i" % socket.getsockname())
        bluez_helper.advertise_service(name, port)

        return socket

    def stop_service(self, name):
        bluez_helper.stop_advertising(name)

    def serve(self, socket):
        while True:
            connection, address = socket.accept()
            if not self.accept_connection(*address):
                connection.close()
                continue

            self.connected = True

            while self.connected:
                try:
                    request = self.request_handler.decode(connection)
                except ConnectionResetError:
                    print("Connection to %s on port %i reset by peer!" % address)
                    self.connected = False
                    break
                self.process_request(connection, request)

    def _max_length(self):
        if hasattr(self, "remote_info"):
            return self.remote_info.max_packet_length
        else:
            return self.max_packet_length

    def send_response(self, socket, response, header_list = []):
        # response encoding will handle making sure we split it
        # appropriately. we just need to send each chunk
        for h in header_list:
            response.add_header(h)
        chunks = response.encode(self._max_length(), True)
        while len(chunks) > 1:
            socket.sendall(chunks.pop(0))
            gf_request = self.request_handler.decode(socket)
            if not isinstance(gf_request, requests.Get_Final):
                raise IOError("didn't receive get final request for continuation")
        socket.sendall(chunks.pop(0))

    def _reject(self, socket):
        self.send_response(socket, responses.Forbidden())

    def accept_connection(self, address, port):
        return True

    def process_request(self, connection, request):
        """Processes the request from the connection.

        This method should be reimplemented in subclasses to add support for
        more request types.
        """

        #print(request)
        if isinstance(request, requests.Connect):
            self.connect(connection, request)
        elif isinstance(request, requests.Disconnect):
            self.disconnect(connection, request)
        elif isinstance(request, requests.Get):
            self.get(connection, request)
        elif isinstance(request, requests.Put):
            self.put(connection, request)
        elif isinstance(request, requests.Set_Path):
            self.set_path(connection, request)
        else:
            self._reject(connection)

    def connect(self, socket, request):
        if request.obex_version > self.obex_version:
            self._reject(socket)

        self.remote_info = request
        max_length = self.remote_info.max_packet_length

        flags = 0
        data = (self.obex_version.to_byte(), flags, max_length)

        response = responses.ConnectSuccess(data)
        self.send_response(socket, response)

    def disconnect(self, socket, request):
        response = responses.Success()
        self.send_response(socket, response)
        self.connected = False

    def get(self, socket, request):
        self._reject(socket)

    def put(self, socket, request):
        self._reject(socket)

    def set_path(self, socket, request):
        self._reject(socket)
