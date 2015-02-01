#!/usr/bin/env python

"""
reponses.py - Classes encapsulating OBEX responses.

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

import struct
from PyOBEX.common import OBEX_Version, Message, MessageHandler

class Response(Message):

    # Define the additional format information required by responses.
    # Subclasses should redefine this when required to ensure that their
    # minimum lengths are calculated correctly.
    format = ""
    
    def __init__(self, data = (), header_data = ()):

        Message.__init__(self, data, header_data)
        self.minimum_length = self.length(Message.format + self.format)

class FailureResponse(Response):

    pass

class Continue(Response):
    code = OBEX_Continue = 0x90

class Success(Response):
    code = OBEX_OK = OBEX_Success = 0xA0

class ConnectSuccess(Response):
    code = OBEX_OK = OBEX_Success = 0xA0
    format = "BBH"

class Bad_Request(FailureResponse):
    code = OBEX_Bad_Request = 0xC0

class Unauthorized(FailureResponse):
    code = OBEX_Unauthorized = 0xC1

class Forbidden(FailureResponse):
    code = OBEX_Forbidden = 0xC3

class Not_Found(FailureResponse):
    code = OBEX_Not_Found = 0xC4

class Precondition_Failed(FailureResponse):
    code = OBEX_Precondition_Failed = 0xCC

class UnknownResponse(Response):
    def __init__(self, code, length, data):
        self.code = code
        self.length = length
        self.data = data[3:]


class ResponseHandler(MessageHandler):

    message_dict = {
        Continue.code: Continue,
        Success.code: Success,
        Bad_Request.code: Bad_Request,
        Unauthorized.code: Unauthorized,
        Not_Found.code: Not_Found,
        Precondition_Failed.code: Precondition_Failed
        }
    
    UnknownMessageClass = UnknownResponse
    
    def decode_connection(self, socket):
    
        code, length, data = self._read_packet(socket)
        
        if code == ConnectSuccess.code:
            message = ConnectSuccess()
        elif code in self.message_dict:
            message = self.message_dict[code]()
        else:
            return self.UnknownMessageClass(code, length, data)
        
        obex_version, flags, max_packet_length = struct.unpack(">BBH", data[3:7])
        
        message.obex_version = OBEX_Version()
        message.obex_version.from_byte(obex_version)
        message.flags = flags
        message.max_packet_length = max_packet_length
        message.read_data(data)
        return message
