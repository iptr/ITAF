import hashxor
import time

class WtaProxyPacketMaker:
    '''
    This class is a class that processes packets to be sent to wta_proxy_server.

    Since wta_proxy_server communicates with encryption, there is an encryption function, and a decryption function is added to check whether encryption is normal. Also included is a function that creates a packet according to the wta_proxy_server packet rule.
    '''
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
        client ip, service port, mapping 되어 있는 port 의 정보를 취득
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
        '''
        127.0.0.1 의 콘솔 접속 로깅 시 사용되는 패킷
        wta 헤더 부분

        @return
            Head Result
        '''
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
        '''
        암호화를 하지 않은 WTA_PROXY 패킷을 생성
        '''
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
        '''
        wta 패킷을 암호화
        wta_proxy_server의 규칙에 따라 암호화 진행

        @return
            암호문
        '''
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
        '''
        암호화된 패킷을 복호화 하는 함수
        제대로 암호화가 되었는 검증을 하기 위해 사용

        @param
            text - 암호화된 내용

        @return
            평문
        '''
        decry = hashxor.HashXor(text)

        result = decry.decrypt(text[16:],len(text) - 16)

        return result

    def startSignal(self):
        '''
        버전 정보를 명시
        패킷의 최 상단의 표기 되기 때문에 시작 신호라고 봐도 무방

        @return
            0x000x01
        '''
        result = bytes.fromhex("00") + bytes.fromhex("01")

        return result

    def getPort(self):
        '''
        wta 에서 받은 port 정보를 반환

        @return
            port value
        '''
        port_hex = hex(self.dbsafer_port).rstrip("L").lstrip("0x") or "0"
        port_hex = '0' * (8 - len(port_hex)) + port_hex

        result = bytes.fromhex(port_hex)

        return result

    def getIP(self):
        '''
        wta 에서 받은 ip 정보를 반환

        @return
            ip value
        '''
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
        '''
        wta_proxy_server 에 동적 포트를 사용해서 보낼 시 해당 함수를 사용

        @param
            port - telnet Port (역바인드해야해서)

        @result
            port data(4 Byte)
        '''
        result = b''
        port_hex = hex(port).rstrip("L").lstrip("0x") or "0"
        port_hex = '0' * (8 - len(port_hex)) + port_hex

        result += bytes.fromhex(port_hex)

        return result