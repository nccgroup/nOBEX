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

class OPPClient(Client):
    def __init__(self, address, port=None):
        if port is None:
            port = find_service("opush", address)
        super(OPPClient, self).__init__(address, port)
