import bluetooth, socket, time
from PyOBEX import server, common

class HFPMessageHandler(object):
    def decode(self, sock):
        msg = bytearray()
        while not (msg.endswith(b'\r') or msg.endswith(b'\n')):
            try:
                msg.extend(sock.recv(1))
            except bluetooth.btcommon.BluetoothError:
                print("connection reset")
                break
        return bytes(msg)

class HFPServer(server.Server):
    def __init__(self, *args, **kwargs):
        super(HFPServer, self).__init__(*args, **kwargs)
        self.request_handler = HFPMessageHandler()

    def serve(self, socket):
        """
        This works a little differently from a normal server:
        1. We tell the car that we support HFP over SDP
        2. We wait for the car to connect to us to get its MAC address
           the connection the car makes is not suitable for AT commands, even
           though the car tries to send us AT commands over it. Any replies we
           send to the car over RFCOMM are lost.
        3. We query the car's MAC address over SDP for HFP (111e). Be aware that
           some cars (like my Ford Focus) will refuse to list all services they
           offer over SDP. However, you will receive a reply if you query for HFP
           specifically. We will get the channel number to connect to over SDP.
        4. We initiate an RFCOMM connection to the car on the correct port for it.
        """
        while True:
            connection, address = socket.accept()
            port = bluetooth.find_service(uuid="111e", address=address[0])[0]['port']
            connection.close()

            print("HFP connecting to %s on port %i" % (address[0], port))
            connection = common.Socket()
            time.sleep(0.5)
            connection.connect((address[0], port))

            self.connected = True
            while self.connected:
                request = self.request_handler.decode(connection)
                self.process_request(connection, request)

    def start_service(self, port=3):
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
            self._reply(sock, b'\r\n+BRSF: 871\r\n')
        self._reply(sock, b'\r\nOK\r\n')

    def _reply(self, sock, resp):
        try:
            sock.sendall(resp)
        except:
            print("failure writing AT cmd response")
