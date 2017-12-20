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

class PBAPClient(Client):
    def __init__(self, address, port=None):
        if port is None:
            port = find_service("pbap", address)
        super(PBAPClient, self).__init__(address, port)

    def connect(self):
        uuid = b'\x79\x61\x35\xf0\xf0\xc5\x11\xd8\x09\x66\x08\x00\x20\x0c\x9a\x66'
        super(PBAPClient, self).connect(header_list = [headers.Target(uuid)])
