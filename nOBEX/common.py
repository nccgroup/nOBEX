#!/usr/bin/env python

"""
common.py - Classes providing common facilities for other modules.

Copyright (C) 2007 David Boddie <david@boddie.org.uk>
Copyright (C) 2017 Sultan Qasim Khan <Sultan.QasimKhan@nccgroup.trust>

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

import socket, struct, sys
from nOBEX import headers

class OBEXError(Exception):
    pass

class OBEX_Version:
    major = 1
    minor = 0

    def to_byte(self):
        return (self.major & 0x0f) << 4 | (self.minor & 0xf)

    def from_byte(self, byte):
        self.major = (byte >> 4) & 0x0f
        self.minor = byte & 0x0f
        return self

    def __gt__(self, other):
        return (self.major, self.minor) > (other.major, other.minor)


class Message(object):
    format = ">BH"

    def __init__(self, data = (), header_data = ()):
        self.data = data
        self.header_data = list(header_data)
        self.minimum_length = self.length(Message.format)

    def length(self, format):
        return format.count("B") + format.count("H") * 2

    def __repr__(self):
        return "%s(data=%s)" % (type(self).__name__, repr(self.data))

    def read_data(self, data):
        # Extract the header data from the complete data.
        header_data = data[self.minimum_length:]
        self.read_headers(header_data)

    def read_headers(self, header_data):
        i = 0
        header_list = []
        while i < len(header_data):
            # Read header ID and data type.
            ID = struct.unpack(">B", header_data[i:i+1])[0]
            ID_type = ID & 0xc0
            if ID_type == 0x00:
                # text
                length = struct.unpack(">H", header_data[i+1:i+3])[0] - 3
                data = header_data[i+3:i+3+length]
                i += 3 + length
            elif ID_type == 0x40:
                # bytes
                length = struct.unpack(">H", header_data[i+1:i+3])[0] - 3
                data = header_data[i+3:i+3+length]
                i += 3 + length
            elif ID_type == 0x80:
                # 1 byte
                data = header_data[i+1]
                i += 2
            elif ID_type == 0xc0:
                # 4 bytes
                data = header_data[i+1:i+5]
                i += 5

            HeaderClass = headers.header_dict.get(ID, headers.Header)
            header_list.append(HeaderClass(data, encoded = True))

        self.header_data = header_list

    def add_header(self, header, max_length=0xFFFFFFFF):
        if self.minimum_length + len(header.data) > max_length:
            return False
        else:
            self.header_data.append(header)
            return True

    def reset_headers(self):
        self.header_data = []

    def encode(self, csize=65535, multi_part=False):
        # message format is >BH then data
        # let's first encode the data, then chunk it up
        # headers must not be split across packets
        data_chunks = [struct.pack(self.format, *self.data)]
        data_chunks.extend(map(lambda h: h.data, self.header_data))

        total_data = sum([len(c) for c in data_chunks])
        bytes_chunked = 0
        last_chunk = False

        assert(multi_part or total_data < csize)

        msg_chunks = []

        # leave 3 bytes for message headers
        while (bytes_chunked < total_data) or (len(msg_chunks) == 0):
            assert(len(data_chunks[0]) < csize - 3)
            chunk = b''
            while len(data_chunks) and (len(chunk) + len(data_chunks[0]) < csize - 3):
                bytes_chunked += len(data_chunks[0])
                chunk += data_chunks.pop(0)
                if len(data_chunks) == 0: last_chunk = True
                if last_chunk: break

            if last_chunk: code = self.code
            else: code = 0x90 # continue response

            length = len(chunk) + 3
            msg_chunks.append(struct.pack(Message.format, code, length) + chunk)

        if multi_part:
            return msg_chunks
        else:
            return msg_chunks[0]

class MessageHandler:
    def _read_packet(self, socket_):
        if hasattr(socket, "MSG_WAITALL"):
            data = socket_.recv(3, socket.MSG_WAITALL)
        else:
            # Windows lacks MSG_WAITALL
            data = b''
            while len(data) < 3:
                data += socket_.recv(3 - len(data))

        type, length = struct.unpack(">BH", data)
        body_len = length - 3
        while body_len > 0:
            read_len = 32767 if body_len > 32767 else body_len
            data += socket_.recv(read_len, socket.MSG_WAITALL)
            body_len -= read_len
        return type, data

    def decode(self, socket_):
        code, data = self._read_packet(socket_)
        if code in self.message_dict:
            message = self.message_dict[code]()
            message.read_data(data)
            return message
        else:
            return self.UnknownMessageClass(code, data)
