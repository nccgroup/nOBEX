
#
# Released as open source by NCC Group Plc - http://www.nccgroup.com/
#
# Developed by Sultan Qasim Khan, Sultan.QasimKhan@nccgroup.trust
#
# http://www.github.com/nccgroup/nOBEX
#
# Released under GPLv3, a full copy of which can be found in COPYING.
#

import re, socket, threading, time
from nOBEX import server, bluez_helper

error_resp = b'ERROR'

default_beast_table = {
    b'AT+CLCC': None,
    b'AT+CHLD=?': b'+CHLD: (0,1,2,3)',
    b'AT+CNMI=?': b'+CNMI: (0-2),(0-3),(0,2,3),(0-2),(0,1)',
    b'AT+CPBR=?': b'+CPBR: (1-1),30,30',
    b'AT+CSCS=?': b'+CSCS: ("UTF-8","IRA","GSM","8859-1")',
    b'AT+COPS?': b'+COPS: 0,0,"WIND AWAY"',
    b'AT+CMGE=?': error_resp,
    b'AT+CIND?': b'+CIND: 0,0,1,3,1,4,0',
    b'AT+CMER=3,0,0,1': None,
    b'AT+CIND=?': b'+CIND: ("call",(0,1)),("callsetup",(0-3)),("service",(0-1)),("signal",(0-5)),("roam",(0,1)),("battchg",(0-5)),("callheld",(0-2))',
    b'AT+CLIP=1': None,
    b'AT+CSMS=?': b'+CSMS: 0,1,1,1',
    b'AT+CPBS?': b'+CPBS: "ME"',
    b'AT+CPMS="SM"': None,
    b'AT+CMGS=?': error_resp,
    b'AT+CMGD=?': error_resp,
    b'AT+CMGR=?': b'+CMGR: "REC READ","+85291234567",,"07/02/18,00:12:05+32"',
    b'AT+CPMS=?': error_resp,
    b'AT+CCWA=1': None,
    b'AT+NREC=0': None,
    b'AT+CPBS=?': b'+CPBS: ("ME","SM","DC","RC","MC")',
    b'AT+CPBR=1,10': b'+CPBR: 1,"18005555555",129,"Contact Name"',
    b'AT+CMGL=?': b'+CMGL: 1,"REC READ","+85291234567",,"07/05/01,08:00:15+32",145,37',
    b'AT+CMGF=?': b'+CMGF: (0-1)',
    b'AT+CNUM': None,
    b'AT+CMEE=1': None,
    b'AT+CSCS?': b'+CSCS: "8859-1"',
    b'AT+CGMI': b'+CGMI: NCC Group',
    b'AT+CGMM': b'+CGMM: nOBEX',
    b'AT+CGMR': b'+CGMR: 0',
    b'AT+CGSN': b'+CGSN: 012345678901237',
    b'AT+CREG?': b'+CREG: 5,4',
    b'AT+CSQ': b'+CSQ: 20,2',
    b'AT+CBC': b'+CBC: 0,0'
}

# for commands that could end with multiple values, but same response applies
regex_beast_table = {
    b'AT\+CPBS=".*"': None,
    b'AT\+COPS=[0-9].*': None,
    b'AT\+BRSF=[0-9]+': b'+BRSF: 871',
    b'AT\+CSCS=".*"': None,
    b'AT\+VGS=[0-9]+': None,
    b'AT\+VGM=[0-9]+': None,
    b'AT\+BAC=[0-9].*': None,
    b'AT\+CREG=[0-9]+': None
}

class HFPMessageHandler(object):
    def decode(self, sock):
        msg = bytearray()
        while not (msg.endswith(b'\r') or msg.endswith(b'\n')):
            try:
                msg.extend(sock.recv(1))
            except ConnectionResetError:
                print("connection reset")
                return None
        return bytes(msg)

