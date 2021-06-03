import time
import hashxor

class WtaPacketMaker:
    '''
    This class is a class related to the wta_server_manager packet, and includes functions to execute packet rules, encryption, and decryption.
    '''
    def __init__(self):
        self.token = bytes.fromhex("0a")
        self.eq_chr = b"="
        self.colon = b":"
        self.current_time_header = b"CURRENT_TIME"
        self.client_ip_header = b"CLIENT_IP"
        self.service_ip_header = b"SERVICE_IP"
        self.service_port_header = b"SERVICE_PORT"
        self.wta_proxy_port_header = b"WTA_PROXY_PORT"
        self.ports_map_header = b"PORTS_MAP"
        self.result = b""
        self.hash_value = b''

    def makePacket(self,client_ip,service_ip,service_port,wta_proxy_port,client_port):
        '''
        wta_server_manager 패킷 생성

        @param
            client_ip - 클라이언트 아이피
            service_ip - 서비스 아이피
            service_port - 서비스 포트
            wta_proxy_port - DBSAFER GW 에서 wta_proxy가 사용하는 포트
            client_port - 클라이언트 포트
        '''
        current_time = str(int(time.time()))

        current_time = current_time.encode()

        client_ip = client_ip.encode()

        service_ip = service_ip.encode()

        service_port = str(service_port).encode()

        wta_proxy_port = str(wta_proxy_port).encode()

        client_port = str(client_port).encode()

        ports_map = client_port + self.colon + service_port

        self.result += self.current_time_header + self.eq_chr + current_time + self.token
        self.result += self.client_ip_header + self.eq_chr + client_ip + self.token
        self.result += self.service_ip_header + self.eq_chr + service_ip + self.token
        self.result += self.service_port_header + self.eq_chr + service_port + self.token
        self.result += self.wta_proxy_port_header + self.eq_chr + wta_proxy_port + self.token
        self.result += self.ports_map_header + self.eq_chr + ports_map + self.token

    def encryptPacket(self):
        '''
        wta_server_manager 패킷 암호화

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
        wta_server_manager 패킷 복호화

        @param
            text - 암호문

        @return
            평문
        '''
        decry = hashxor.HashXor(text)

        result = decry.decrypt(text[16:],len(text) - 16)

        return result

    def collectInfo(self,wta_info_socket):
        '''
        socket 을 입력 받아 wta 에서 받는 정보를 반환
        반환된 정보는 wta_proxy_server패킷을 만들어 보낼때 사용

        @param
            wta_info_socket - DBSAFER Log 에 올라와 있는 wta_server_manager와 통신하는 소켓

        @return
            wta에서 보낸 정보들을 mapping 한 result
        '''
        wta_info = {}
        wta_recv = wta_info_socket.recv(1000)
        if len(wta_recv) != 0:
            decrypt = self.decryptPacket(wta_recv).split(bytes.fromhex("0a"))
            for i in range(len(decrypt)):
                if decrypt[i].find(bytes.fromhex("3d")) != -1:
                    token_result = decrypt[i].split(bytes.fromhex("3d"))
                    wta_info[token_result[0]] = token_result[1]

        return wta_info

if __name__ == '__main__':
    w = WtaPacketMaker()
    w.makePacket(client_ip='192.168.3.221',client_port=3306,wta_proxy_port=3307,service_port=3308,service_ip="192.168.3.222")
    print(w.encryptPacket())
    print(w.decryptPacket(w.encryptPacket()))


