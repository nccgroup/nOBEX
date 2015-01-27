#!/usr/bin/env python

"""
requests.py - Classes encapsulating OBEX requests.

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

class Request(Message):

    # Define the additional format information required by requests.
    # Subclasses should redefine this when required to ensure that their
    # minimum lengths are calculated correctly.
    format = ""
    
    def __init__(self, data = (), header_data = ()):

        Message.__init__(self, data, header_data)
        self.minimum_length = self.length(Message.format + self.format)
    
    def is_final(self):
    
        return (self.code & 0x80) == 0x80

class Connect(Request):

    code = OBEX_Connect = 0x80
    format = "BBH"
    
    def read_data(self, data):
    
        # Extract the connection data from the complete data.
        extra_data = data[self.length(Message.format):self.minimum_length]
        
        obex_version, flags, max_packet_length = struct.unpack(
            ">"+self.format, extra_data
            )
        
        self.obex_version = OBEX_Version().from_byte(obex_version)
        self.flags = flags
        self.max_packet_length = max_packet_length
        
        Request.read_data(self, data)

class Disconnect(Request):

    code = OBEX_Disconnect = 0x81
    format = ""

class Put(Request):

    code = OBEX_Put = 0x02
    format = ""

class Put_Final(Put):

    code = OBEX_Put_Final = 0x82
    format = ""

class Get(Request):

    code = OBEX_Get = 0x03
    format = ""

class Get_Final(Get):

    code = OBEX_Get_Final = 0x83
    format = ""

class Set_Path(Request):

    code = OBEX_Set_Path = 0x85
    format = "BB"
    NavigateToParent = 1
    DontCreateDir = 2
    
    def read_data(self, data):
    
        # Extract the extra message data from the complete data.
        extra_data = data[self.length(Message.format):self.minimum_length]
        
        flags, constants = struct.unpack(">"+self.format, extra_data)
        
        self.flags = flags
        self.constants = constants
        
        Request.read_data(self, data)

class Abort(Request):

    code = OBEX_Abort = 0xff
    format = ""

class UnknownRequest(Request):

    pass

class RequestHandler(MessageHandler):

    OBEX_User_First = 0x10
    OBEX_User_Last = 0x1f
    
    message_dict = {
        Connect.code: Connect,
        Disconnect.code: Disconnect,
        Put.code: Put,
        Put_Final.code: Put_Final,
        Get.code: Get,
        Get_Final.code: Get_Final,
        Set_Path.code: Set_Path,
        Abort.code: Abort
        }
    
    UnknownMessageClass = UnknownRequest
