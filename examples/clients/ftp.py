#
# Released as open source by NCC Group Plc - http://www.nccgroup.com/
#
# Developed by Sultan Qasim Khan, Sultan.QasimKhan@nccgroup.trust
#
# http://www.github.com/nccgroup/nOBEX
#
# Released under GPLv3, a full copy of which can be found in COPYING.
#

from nOBEX.client import Client
from nOBEX.bluez_helper import find_service
from nOBEX import headers

class FTPClient(Client):
    """FTPClient(Client)

    Provides an OBEX client that can be used to browse directories on a
    server via a folder-browsing service (File Transfer Profile).

    The address used is a standard six-field bluetooth address, and the port
    should correspond to the port providing the folder-browsing service.

    To determine the correct port, examine the advertised services for a
    device by calling the nOBEX.bluez_helper.find_service() function with the
    service name and address of the device as arguments.
    """

    def __init__(self, address, port=None):
        if port is None:
            port = find_service("ftp", address)
        super(FTPClient, self).__init__(address, port)

    def connect(self):
        uuid = b"\xF9\xEC\x7B\xC4\x95\x3C\x11\xd2\x98\x4E\x52\x54\x00\xDC\x9E\x09"
        super(FTPClient, self).connect(header_list = [headers.Target(uuid)])

    def capability(self):
        """capability(self)

        Returns a capability object from the server. An exception will pass
        through if there is an error.
        """

        hdrs, data = self.get(header_list=[headers.Type(b"x-obex/capability")])
        return data

class SyncClient(Client):
    def connect(self, header_list=(headers.Target(b"IRMC-SYNC"),)):
        super(SyncClient, self).connect(header_list)

class SyncMLClient(Client):
    def connect(self, header_list=(headers.Target(b"SYNCML-SYNC"),)):
        super(SyncMLClient, self).connect(header_list)

