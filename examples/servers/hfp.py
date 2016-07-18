import bluetooth, socket, time
from PyOBEX import server, common

default_beast_table = {
    b'AT+CLCC': None,
    b'AT+CHLD=?': b'+CHLD: (0,1,2,3)',
    b'AT+CNMI=?': b'+CNMI: (0-2),(0-3),(0,2,3),(0-2),(0,1)',
    b'AT+CPBR=?': b'+CPBR: (1-1),30,30',
    b'AT+CPBS="ME"': None,
    b'AT+CSCS=?': b'+CSCS: ("UTF-8","IRA","GSM")',
    b'AT+CPBS="MC"': None,
    b'AT+COPS?': b'+COPS: 0,0,"WIND AWAY"',
    b'AT+CMGE=?': b'ERROR',
    b'AT+CIND?': b'+CIND: 0,0,1,5,0,5,0',
    b'AT+CMER=3,0,0,1': None,
    b'AT+CSCS="UTF-8"': None,
    b'AT+CIND=?': b'+CIND: (\\"call\\",(0,1)),(\\"callsetup\\",(0-3)),(\\"service\\",(0-1)),(\\"signal\\",(0-5)),(\\"roam\\",(0,1)),(\\"battchg\\",(0-5)),(\\"callheld\\",(0-2))',
    b'AT+CLIP=1': None,
    b'AT+CSMS=?': b'+CSMS: 0,1,1,1',
    b'AT+CPBS?': b'+CPBS: "ME"',
    b'AT+CPMS="SM"': None,
    b'AT+CMGS=?': b'ERROR',
    b'AT+CMGD=?': b'ERROR',
    b'AP+COPS=3,0': None,
    b'AT+CMGR=?': b'+CMGR: "REC READ","+85291234567",,"07/02/18,00:12:05+32"',
    b'AT+COPS=3,2': None,
    b'AT+CPMS=?': b'ERROR',
    b'AT+CCWA=1': None,
    b'AT+NREC=0': None,
    b'AT+CPBS=?': b'+CPBS: ("ME","SM","DC","RC","MC")',
    b'AT+CPBR=1,10': b'+CPBR: 1,"18005555555",129,"Contact Name"',
    b'AT+BRSF=39': b'+BRSF: 871',
    b'AT+CMGL=?': b'+CMGL: 1,"REC READ","+85291234567",,"07/05/01,08:00:15+32",145,37',
    b'AT+CMGF=?': b'+CMGF: (0-1)',
    b'AT+BRSF=111': b'+BRSF: 871',
    b'AT+CNUM': None
}

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
    def __init__(self, beast_file=None):
        """beast_file is a bbeast format AT command response table file"""
        super(HFPServer, self).__init__()
        self.request_handler = HFPMessageHandler()
        self.resp_dict = default_beast_table
        if beast_file: self._load_beast(beast_file)

    def _load_beast(self, beast_file):
        lines = open(beast_file, 'rb').readlines()
        for l in lines:
            cmd, resp = l.strip().split(b'\t')
            if resp == b'OK': resp = None
            self.resp_dict[cmd] = resp
        print(self.resp_dict)

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
            time.sleep(1)
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
        cmd = cmd.strip()
        if cmd in self.resp_dict:
            print("known command, resp: %s" % repr(self.resp_dict[cmd]))
            self._reply(sock, self.resp_dict[cmd])
        else:
            print("new command, no response (just OK)")
            self._reply(sock, None)

    def _reply(self, sock, resp):
        try:
            if resp is not None:
                sock.sendall(b'\r\n' + resp + b'\r\n')
            sock.sendall(b'\r\nOK\r\n')
        except:
            print("failure writing AT cmd response")
