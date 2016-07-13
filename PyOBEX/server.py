#!/usr/bin/env python

"""
server.py - Server classes for handling OBEX requests and sending responses.

Copyright (C) 2007 David Boddie <david@boddie.org.uk>

This file is part of the PyOBEX Python package.

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

from bluetooth import BluetoothSocket, RFCOMM, OBEX_FILETRANS_CLASS, \
        OBEX_FILETRANS_PROFILE, OBEX_OBJPUSH_CLASS, OBEX_OBJPUSH_PROFILE, \
        OBEX_UUID, PUBLIC_BROWSE_GROUP, RFCOMM_UUID, advertise_service, \
        stop_advertising

from PyOBEX.common import OBEX_Version
from PyOBEX import headers
from PyOBEX import requests
from PyOBEX import responses

OBEX_PBAP_CLASS = "112F"
OBEX_PBAP_PROFILE = ("1130", 0x0101)
OBEX_MAP_CLASS = "1132"
OBEX_MAP_PROFILE = ("1134", 0x0102)

class Server:
    def __init__(self, address = ""):
        self.address = address
        self.max_packet_length = 0xffff
        self.obex_version = OBEX_Version()
        self.request_handler = requests.RequestHandler()

    def start_service(self, port, name, uuid, service_classes, service_profiles,
            provider, description, protocols):
        socket = BluetoothSocket(RFCOMM)
        socket.bind((self.address, port))
        socket.listen(1)

        advertise_service(
                socket, name, uuid, service_classes, service_profiles,
                provider, description, protocols
                )

        print("Starting server for %s on port %i" % socket.getsockname())
        #self.serve(socket)
        return socket

    def stop_service(self, socket):
        stop_advertising(socket)

    def serve(self, socket):
        while True:
            connection, address = socket.accept()
            if not self.accept_connection(*address):
                connection.close()
                continue

            self.connected = True

            while self.connected:
                request = self.request_handler.decode(connection)
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

class BrowserServer(Server):
    def start_service(self, port = None):
        if port is None:
            port = get_available_port(RFCOMM)

        name = "OBEX File Transfer"
        # "E006" also appears to work if used as a service ID. However, 1106
        # is the official profile number:
        # (https://www.bluetooth.org/en-us/specification/assigned-numbers/service-discovery)
        uuid = "F9EC7BC4-953C-11d2-984E-525400DC9E09"
        service_classes = [OBEX_FILETRANS_CLASS]
        service_profiles = [OBEX_FILETRANS_PROFILE]
        provider = ""
        description = "File transfer"
        protocols = [OBEX_UUID]

        return Server.start_service(self, port, name, uuid, service_classes,
                service_profiles, provider, description, protocols)

class PushServer(Server):
    def start_service(self, port = None):
        if port is None:
            port = get_available_port(RFCOMM)

        name = "OBEX Object Push"
        uuid = PUBLIC_BROWSE_GROUP
        service_classes = [OBEX_OBJPUSH_CLASS]
        service_profiles = [OBEX_OBJPUSH_PROFILE]
        provider = ""
        description = "File transfer"
        protocols = [RFCOMM_UUID, OBEX_UUID]

        return Server.start_service(self, port, name, uuid, service_classes,
                service_profiles, provider, description, protocols)

class PBAPServer(Server):
    def start_service(self, port = 19):
        name = "Phonebook Access Server"
        uuid = "796135f0-f0c5-11d8-0966-0800200c9a66"
        service_classes = [OBEX_PBAP_CLASS]
        service_profiles = [OBEX_PBAP_PROFILE]
        provider = ""
        description = ""
        protocols = [RFCOMM_UUID, OBEX_UUID]

        return Server.start_service(self, port, name, uuid, service_classes,
                service_profiles, provider, description, protocols)

class MAPServer(Server):
    def start_service(self, port = 4):
        name = "SMS/MMS"
        uuid = "bb582b40-420c-11db-b0de-0800200c9a66"
        service_classes = [OBEX_MAP_CLASS]
        service_profiles = [OBEX_MAP_PROFILE]
        provider = ""
        description = ""
        protocols = [RFCOMM_UUID, OBEX_UUID]

        return Server.start_service(self, port, name, uuid, service_classes,
                service_profiles, provider, description, protocols)
