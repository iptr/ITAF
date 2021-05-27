import socket
import binascii
from multiprocessing import Lock
from struct import pack
from ipaddress import IPv4Address
import dpkt

class NATIDPKT:
    idcode = b'NATIDENTITY'
    pktver = pack('>H',1)
    totlen = pack('>H',0)
    encrypt = pack('>B',0)
    svctype = pack('>I',512)
    rdplog = pack('>I',0)
    svcnum = pack('>I',0)
    localip = b''
    localport = b''
    targetip = b''
    targetport = b''
    gwip = IPv4Address('0.0.0.0').packed
    gwport = pack('>H',0)
    certidlen = pack('>H',12)
    certid = b''
    proglen = pack('>H',11)
    progname = b''
    assistkeylen = pack('>H',0)
    assistkey = b''
    proghashlen = pack('>H',32)
    proghash = b'c30a803fa8897e1e31584d9151ab8064e22a3a02f38a8f891882fb2da9252c6e'
    webassist = pack('>I',0)
    ostype = pack('>H',0)
    msgtunnel = pack('>H',0)
    payload = b''

    def __init__(self):
        pass

    def set(self, svctype = 1,svcnum=b'', tgip=b'', tgport=b'', gwip=b'',
            gwport=b'', certid=b'', loip=b'', loport=b'',progname = b''):
        # 필수정보 교체: 대상서비스번호, 대상IP, port, 로컬IP, 로컬port, dbsIP, dbsport,
        #               보안계정)
        if loip != b'':
            self.localip = IPv4Address(loip).packed
        if loport != b'':
            self.localport = pack('>H',loport)
        if svcnum != b'':
            self.svcnum = pack('>I',int(svcnum))
        if progname != b'':
            self.progname = progname.encode()
        if tgip != b'':
            self.targetip = IPv4Address(tgip).packed
        if tgport != b'':
            self.targetport = pack('>H',int(tgport))
        if gwip != b'':
            self.gwip = IPv4Address(gwip).packed
        if gwport != b'':
            self.gwport = pack('>H',int(gwport))
        if certid != b'':
            try:
                self.certid = certid.encode()
            except Exception as e:
                print('debug : %s, %s'%(e,certid))
    # 보안계정 길이 계산
        self.certidlen = pack('>H',len(self.certid))

        self.svctype = pack('>I', svctype)

        program_len = len(self.progname)
        program_len = hex(program_len).rstrip("L").lstrip("0x") or "0"
        program_len = '0' * (4 - len(program_len)) + program_len
        program_len = bytes.fromhex(program_len)
        self.proglen = program_len

        # 전체 길이 계산(encrypt ~ 끝까지)
        payload = self.encrypt + self.svctype + self.rdplog + self.svcnum
        payload += self.localip + self.localport + self.targetip + self.targetport
        payload += self.gwip + self.gwport + self.certidlen + self.certid
        payload += self.proglen + self.progname + self.assistkeylen + self.assistkey
        payload += self.proghashlen + self.proghash + self.webassist + self.ostype + self.msgtunnel
        self.totlen = pack('>H', len(payload))
        self.payload = self.idcode + self.pktver + self.totlen + payload

        print(self.payload)
        return self.payload

    @staticmethod
    def getTypeNumber(type):
        type = type.lower()

        type_num = -1

        if type == 'oracle':
            type_num = 1
        elif type == 'ftp':
            type_num = 2
        elif type == 'telnet':
            type_num = 4
        elif type == 'tp':
            type_num = 16
        elif type == 'bypass':
            type_num = 32
        elif type == 'bridge oracle':
            type_num = 65
        elif type == 'bridge ftp':
            type_num = 66
        elif type == 'bridge telnet':
            type_num = 68
        elif type == 'bridge tp':
            type_num = 78
        elif type == 'bridge bypass':
            type_num = 96
        elif type == 'tibero':
            type_num = 10
        elif type == 'teradata':
            type_num = 6
        elif type == 'sybaseiq':
            type_num = 256
        elif type == 'informix':
            type_num = 3
        elif type == 'hanadb':
            type_num = 15
        elif type == 'goldilocks':
            type_num = 19
        elif type == 'cubrid':
            type_num = 11
        elif type == 'altibase':
            type_num = 5
        elif type == 'telnet sniff':
            type_num = 16388
        elif type == 'teradata sniff':
            type_num = 16390
        elif type == 'udb':
            type_num = 7
        elif type == 'mysql':
            type_num = 9
        elif type == 'postgresql':
            type_num = 12
        elif type == 'sybase sniff':
            type_num = 16512
        elif type == 'mssql':
            type_num = 512


        return type_num

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

