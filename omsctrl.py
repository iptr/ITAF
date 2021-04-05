import socket as skt
from commonlib import *

OMS_DMS_PORT = 50011
MAX_RECV_SIZE = 4096
TIME_OUT_SEC = 100

#Command code
DEFAULT_STRUCT_HASH = 0
VERSION_REQ_CODE = 10
VERSION_RES_CODE = 15
POLICY_REQ_CODE = 21
POLICY_RES_CODE = 27
LOGIN_UNIKEY_REQ_CODE = 32
LOGIN_UNIKEY_RES_CODE = 35
IP_CHECK_REQ_CODE = 1040
IP_CHECK_RES_CODE = 1045
LOGIN_REQ_CODE = 2001
LOGIN_FAIL_RES_CODE = 47
SAVE_CLIENT_REQ_CODE = 52
SAVE_CLIENT_RES_CODE = 55
CHECK_SERIAL_REQ_CODE = 72
CHECK_SERIAL_RES_CODE = 75
SERVICE_REQ_CODE = 316
SERVICE_START_RES_CODE = 317
SERVICE_DATA_RES_CODE = 318
LOOPBACK_REQ_CODE = 407
LOOPBACK_REQ_CODE = 408
LOGOUT_REQ_CODE = 92
LOGOUT_RES_CODE = 95

# Structhash code
DEFAULT_STRUCTHASH = 0
MESSAGE_STRUCTHASH = 655
POLICY_STRUCTHASH = 43353 # 보낼때 필요
LOGIN_UNIKEY_STRUCTHASH = 3817 # 보낼때 필요
ENV_UNIKEY_STRUCTHASH = 34711 # 보낼때 필요
LOGIN_V4_STRUCTHASH = 61820 # 보낼때 필요
LOGIN_EX_STRUCTHASH = 2254 # 보낼때 필요
M_DATA_0111_STRUCTHASH = 7 

#etc code
COMMAND_LENGTH = 65535
CHECK_CODE = b'CK'

class PolicyT:
    '''
    응답받은 정책에 대한 데이터 클래스
    '''
    num = 0
    title = ''
    excpt = ''
    value = ''

class OmsPktMaker:
    '''
    OMS_DMS 테스트를 위한 작업 패킷을 만들기 위한 클래스
    '''
    cmd_info = None
    login_info = None
    env_unikey_info = None
    
    def makeCommandInfo(self, cmd, length, structhash, checkcode):
        '''
        OMS_DMS 명령어 부분 만드는 함수
        '''
        payload = usToB(cmd)
        payload += usToB(length)
        payload += usToB(structhash)
        payload += checkcode
        self.cmd_info = payload
        return payload

    def makeLoginInfo(self, struct_type, sno, pw, privip, pubip, 
                      name, tel, part, position, business, 
                      unikey):
        '''
        로그인 패킷 만들때 명령어 뒷부분에 붙는 내용
        Struct_type : 구조체 종류 (unikey, v4, ex)
        '''
        payload = longToB(2)
        payload += usToB(len(sno)) + sno.encode()
        payload += usToB(44) + encode_b64(get_hash_bytes(pw))
        payload += usToB(len(name)) + name.encode()
        payload += usToB(len(tel)) + tel.encode()
        payload += usToB(len(part)) + part.encode()
        payload += usToB(len(position)) + position.encode()
        payload += usToB(len(business)) + business.encode()
        payload += usToB(len(privip)) + privip.encode()
        strtype = struct_type.lower()
        if strtype in ('unikey','v4') :
            #unikey
            payload += usToB(64)
            payload += encode_b64(get_hash_bytes(unikey.encode()))
            self.login_info = payload    
            if strtype == 'v4':
                #pw_sha256
                payload += usToB(44) + encode_b64(get_hash_bytes(pw))
                #pw_sha512
                payload += usToB(128)
                payload += encode_b64(get_hash_bytes(pw, algorithm='sha512'))
                #public ip
                payload += usToB(len(pubip)) + pubip.encode()
                #login_tool
                payload += longToB(0)
                self.logininfo = payload
        return payload
        
    def makeEnvUnikeyInfo(self, env_ip, mac_address, lan_count,
                          nat_version, com_name, cpu_info, mem_info,
                          ipaddr, unikey):
        payload = usToB(len(env_ip)) + env_ip.encode()
        payload += usToB(len(mac_address)) + mac_address.encode()
        payload += usToB(len(lan_count)) + lan_count.encode()
        payload += usToB(len(nat_version)) + nat_version.encode()
        payload += usToB(len(com_name)) + com_name.encode()
        payload += usToB(len(cpu_info)) + cpu_info.encode()
        payload += usToB(len(mem_info)) + mem_info.encode()
        payload += usToB(len(ipaddr)) + ipaddr.encode()
        payload += usToB(64) + encode_b64(get_hash_bytes(unikey.encode()))
        self.env_unikey_info = payload
        return payload

       
