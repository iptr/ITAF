import time
import hashxor

class WtaPacketMaker:
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
        packet = b''

        hash_object = hashxor.HashMd5(self.result)
        hash_result = hash_object.hashing()
        hash_result = bytes.fromhex(hash_result)
        packet = hash_result + self.result
        print(packet)
        print()
        self.hash_value = packet[:16]

        encrypt_objcet = hashxor.HashXor(packet)

        result = encrypt_objcet.encrypt(packet[16:],len(packet) - 16)
        result = self.hash_value + result

        return result

    def decryptPacket(self,text):
        decry = hashxor.HashXor(text)

        result = decry.decrypt(text[16:],len(text) - 16)

        return result

if __name__ == '__main__':
    w = WtaPacketMaker()
    w.makePacket(client_ip='192.168.3.221',client_port=3306,wta_proxy_port=3307,service_port=3308,service_ip="192.168.3.222")
    print(w.encryptPacket())
    print(w.decryptPacket(w.encryptPacket()))