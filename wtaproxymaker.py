import hashxor

class WtaProxyPacketMaker:
    def __init__(self,wta_info,login_id):
        self.result = b''
        self.hash_value = b''
        self.login_id = login_id
        self.dbsafer_port = 0
        self.target_ip = ''
        self.target_port = 0
        self.wta_info = wta_info
        self.port_map = {}
        self.setWtaInfo()
        print(self.target_port)
        print(self.target_ip)
        print(self.wta_info)

    def setWtaInfo(self):
        '''
        WAS 정보 취득

        '''
        self.target_ip = self.wta_info[b"CLIENT_IP"].decode("ascii")
        self.dbsafer_port = int(self.wta_info[b"SERVICE_PORT"].decode("ascii"))
        port_data = self.wta_info[b"PORTS_MAP"].decode("ascii")
        split_result = port_data.split(",")
        print(split_result)
        for i in range(len(split_result)):
            result_data = split_result[i]
            devide_port = result_data.split(":")
            self.port_map[int(devide_port[1])] = int(devide_port[0])
        print(self.port_map)
        self.target_port = self.port_map[self.dbsafer_port]

    def setHead(self):
        result = b''
        MSG = b'WTA'
        UnKnown=bytes.fromhex("18")

        result += bytes.fromhex("00") + bytes.fromhex("01")
        port_hex = hex(self.dbsafer_port).rstrip("L").lstrip("0x") or "0"
        port_hex = '0' * (8 - len(port_hex)) + port_hex

        result += bytes.fromhex(port_hex)
        ip_list = self.target_ip.split(".")

        result += MSG + UnKnown
        for i in range(len(ip_list)):
            print(hex(int(ip_list[i])))
            ip_hex = hex(int(ip_list[i])).rstrip("L").lstrip("0x") or "0"
            ip_hex = '0' * (2 - len(ip_hex)) + ip_hex
            print(ip_hex)
            result += bytes.fromhex(ip_hex)

        print(result)
        return result


    def makePacket(self):
        # wta_proxy_server 기준
        # 01 (?) ~~~
        # dbsafer PORT
        # WTA ? IP (ex) 0a 4d a2 0b -> 10 77 162 11)
        # hash
        # body
        # 1. 구분자 0x20
        # 2. Login: ~~~~
        # 3. IP
        # 4. PORT
        # 5. ? (기본값 0)
        token = bytes.fromhex("20")
        final = bytes.fromhex("30")
        #length = 0
        MSG = b"Login:"
        tt = b'17676'
        UNKNOW1 = bytes.fromhex("0000004a60891896")
        UNKNOW2 = bytes.fromhex("000000000000000000000000")
        print(UNKNOW1)
        login_id = self.login_id.encode()

        service_ip = self.target_ip.encode()

        service_port = str(self.target_port).encode()

        content = MSG + token + login_id + token + tt + token + final

        length = len(content)
        length = hex(length).rstrip("L").lstrip("0x") or "0"
        length = '0' * (8 - len(length)) + length
        length = bytes.fromhex(length)

        self.result += UNKNOW1 + length + UNKNOW2 + content

        print(self.result)

    def encryptPacket(self):
        packet = b''

        hash_object = hashxor.HashMd5(self.result)
        hash_result = hash_object.hashing()
        hash_result = bytes.fromhex(hash_result)
        packet = hash_result + self.result

        self.hash_value = packet[:16]

        encrypt_objcet = hashxor.HashXor(packet)

        result = encrypt_objcet.encrypt(packet[16:],len(packet) - 16)
        result = self.hash_value + result

        return result

    def decryptPacket(self,text):
        decry = hashxor.HashXor(text)

        result = decry.decrypt(text[16:],len(text) - 16)

        return result

    def startSignal(self):
        result = bytes.fromhex("00") + bytes.fromhex("01")

        return result

    def getPort(self):
        port_hex = hex(self.dbsafer_port).rstrip("L").lstrip("0x") or "0"
        port_hex = '0' * (8 - len(port_hex)) + port_hex

        result = bytes.fromhex(port_hex)

        return result

    def getIP(self):
        MSG = b'WTA'
        UnKnown=bytes.fromhex("57")
        ip_list = self.target_ip.split(".")

        result = MSG + UnKnown
        for i in range(len(ip_list)):
            print(hex(int(ip_list[i])))
            ip_hex = hex(int(ip_list[i])).rstrip("L").lstrip("0x") or "0"
            ip_hex = '0' * (2 - len(ip_hex)) + ip_hex
            print(ip_hex)
            result += bytes.fromhex(ip_hex)

        return result

    def dynamicPacketMaker(self,port):
        result = b''
        port_hex = hex(port).rstrip("L").lstrip("0x") or "0"
        port_hex = '0' * (8 - len(port_hex)) + port_hex

        result += bytes.fromhex(port_hex)

        return result