class OmsPktSender:
    '''
    패킷을 전송하는 클래스
    '''
    # setConf() 실행여부 Flag
    conf_flag = False
    
    def __init__(self):
        self.pkt_maker = OmsPktMaker()
        
    def setConf(self, host, sno, pw, privip, pubip,
                name, tel, part, position, business,
                envip, mac, nic, natver, comname,
                cpu, mem, ipaddr):
        self.host = host
        self.sno = sno
        self.pw = pw
        self.privip = privip
        self.pubip = pubip
        self.name = name
        self.tel = tel
        self.part = part
        self.position = position
        self.business = business
        self.envip = envip
        self.mac = mac
        self.nic = nic
        self.natver = natver
        self.comname = comname
        self.cpu = cpu
        self.mem = mem
        self.ipaddr = ipaddr
        self.unikey = 'unikey'
        self.conf_flag = True
    
    def sendPacket(self, payload):
        if self.conf_flag != True:
            # Logger 기술
            return -1
        sock = skt.socket(skt.AF_INET, skt.SOCK_STREAM)
        sock.settimeout(TIME_OUT_SEC)
        #sock.setblocking(0)
        sock.connect((self.host, OMS_DMS_PORT))
        print(payload)
        print("Response DATA")
        sock.send(payload)
        data = b''
        while True:
            buf = sock.recv(MAX_RECV_SIZE)
            data += buf
            if not buf:
                break
            if len(buf) < MAX_RECV_SIZE:
                break
        sock.close()
        return data
    
    def sendVersionReqPkt(self):
        if self.conf_flag != True:
            # Logger 기술
            return -1        
        payload = self.pkt_maker.makeCommandInfo(VERSION_REQ_CODE, 
                                       COMMAND_LENGTH,
                                       DEFAULT_STRUCTHASH,
                                       CHECK_CODE)
        return self.sendPacket(payload)
        
    def sendPolicyReqPkt(self):
        if self.conf_flag != True:
            # Logger 기술
            return -1
        payload = self.pkt_maker.makeCommandInfo(POLICY_REQ_CODE,
                                              COMMAND_LENGTH,
                                              DEFAULT_STRUCTHASH,
                                              CHECK_CODE)
        return self.sendPacket(payload)
        
    def sendIPCheckReqPkt(self):
        if self.conf_flag != True:
            # Logger 기술
            return -1
        
        payload = self.pkt_maker.makeCommandInfo(IP_CHECK_REQ_CODE,
                                                 COMMAND_LENGTH,
                                                 DEFAULT_STRUCTHASH,
                                                 CHECK_CODE)
        return self.sendPacket(payload)

    def sendLoginUnikeyReqPkt(self):
        if self.conf_flag != True:
            # Logger 기술
            return -1
        
        payload = self.pkt_maker.makeCommandInfo(LOGIN_UNIKEY_REQ_CODE,
                                                 COMMAND_LENGTH,
                                                 LOGIN_UNIKEY_STRUCTHASH,
                                                 CHECK_CODE)
        payload += self.pkt_maker.makeLoginInfo('Unikey',
                                                self.sno,
                                                self.pw,
                                                self.privip,
                                                self.pubip,
                                                self.name,
                                                self.tel,
                                                self.part,
                                                self.position,
                                                self.business,
                                                self.unikey)
        return self.sendPacket(payload)
        
    def sendLoginReqPkt(self):
        if self.conf_flag != True:
            # Logger 기술
            return -1   
        
        payload = self.pkt_maker.makeCommandInfo(LOGIN_UNIKEY_REQ_CODE,
                                      COMMAND_LENGTH,
                                      LOGIN_UNIKEY_STRUCTHASH,
                                      CHECK_CODE)
        payload += self.pkt_maker.makeLoginInfo('v4',
                                                self.sno,
                                                self.pw,
                                                self.privip,
                                                self.pubip,
                                                self.name,
                                                self.tel,
                                                self.part,
                                                self.position,
                                                self.business,
                                                self.unikey)
        return self.sendPacket(payload)

    def sendSaveEnvReqPkt(self):
        if self.conf_flag != True:
            # Logger 기술
            return -1
        
        payload = self.pkt_maker.makeCommandInfo(SAVE_CLIENT_REQ_CODE,
                                                 COMMAND_LENGTH,
                                                 ENV_UNIKEY_STRUCTHASH,
                                                 CHECK_CODE)
        payload += self.pkt_maker.makeEnvUnikeyInfo(self.envip,
                                                    self.mac,
                                                    self.nic,
                                                    self.natver,
                                                    self.comname,
                                                    self.cpu,
                                                    self.mem,
                                                    self.ipaddr,
                                                    self.unikey)
        return self.sendPacket(payload)
        
    def sendSerialCheckReqPkt(self):
        if self.conf_flag != True:
            # Logger 기술
            return -1
        
        payload = self.pkt_maker.makeCommandInfo(CHECK_SERIAL_REQ_CODE,
                                                 COMMAND_LENGTH,
                                                 LOGIN_UNIKEY_STRUCTHASH,
                                                 CHECK_CODE)
        payload += self.pkt_maker.makeLoginInfo('unikey',
                                                self.sno,
                                                self.pw,
                                                self.privip,
                                                self.pubip,
                                                self.name,
                                                self.tel,
                                                self.part,
                                                self.position,
                                                self.business,
                                                self.unikey)
        return self.sendPacket(payload)
    
    def sendServiceReqPkt(self):
        if self.conf_flag != True:
            # Logger 기술
            return -1
        payload = self.pkt_maker.makeCommandInfo(SERVICE_REQ_CODE,
                                       COMMAND_LENGTH,
                                       LOGIN_EX_STRUCTHASH,
                                       CHECK_CODE)
        payload += self.pkt_maker.makeLoginInfo('ex',
                                                self.sno,
                                                self.pw,
                                                self.privip,
                                                self.pubip,
                                                self.name,
                                                self.tel,
                                                self.part,
                                                self.position,
                                                self.business,
                                                self.unikey)
        return self.sendPacket(payload)
                      
    def sendLoopBackMsgReqPkt(self):
        if self.conf_flag != True:
            # Logger 기술
            return -1
        payload = self.pkt_maker.makeCommandInfo(LOOPBACK_REQ_CODE,
                                                 COMMAND_LENGTH,
                                                 DEFAULT_STRUCTHASH,
                                                 CHECK_CODE)
        return self.sendPacket(payload)
                
    def sendLogoutReqPkt(self):
        if self.conf_flag != True:
            # Logger 기술
            return -1
        payload = self.pkt_maker.makeCommandInfo(LOGOUT_REQ_CODE,
                                                 COMMAND_LENGTH,
                                                 LOGIN_UNIKEY_STRUCTHASH,
                                                 CHECK_CODE)
        payload += self.pkt_maker.makeLoginInfo('unikey', 
                                                self.sno,
                                                self.pw,
                                                self.privip,
                                                self.pubip,
                                                self.name,
                                                self.tel,
                                                self.part,
                                                self.position,
                                                self.business,
                                                self.unikey)
        return self.sendPacket(payload)

