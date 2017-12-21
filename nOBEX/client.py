#!/usr/bin/env python

"""
client.py - Client classes for sending OBEX requests and handling responses.

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

import sys
from nOBEX.common import OBEX_Version, OBEXError
from nOBEX.bluez_helper import BluetoothSocket
from nOBEX import headers
from nOBEX import requests
from nOBEX import responses
from nOBEX.xml_helper import parse_xml

class Client(object):
    """Client

    client = Client(address, port)

    Provides common functionality for OBEX clients, including methods for
    connecting to and disconnecting from a server, sending and receiving
    headers, and methods for higher level actions such as "get", "put",
    "set path" and "abort".

    The address used is a standard six-field bluetooth address, and the port
    should correspond to the port providing the service you wish to access.
    """

    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.max_packet_length = 0xffff
        self.obex_version = OBEX_Version()
        self.response_handler = responses.ResponseHandler()

        self.socket = None
        self._external_socket = False
        self.connection_id = None

    def _send_headers(self, request, header_list, max_length):
        """Convenience method to add headers to a request and send one or
        more requests with those headers."""

        # Ensure that any Connection ID information is sent first.
        if self.connection_id:
            header_list.insert(0, self.connection_id)

        while header_list:
            if request.add_header(header_list[0], max_length):
                header_list.pop(0)
            else:
                self.socket.sendall(request.encode())

                if isinstance(request, requests.Connect):
                    response = self.response_handler.decode_connection(self.socket)
                else:
                    response = self.response_handler.decode(self.socket)

                if not isinstance(response, responses.Continue):
                    return response

                request.reset_headers()

        # Always send at least one request.
        if isinstance(request, requests.Get):
            # Turn the last Get request containing the headers into a
            # Get_Final request.
            request.code = requests.Get_Final.code

        self.socket.sendall(request.encode())

        if isinstance(request, requests.Connect):
            response = self.response_handler.decode_connection(self.socket)
        else:
            response = self.response_handler.decode(self.socket)

        return response

    def _collect_parts(self, header_list):
        body = []
        new_headers = []
        for header in header_list:
            if isinstance(header, headers.Body):
                body.append(header.data)
            elif isinstance(header, headers.End_Of_Body):
                body.append(header.data)
            else:
                new_headers.append(header)

        return new_headers, b"".join(body)

    def set_socket(self, socket):
        """set_socket(self, socket)

        Sets the socket to be used for communication to the socket specified.

        If socket is None, the client will create a socket for internal use
        when a connection is made. This is the default behaviour.

        This method must not be called once a connection has been opened.
        Only after an existing connection has been disconnected is it safe
        to set a new socket.
        """

        self.socket = socket

        if socket is None:
            self._external_socket = False
        else:
            self._external_socket = True

    def connect(self, header_list = ()):
        """connect(self, header_list = ())

        Sends a connection message to the server. Raises an exception
        with an error response if it fails. Typically, the response is
        either Success or a subclass of FailureResponse.

        Specific headers can be sent by passing a sequence as the
        header_list keyword argument.
        """

        if not self._external_socket:
            self.socket = BluetoothSocket()

        self.socket.connect((self.address, self.port))

        flags = 0
        data = (self.obex_version.to_byte(), flags, self.max_packet_length)

        max_length = self.max_packet_length
        request = requests.Connect(data)

        header_list = list(header_list)
        response = self._send_headers(request, header_list, max_length)

        if isinstance(response, responses.ConnectSuccess):
            self.remote_info = response
            for header in response.header_data:
                if isinstance(header, headers.Connection_ID):
                    # Recycle the Connection ID data to create a new header
                    # for future use.
                    self.connection_id = headers.Connection_ID(header.decode())
        elif not self._external_socket:
            self.socket.close()

        if not isinstance(response, responses.ConnectSuccess):
            raise OBEXError(response)

    def disconnect(self, header_list = ()):
        """disconnect(self, header_list = ())

        Sends a disconnection message to the server. Raises an exception
        with the response if it fails. Typically, the response is either
        Success or a subclass of FailureResponse.

        Specific headers can be sent by passing a sequence as the
        header_list keyword argument.

        If the socket was not supplied using set_socket(), it will be closed.
        """

        max_length = self.remote_info.max_packet_length
        request = requests.Disconnect()

        header_list = list(header_list)
        response = self._send_headers(request, header_list, max_length)

        if not self._external_socket:
            self.socket.close()

        self.connection_id = None

        if not isinstance(response, responses.Success):
            raise OBEXError(response)

    def put(self, name, file_data, header_list = ()):
        """put(self, name, file_data, header_list = ())

        Performs an OBEX PUT request to send a file with the given name,
        containing the file_data specified, to the server for storage in
        the current directory for the session.

        Additional headers can be sent by passing a sequence as the
        header_list keyword argument. These will be sent after the name and
        file length information associated with the name and file_data
        supplied.

        This function does not return anything. If a failure response is
        received, an OBEXError will be raised with the error response as
        its argument.
        """

        for response in self._put(name, file_data, header_list):
            if isinstance(response, responses.Continue) or \
                    isinstance(response, responses.Success):
                continue
            else:
                raise OBEXError(response)

    def _put(self, name, file_data, header_list = ()):
        header_list = [
                headers.Name(name),
                headers.Length(len(file_data))
                ] + list(header_list)

        max_length = self.remote_info.max_packet_length
        request = requests.Put()

        response = self._send_headers(request, header_list, max_length)
        yield response

        if not isinstance(response, responses.Continue):
            return

        # Send the file data.

        # The optimum size is the maximum packet length accepted by the
        # remote device minus three bytes for the header ID and length
        # minus three bytes for the request.
        optimum_size = max_length - 3 - 3

        i = 0
        while i < len(file_data):
            data = file_data[i:i+optimum_size]
            i += len(data)
            if i < len(file_data):
                request = requests.Put()
                request.add_header(headers.Body(data, False), max_length)
                self.socket.sendall(request.encode())

                response = self.response_handler.decode(self.socket)
                yield response

                if not isinstance(response, responses.Continue):
                    return

            else:
                request = requests.Put_Final()
                request.add_header(headers.End_Of_Body(data, False), max_length)
                self.socket.sendall(request.encode())

                response = self.response_handler.decode(self.socket)
                yield response

                if not isinstance(response, responses.Success):
                    return

    def get(self, name = None, header_list = ()):
        """get(self, name = None, header_list = (), callback = None)

        Performs an OBEX GET request to retrieve a file with the given name
        from the server's current directory for the session.

        Additional headers can be sent by passing a sequence as the
        header_list keyword argument. These will be sent after the name
        information.

        This method returns a tuple of the form (resp_header_list, body)
        where resp_header_list is a list of all non-body response headers,
        and body is a reconstructed byte string of the response body.
        """

        returned_headers = []

        for response in self._get(name, header_list):
            if isinstance(response, responses.Continue) or \
                    isinstance(response, responses.Success):
                # collect responses for processing at end
                returned_headers += response.header_data
            else:
                # Raise an exception for the failure
                raise OBEXError(response)

        # Finally, return the collected responses
        return self._collect_parts(returned_headers)

    def _get(self, name = None, header_list = ()):
        header_list = list(header_list)
        if name is not None:
            header_list = [headers.Name(name)] + header_list

        max_length = self.remote_info.max_packet_length
        request = requests.Get()

        response = self._send_headers(request, header_list, max_length)
        yield response

        if not (isinstance(response, responses.Continue) or
                isinstance(response, responses.Success)):
            return

        # Retrieve the file data.
        file_data = []
        request = requests.Get_Final()

        while isinstance(response, responses.Continue):
            self.socket.sendall(request.encode())
            response = self.response_handler.decode(self.socket)
            yield response

    def setpath(self, name = "", create_dir = False, to_parent = False, header_list = ()):
        """setpath(self, name = "", create_dir = False, to_parent = False, header_list = ())

        Requests a change to the server's current directory for the session
        to the directory with the specified name. Raises an exception with the
        response if the response was unexpected.

        This method is also used to perform other actions, such as navigating
        to the parent directory (set to_parent to True) and creating a new
        directory (set create_dir to True).

        Additional headers can be sent by passing a sequence as the
        header_list keyword argument. These will be sent after the name
        information.
        """

        header_list = list(header_list)
        if name is not None:
            header_list = [headers.Name(name)] + header_list

        max_length = self.remote_info.max_packet_length

        flags = 0
        if not create_dir:
            flags |= requests.Set_Path.DontCreateDir
        if to_parent:
            flags |= requests.Set_Path.NavigateToParent

        request = requests.Set_Path((flags, 0))

        response = self._send_headers(request, header_list, max_length)

        if not isinstance(response, responses.Success):
            raise OBEXError(response)

    def delete(self, name, header_list = ()):
        """delete(self, name, header_list = ())

        Requests the deletion of the file with the specified name from the
        current directory. Raises an OBEXError with the response if there
        is an error.
        """

        header_list = [
                headers.Name(name)
                ] + list(header_list)

        max_length = self.remote_info.max_packet_length
        request = requests.Put_Final()

        response = self._send_headers(request, header_list, max_length)

        if not isinstance(response, responses.Success):
            raise OBEXError(response)

    def abort(self, header_list = ()):
        """abort(self, header_list = ())

        Aborts the current session. Raises an OBEXError with the response
        if there is an error.

        Specific headers can be sent by passing a sequence as the
        header_list keyword argument.

        Warning: This method should only be called to terminate a running
        operation and is therefore only useful for developers who want to
        reimplementing existing operations.
        """

        header_list = list(header_list)
        max_length = self.remote_info.max_packet_length
        request = requests.Abort()

        response = self._send_headers(request, header_list, max_length)

        if not isinstance(response, responses.Success):
            raise OBEXError(response)

    def listdir(self, name = "", xml=False):
        """listdir(self, name = "")

        Requests information about the contents of the directory with the
        specified name relative to the current directory for the session.

        If the name is omitted or an empty string is supplied, the contents
        of the current directory are typically listed by the server.

        If successful, the server will provide an XML folder listing.
        If the xml argument is true, the XML listing will be returned directly.
        Else, this function will parse the XML and return a tuple of two lists,
        the first list being the folder names, and the second list being
        file names.
        """

        hdrs, data = self.get(name,
                header_list=[headers.Type(b"x-obex/folder-listing", False)])

        if xml:
            return data

        tree = parse_xml(data)
        folders = []
        files = []
        for e in tree:
            if e.tag == "folder":
                folders.append(e.attrib["name"])
            elif e.tag == "file":
                files.append(e.attrib["name"])
            elif e.tag == "parent-folder":
                pass # ignore it
            else:
                sys.stderr.write("Unknown listing element %s\n" % e.tag)

        return folders, files
