import socket
import binascii
from multiprocessing import Lock
import termctrl
import wtapacket


class Packet:
    direction = True
    packet = ''

    def __init__(self, direction, packet):
        '''
        생성자

        @param
            direction - send,receive 구분자
            packet - 데이터
        '''
        self.direction = direction
        self.packet = packet


class PacketReader:
    @staticmethod
    def read(data):
        '''
        패킷 데이터를 읽는 함수

        @param
            data - 패킷 데이터

        @return
            읽은 패킷 데이터 리스트
        '''

        datas = ""

        # 패킷 데이터 줄단위로 나눔
        if isinstance(data, list) or isinstance(data, str):
            data = ''.join(data)
            datas = data.split('\n')
        else:
            print("ERROR!@#!@#")
            return False

        ret = []
        packet = []

        last_direction = True
        for l in datas:
            l_strip = l.strip()
            if len(l_strip) == 0:
                if len(packet) == 0:
                    continue
                ret.append(Packet(last_direction, bytes(packet)))
                packet = []
                continue
            direction = l[0] != ' '
            # Check direction.
            if last_direction != direction and len(packet) != 0:
                ret.append(Packet(last_direction, bytes(packet)))
                packet = []
            last_direction = direction

            values = ''.join(l_strip[10:59].split(' '))
            # ASCII 변환
            bytes_value = binascii.unhexlify(values)
            packet.extend(list(bytes_value))

            if (len(bytes_value) < 16 and len(packet) != 0):
                # 패킷을 바이트로 인코딩 한 결과를 추가
                ret.append(Packet(last_direction, bytes(packet)))
                packet = []

        if len(packet) != 0:
            ret.append(Packet(last_direction, bytes(packet)))

        return ret


class VirtualConnector:
    lock = Lock()

    def __init__(self,  service_port, dbsafer_ip, dbsafer_port):
        '''

        @param
            service_port - 기존의 서비스 포트
            dbsafer_ip - 접속하고자하는 dbsafer IP
            dbsafer_port - 접속하고자하는 dbsafer port
        '''
        self.dbsafer_ip = dbsafer_ip
        self.dbsafer_port = dbsafer_port
        self.service_port = service_port

    async def dbModeConnect(self):
        self.lock.acquire()
        try:
            service_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            service_sock.connect((self.dbsafer_ip, self.dbsafer_port))
            return (service_sock)
        except Exception as e:
            print("Session Error")
            print(e)
        finally:
            self.lock.release()

    def rdpModeConnect(self):
        self.lock.acquire()
        try:
            nat = termctrl.NATIDPKT()
            telnet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            telnet_socket.connect((self.dbsafer_ip, self.dbsafer_port))
            telnet_socket.send(nat.set(tgip="10.77.162.13",tgport=self.service_port,gwport=self.dbsafer_port,gwip="192.168.4.190",certid="shyoon",loip=telnet_socket.getsockname()[0],loport=telnet_socket.getsockname()[1]))
            # 필수정보 교체: 대상서비스번호, 대상IP, port, 로컬IP, 로컬port, dbsIP, dbsport,
            #               보안계정)))
            #print(w.encryptPacket())
            #test.send(w.encryptPacket())
            # print(terminal_socket)
            # print(telnet_socket)
            # print(wta_socket)
            return (telnet_socket)
        except Exception as e:
            print("Session Error")
            print(e)
        finally:
            self.lock.release()

        # async def rdpModeConnect(self):
        #     self.lock.acquire()
        #     try:
        #         nat = termctrl.NATIDPKT()
        #         telnet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #         print(self.dbsafer_port)
        #         telnet_socket.connect((self.dbsafer_ip, self.dbsafer_port))
        #         telnet_socket.send(nat.set(tgip="10.77.162.11", tgport=self.service_port, gwport=self.dbsafer_port,
        #                                    gwip="192.168.4.190", certid="shyoon", loip=telnet_socket.getsockname()[0],
        #                                    loport=telnet_socket.getsockname()[1]))
        #         # 필수정보 교체: 대상서비스번호, 대상IP, port, 로컬IP, 로컬port, dbsIP, dbsport,
        #         #               보안계정)))
        #         wta_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #         (terminal_socket, address) = self.serversocket.accept()
        #         wta_socket.connect((self.dbsafer_ip, 3141))
        #         wta_info_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #         wta_info_socket.connect((self.dbsafer_ip, 3140))
        #
        #         w = wtapacket.WtaPacketMaker()
        #         w.makePacket(client_ip="10.77.162.11", client_port=self.service_port, wta_proxy_port=3141,
        #                      service_port=self.dbsafer_port,
        #                      service_ip="192.168.4.190")
        #         # print(w.encryptPacket())
        #         # test.send(w.encryptPacket())
        #         # print(terminal_socket)
        #         # print(telnet_socket)
        #         # print(wta_socket)
        #
        #         return (terminal_socket, telnet_socket, wta_socket, wta_info_socket)
        #     except Exception as e:
        #         print("Session Error")
        #         print(e)
        #     finally:
        #         self.lock.release()
class VirtualServer:
    def __init__(self,service_port,dbsafer_ip,dbsafer_port):
        self.dbsafer_ip = dbsafer_ip
        self.dbsafer_port = dbsafer_port
        self.service_port = service_port
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serversocket.bind(('', service_port))
        self.serversocket.listen(100)

    def rdpModeServer(self):
        try:
            wta_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            wta_socket.connect((self.dbsafer_ip, 3141))
            wta_info_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            wta_info_socket.connect((self.dbsafer_ip, 3140))
            print(wta_info_socket,wta_socket)
            (terminal_socket, address) = self.serversocket.accept()

            return (terminal_socket,wta_socket,wta_info_socket)
        except Exception as e:
            print("Session Error")
            print(e)