def prepareTest():
    pktsender = OmsPktSender()
    pktsender.setConf('192.168.4.200',
                      'trollking',
                      'dbsafer00',
                      '10.77.160.180',
                      '10.77.160.180',
                      'Trollking',
                      '01062445025',
                      'QA',
                      'Tester',
                      'None',
                      '10.77.160.180',
                      'AA:BB:CC:DD:EE:FF',
                      '2',
                      '3.2.32.123',
                      'MyCom',
                      'IntelCPU',
                      '16',
                      '10.77.160.180')
    return pktsender

def runTest(pkts):
    print('Version Request')
    print(pkts.sendVersionReqPkt())
    print('Policy Request')
    print(pkts.sendPolicyReqPkt())
    print('IP check Request')
    print(pkts.sendIPCheckReqPkt())
    print('Login Unikey Request')
    print(pkts.sendLoginUnikeyReqPkt())
    print('Login Request')
    print(pkts.sendLoginReqPkt())
    print('Save Env Request')
    print(pkts.sendSaveEnvReqPkt())
    print('Serial Check Request')
    print(pkts.sendSerialCheckReqPkt())
    print('Service Request')
    print(pkts.sendServiceReqPkt())
    print('LoopBackMsg Request')
    print(pkts.sendLoopBackMsgReqPkt())
    print('Log-out Request')
    print(pkts.sendLogoutReqPkt())
    
def closeTest():
    pass

if __name__ == '__main__':

    pktsender = prepareTest()
    runTest(pktsender)