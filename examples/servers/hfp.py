import bluetooth, socket
from PyOBEX import server

class HFPMessageHandler(object):
    def decode(self, sock):
        msg = bytearray()
        while not msg.endswith(b'\n'):
            try:
                msg.extend(sock.recv(1, socket.MSG_WAITALL))
            except bluetooth.btcommon.BluetoothError:
                print("connection reset")
                break
        return bytes(msg)

class HFPDummyServer(server.Server):
    def __init__(self, *args, **kwargs):
        super(HFPDummyServer, self).__init__(*args, **kwargs)
        self.request_handler = HFPMessageHandler()

    def start_service(self, port=bluetooth.PORT_ANY):
        name = "Handsfree Gateway"
        uuid = bluetooth.PUBLIC_BROWSE_GROUP
        service_classes = [bluetooth.HANDSFREE_AGW_CLASS, bluetooth.GENERIC_AUDIO_CLASS]
        service_profiles = [bluetooth.HANDSFREE_PROFILE]
        provider = ""
        description = ""
        protocols = [bluetooth.RFCOMM_UUID]

        return server.Server.start_service(self, port, name, uuid, service_classes,
                service_profiles, provider, description, protocols)

    def process_request(self, sock, cmd):
        print("received AT cmd: %s" % cmd)
        if cmd.startswith(b'AT+BRSF'):
            self._reply(sock, b'+BRSF: 0\r\n')
        else:
            self._reply(sock, b'OK\r\n')

    def _reply(self, sock, resp):
        try:
            sock.sendall(resp)
        except:
            print("failure writing AT cmd response")
