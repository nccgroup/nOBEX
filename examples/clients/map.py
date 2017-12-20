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

class MAPClient(Client):
    def __init__(self, address, port=None):
        if port is None:
            port = find_service("map", address)
        super(MAPClient, self).__init__(address, port)

    def connect(self):
        uuid = b'\xbb\x58\x2b\x40\x42\x0c\x11\xdb\xb0\xde\x08\x00\x20\x0c\x9a\x66'
        super(MAPClient, self).connect(header_list = [headers.Target(uuid)])