class HFPServer(server.Server):
    def __init__(self, beast_file=None, address=None):
        """beast_file is a bbeast format AT command response table file"""
        super(HFPServer, self).__init__(address)
        self.request_handler = HFPMessageHandler()
        self.resp_dict = default_beast_table
        if beast_file: self._load_beast(beast_file)
        self.conn = None
        self.write_lock = threading.Lock()
        self.commander = ATCommander(self.external_sock_send)
        self.commander.start()

    def start_service(self, port=3):
        # we don't actually listen on a socket for HFP
        bluez_helper.advertise_service("hfag", port)
        print("Advertising HFP on port %i" % port)
        return None

    def _load_beast(self, beast_file):
        lines = open(beast_file, 'rb').readlines()
        for l in lines:
            cmd, resp = l.strip().split(b'\t')
            if resp == b'OK': resp = None
            self.resp_dict[cmd] = resp
        print(self.resp_dict)

    @staticmethod
    def _connect_hfp(address, port=None, control_chan=True, audio_chan=True):
        connection = None

        # Connect to RFCOMM control channel on HF (car kit)
        if control_chan:
            if port is None:
                port = bluez_helper.find_service("hf", address)
            print("HFP connecting to %s on port %i" % (address, port))
            connection = bluez_helper.BluetoothSocket()
            time.sleep(0.5)
            connection.connect((address, port))

        if audio_chan and hasattr(socket, "BTPROTO_SCO"):
            asock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_SCO)
            time.sleep(0.5)
            try:
                asock.connect(bytes(address, encoding="UTF-8"))
            except ConnectionRefusedError:
                print("Connection refused for audio socket")
            else:
                print("HFP SCO audio socket established")

        return connection

    def serve(self, socket):
        """
        This works a little differently from a normal server:
        1. We tell the car that we support HFP over SDP
        2. We look through the listing of paired devices to find a head unit that
           that supports HFP HF mode.
        3. Our HFP AG "server" initiates a connection to the HFP HF "client" that's
           listening on a port. In other words, the "client" is an RFCOMM server.

        While many vehicles do try initiating connections to the HFP AG, these
        vehicle-initiated connections sometimes don't work (eg. on Ford Sync Gen 1).
        They do work on other head units (eg. BMW iDrive CIC-HIGH). Some head units
        never try to initate connections themselves (eg. Porsche PCM). This alternate
        approach of the AG connecting to the HF seems to work on most (but not all)
        head units.
        """
        while True:
            devs = bluez_helper.list_paired_devices()
            for address in devs:
                print("hfp trying", address)
                try:
                    port = bluez_helper.find_service("hf", address)
                except bluez_helper.SDPException:
                    continue
                print("HFP HF found on port %i of %s" % (port, address))
                connection = self._connect_hfp(address, port)
                self.conn = connection

                self.connected = True
                while self.connected:
                    request = self.request_handler.decode(connection)
                    if request is None:
                        self.connected = False
                        break
                    self.commander.sock_notify(request)
                    with self.write_lock:
                        self.process_request(connection, request)
                self.conn = None

    def external_sock_send(self, msg):
        if self.conn is None:
            return
        with self.write_lock:
            self._reply(self.conn, msg, False)

    def process_request(self, sock, cmd):
        print("received AT cmd: %s" % cmd)
        cmd = cmd.strip()

        # We connected to wrong device or at wrong time, need to re-connect
        if len(cmd) == 0:
            return
        elif cmd == b'ERROR':
            print("Peer reports AT ERROR, wants reconnect. Be patient.")
            self.connected = False
            return

        if cmd in self.resp_dict:
            print("known command, resp: %s" % repr(self.resp_dict[cmd]))
            self._reply(sock, self.resp_dict[cmd])
        else:
            match_found = False
            for rx in regex_beast_table:
                if re.match(rx, cmd):
                    print("known regex command, resp %s" % repr(regex_beast_table[rx]))
                    self._reply(sock, regex_beast_table[rx])
                    match_found = True
                    break
            if not match_found:
                print("new command, no response (just OK)")
                self._reply(sock, None)

    def _reply(self, sock, resp, ok=True):
        try:
            msg = b''
            if resp is not None:
                msg += b'\r\n' + resp + b'\r\n'
            if ok and resp != error_resp:
                msg += b'\r\nOK\r\n'
            sock.sendall(msg)
        except BaseException as e:
            print("failure writing AT cmd response")

class ATCommander(threading.Thread):
    def __init__(self, write_cback):
        super(ATCommander, self).__init__(daemon=True)
        self._sock = socket.socket()
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(('127.0.0.1', 7137))
        self._conn = None
        self._conn_lock = threading.Lock()
        self.wcb = write_cback

    def run(self):
        self._sock.listen(0)
        while True:
            self._conn = None
            self._conn, _ = self._sock.accept()
            conn_file = self._conn.makefile('rb')

            try:
                while True:
                    self.process_cmd(conn_file.readline().strip())
            except IOError as e:
                print(e) # handle connection close

    def process_cmd(self, cmd):
        if cmd.startswith(b'send'):
            self.wcb(cmd[5:])
        elif cmd.startswith(b'ursp'): # update auto response
            """syntax: ursp AT_CMD AT_RSP
            example: ursp AT+CLCC +CLCC: 1,1,4,0,0,"1234567890",129
            for simplicity, this syntax assumes every AT command received has no spaces
            the response can have spaces
            this is a reasonable assumption, though might not always work"""
            try:
                atcmd = cmd.split(b' ')[1]
                atrsp = cmd[5 + len(atcmd) + 1:]
                default_beast_table[atcmd] = atrsp
            except:
                with self._conn_lock:
                    self._conn.sendall(b'syntax error!\n')
        else:
            with self._conn_lock:
                self._conn.sendall(b'unknown command!\n')

    def sock_notify(self, msg):
        if self._conn is not None:
            with self._conn_lock:
                self._conn.sendall(b'recvd ' + msg + b'\n')
