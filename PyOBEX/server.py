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

from bluetooth import BluetoothSocket, RFCOMM

from common import OBEX_Version
import headers
import requests
import responses


class Server:

    def __init__(self, address = ""):
    
        self.address = address
        self.max_packet_length = 0xffff
        self.obex_version = OBEX_Version()
        self.request_handler = requests.RequestHandler()
        self.methods = {
            requests.Connect: self.connect,
            requests.Disconnect: self.disconnect
            }
    
    def start_service(self, port, name, uuid, service_classes, service_profiles,
                      provider, description, protocols):
    
        socket = BluetoothSocket(RFCOMM)
        socket.bind((self.address, port))
        socket.listen(1)
        
        advertise_service(
            socket, name, uuid, service_classes, service_profiles,
            provider, description, protocols
            )
        
        print "Starting server for %s on port %i" % socket.getsockname()
        #self.serve(socket)
        return socket
    
    def stop_service(self, socket):
    
        stop_advertising(socket)
    
    def serve(self, socket):
    
        while True:
        
            connection, address = socket.accept()
            request = self.request_handler.decode(connection)
            
            try:
                self.methods[request.__class__](connection, request)
            
            except KeyError:
                self.reject(connection)
    
    def _send_headers(self, socket, response, header_list, max_length):
    
        while header_list:
        
            if response.add_header(header_list[0], max_length):
                header_list.pop(0)
            else:
                socket.sendall(response.encode())
                response.reset_headers()
        
        # Always send at least one request.
        socket.sendall(response.encode())
    
    def _reject(self, socket):
    
        if hasattr(self, remote_info):
            max_length = self.remote_info.max_packet_length
        else:
            max_length = self.max_packet_length
        
        response = responses.Forbidden()
        self._send_headers(response, [], max_length)
    
    def connect(self, socket, request):
    
        if request.obex_version > self.obex_version:
            self._reject(socket)
        
        self.remote_info = request
        max_length = self.remote_info.max_packet_length
        
        flags = 0
        data = (self.obex_version.to_byte(), flags, max_length)
        
        response = responses.ConnectSuccess(data)
        header_list = []
        self._send_headers(socket, response, header_list, max_length)
    
    def disconnect(self, socket, request):
    
        max_length = self.remote_info.max_packet_length
        
        response = responses.Success(data)
        header_list = []
        self._send_headers(socket, response, header_list, max_length)

class BrowserServer(Server):

    def start_service(self, port = None):
    
        if port is None:
            port = get_available_port(RFCOMM)
        
        name = "OBEX File Transfer"
        uuid = "F9EC7BC4-953C-11d2-984E-525400DC9E09" # "E006" also appears to work
        service_classes = [OBEX_FILETRANS_CLASS]
        service_profiles = [OBEX_FILETRANS_PROFILE]
        provider = ""
        description = "File transfer"
        protocols = [OBEX_UUID]
        
        return Server.start_service(
            self, port, name, uuid, service_classes, service_profiles,
            provider, description, protocols
            )

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
        
        return Server.start_service(
            self, port, name, uuid, service_classes, service_profiles,
            provider, description, protocols
            )
