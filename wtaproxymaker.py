import hashxor
import time

class WtaProxyPacketMaker:
    def __init__(self,login_id,target_ip,wta_info={}):
        self.result = b''
        self.hash_value = b''
        self.login_id = login_id
        self.target_ip = target_ip
        self.dbsafer_port = 0
        self.target_port = 0
        self.wta_info = wta_info
        self.port_map = {}
        #self.setWtaInfo()
        #print(self.target_ip)
        #print(self.target_port)

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
        # 프로토콜 버전 (2 Byte) 00 01
        # telnet SRC Port (4 Byte)
        # 총 길이(4 Byte)
        # 시간(4 Byte)
        # 명령어 길이(4 Byte)
        # 결과 길이(4 Byte)
        # 이미지 길이(4 Byte)
        # 델타 이미지 여부(4 Byte)
        # 명령어
            # Login: ~~~~
            # IP
        # 응답 값
        # 이미지 데이터
        token = bytes.fromhex("20")
        final = bytes.fromhex("30")
        #length = 0
        MSG = b"Login:"
        rsp = b'17676'
        current_time = bytes.fromhex("12345678")
        result_len = bytes.fromhex("00000000")
        image_len = bytes.fromhex("00000000")
        delta_image_len = bytes.fromhex("00000000")

        login_id = self.login_id.encode()
        target_ip = self.target_ip
        service_ip = target_ip.encode()

        content = MSG + token + login_id + token + service_ip + token + rsp + token + final

        length = len(content)
        length = hex(length).rstrip("L").lstrip("0x") or "0"
        length = '0' * (8 - len(length)) + length
        length = bytes.fromhex(length)

        # 명령어 길이 + 헤더
        total_length = len(content) + 24
        total_length = hex(total_length).rstrip("L").lstrip("0x") or "0"
        total_length = '0' * (8 - len(total_length)) + total_length
        total_length = bytes.fromhex(total_length)

        self.result += total_length + current_time + length + result_len + image_len + delta_image_len + content

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