class PcapReader:
    def __init__(self,path):
        self.path = path

    def getPacketData(self):
        '''
        pcap 파일 읽기

        @return
            tcp stream이 담긴 배열
        '''
        count = 0
        pair = {}
        stream_data = [[]]
        size = 0

        with open(self.path,'rb') as f:
            pcap = dpkt.pcap.Reader(f)

            for ts, buf in pcap:
                try:
                    eth = dpkt.sll.SLL(buf)
                    ip = eth.data
                    tcp = ip.data

                    # Syn 확인 Syn Ack 제외
                    if (tcp.flags & dpkt.tcp.TH_SYN):
                        if (tcp.flags & dpkt.tcp.TH_ACK) == 0:
                            src_pair = (ip.src, tcp.sport)
                            dst_pair = (ip.dst, tcp.dport)
                            pair[count] = (src_pair, dst_pair)
                            count += 1

                    # Stream 개수 리스트 크기 조정
                    size = len(stream_data)
                    if len(pair) - size > 0:
                        for i in range(len(pair) - size):
                            stream_data.append([])

                    # 패킷의 데이터가 있을 시
                    if len(tcp.data) != 0:
                        for i in range(len(pair)):
                            if pair[i][0][0] == ip.src and pair[i][0][1] == tcp.sport and pair[i][1][0] == ip.dst and pair[i][1][1] == tcp.dport:
                                # 패킷 데이터 스트림에 저장
                                stream_data[i].append(Packet(direction=True, packet=tcp.data))
                                break
                            elif pair[i][0][0] == ip.dst and pair[i][0][1] == tcp.dport and pair[i][1][0] == ip.src and pair[i][1][1] == tcp.sport:
                                # 패킷 데이터 스트림에 저장
                                stream_data[i].append(Packet(direction=False, packet=tcp.data))
                                break
                            else:
                                pass
                except Exception as e:
                    pass

        f.close()

        return stream_data

class VirtualConnector:
    lock = Lock()

    def __init__(self,target_ip,service_port, dbsafer_ip, dbsafer_port,svcnum,cert_info_list):
        '''

        @param
            service_port - 기존의 서비스 포트
            dbsafer_ip - 접속하고자하는 dbsafer IP
            dbsafer_port - 접속하고자하는 dbsafer port
        '''
        self.target_ip = target_ip
        self.dbsafer_ip = dbsafer_ip
        self.dbsafer_port = dbsafer_port
        self.service_port = service_port
        self.svcnum = svcnum
        self.cert_info_list = cert_info_list

    def dbModeConnect(self,type):
        self.lock.acquire()
        try:
            nat = NATIDPKT()
            service_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            service_sock.connect((self.dbsafer_ip, self.dbsafer_port))
            service_sock.send(nat.set(svcnum=self.svcnum,svctype=type,tgip=self.target_ip,tgport=self.service_port,gwport=self.dbsafer_port,gwip=self.dbsafer_ip,certid=self.cert_info_list[0],loip=self.cert_info_list[2],loport=service_sock.getsockname()[1],progname=self.cert_info_list[1]))

            return (service_sock)
        except Exception as e:
            print("Session Error")
            print(e)
        finally:
            self.lock.release()

    def rdpModeConnect(self):
        self.lock.acquire()
        try:
            nat =NATIDPKT()
            telnet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            telnet_socket.connect((self.dbsafer_ip, self.dbsafer_port))
            telnet_socket.send(nat.set(svcnum=self.svcnum,svctype=4,tgip=self.target_ip,tgport=self.service_port,gwport=self.dbsafer_port,gwip=self.dbsafer_ip,certid=self.cert_info_list[0],loip=self.cert_info_list[1],loport=telnet_socket.getsockname()[1]))
            # 필수정보 교체: 대상서비스번호, 대상IP, port, 로컬IP, 로컬port, dbsIP, dbsport,
            #               보안계정)))

            return (telnet_socket)

        except Exception as e:
            print("Session Error")
            print(e)
        finally:
            self.lock.release()

class VirtualServer:
    def __init__(self,service_port,dbsafer_ip,wta_info = [],wta_proxy_info=[]):
        self.dbsafer_ip = dbsafer_ip
        self.wta_info = wta_info
        self.wta_proxy_info = wta_proxy_info
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serversocket.bind(('', int(service_port)))
        self.serversocket.listen(10000)

    def dbmsModeServer(self):
        try:
            (dbms_sock, address) = self.serversocket.accept()

            return (dbms_sock)
        except Exception as e:
            print("Session Error")
            print(e)

    def rdpModeServer(self):
        try:
            wta_info_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            wta_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            wta_info_socket.connect((str(self.wta_info[0]),int(self.wta_info[1])))
            wta_socket.connect((str(self.wta_proxy_info[0]),int(self.wta_proxy_info[1])))

            print(wta_info_socket,wta_socket)
            (terminal_socket, address) = self.serversocket.accept()

            return (terminal_socket,wta_socket,wta_info_socket)
        except Exception as e:
            print("Session Error")
            print(e)
