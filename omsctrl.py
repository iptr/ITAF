import socket as skt
import binascii as ba
import platform as pf
import time
from commonlib import *

OMS_DMS_PORT = 50011
MAX_RECV_SIZE = 4192
TIME_OUT_SEC = 30

#Request Command Code
VERSION_REQ = 10
POLICY_REQ = 21
LOGIN_UNIKEY_REQ = 32
ALIVE_CHECK_REQ = 1002
IP_CHECK_REQ = 1040
LOGIN_REQ = 2001
SAVE_CLIENT_REQ = 52
CHECK_SERIAL_REQ = 72
SERVICE0111_REQ = 316
SERVICE0112_REQ = 342
LOOPBACK_REQ = 407
LOGOUT_REQ = 92

#Response Command Code
VERSION_RET = 15
POLICY_RET = 27
POLICY_ERR = 28
IP_CHECK_RET = 1045

#LoginUnikey Res code
CERTID_NOT_LOGGED_IN = 35
CERTID_LOGGED_IN = 36
CERTID_LOGIN_ERR = 37

#Login Res code
LOGIN_RET = 45
LOGIN_RET_SHA256 = 52
LOGIN_ERR = 46
LOGIN_ERR_PASSWD = 47
LOGIN_ERR_LOCK_TEMP = 48
LOGIN_ERR_LOCK = 49
LOGIN_ERR_EXPIRY = 50
LOGIN_ERR_DOUBLE_ACCESS_DENY = 53
LOGIN_ERR_NOT_EXIST = 54

#Save Env Res code
SAVE_ENV_RET = 55
SAVE_ENV_ERR = 56

#Check Serial (서비스 변경 유무 확인)
SERIAL_RET = 75
SERIAL_ERR = 76
SERIAL_LOGOUT = 77
SERIAL_SAME_IP = 78

SERVICE_0111_START_RET = 317
SERVICE_0111_DATA_RET = 318
SERVICE_0111_END_RET = 313
SERVICE_0112_START_RET = 343
SERVICE_0112_DATA_RET = 344
SERVICE_0112_END_RET = 345

LOOPBACK_RET = 408
LOGOUT_RET = 95
LOGOUT_ERR = 96

#서버 이상 유무 응답
ALIVE_RET = 1005
ALIVE_ERR = 1006
ALIVE_LOGOUT = 1007
ALIVE_SAME_IP = 1008

# Structhash code
DEFAULT_STRUCTHASH = 0
MESSAGE_STRUCTHASH = 655
POLICY_STRUCTHASH = 43353 # 보낼때 필요
LOGIN_UNIKEY_STRUCTHASH = 3817 # 보낼때 필요
ENV_UNIKEY_STRUCTHASH = 34711 # 보낼때 필요
LOGIN_V4_STRUCTHASH = 61820 # 보낼때 필요
LOGIN_EX_STRUCTHASH = 2254 # 보낼때 필요
M_DATA_0111_STRUCTHASH = 7

#etc
COMMAND_LENGTH = 65535
CHECK_CODE = b'CK'

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
                      name, tel, part, position, business):
        '''
        로그인 패킷 만들때 명령어 뒷부분에 붙는 내용
        Struct_type : 구조체 종류 (unikey, v4, ex, v4nopw)
        '''
        strtype = struct_type.lower()
        
        payload = longToB(2)
        payload += usToB(len(sno)) + sno.encode()
        
        if struct_type == 'v4nopw':
            payload += usToB(0)
        else:
            payload += usToB(44) + encode_b64(get_hash_bytes(pw))
        
        payload += usToB(len(name)) + name.encode()
        payload += usToB(len(tel)) + tel.encode()
        payload += usToB(len(part)) + part.encode()
        payload += usToB(len(position)) + position.encode()
        payload += usToB(len(business)) + business.encode()
        payload += usToB(len(privip)) + privip.encode()
        
        if strtype in ('unikey', 'v4', 'v4nopw') :
            #unikey
            payload += usToB(64)
            # To do @jycho : Unikey 생성 방법 확인 후 작성 예정
            payload += b'87443DE767DDB0BEDD5D7EDE8B79A923490FF50FC0DA8D2513869BA73132D4C1'
            
            self.login_info = payload    
            if strtype == 'v4':
                #pw_sha256
                payload += usToB(44) + encode_b64(get_hash_bytes(pw))
                #pw_sha512
                payload += usToB(128)
                payload += ba.hexlify(get_hash_bytes(pw, algorithm='sha512'))
                #public ip
                payload += usToB(len(pubip)) + pubip.encode()
                #login_tool
                payload += longToB(0)
                self.logininfo = payload
            
            if strtype == 'v4nopw':
                payload += (longToB(0) * 2) + usToB(0)
                
        return payload
        
    def makeEnvUnikeyInfo(self, env_ip, mac_address, lan_count,
                          nat_version, com_name, cpu_info, mem_info,
                          ipaddr):
        payload = usToB(len(env_ip)) + env_ip.encode()
        payload += usToB(len(mac_address)) + mac_address.encode()
        payload += usToB(len(lan_count)) + lan_count.encode()
        payload += usToB(len(nat_version)) + nat_version.encode()
        payload += usToB(len(com_name)) + com_name.encode()
        payload += usToB(len(cpu_info)) + cpu_info.encode()
        payload += usToB(len(mem_info)) + mem_info.encode()
        payload += usToB(len(ipaddr)) + ipaddr.encode()
        payload += usToB(64) + b'87443DE767DDB0BEDD5D7EDE8B79A923490FF50FC0DA8D2513869BA73132D4C1'
        self.env_unikey_info = payload
        return payload

class OmsPktParser:
         
    def readPolicyRes(self, payload):
        policy_n_t = {}
        policy_n_t['num'] = []
        policy_n_t['title'] = []
        policy_n_t['exception'] = []
        policy_n_t['value'] = []
        pl = payload
        while True:
            startp = pl.find(b'\x00\x1b\xff\xff\xa9YCK')
            if startp > -1:
                pl = pl[8:]
                policy_n_t['num'].append(byteToNum(pl[0:4]))
                pl = pl[4:]
                policy_n_t['title'].append(pl[0:pl.find(b'\x00')])
                pl = pl[32:]
                policy_n_t['exception'].append(byteToNum(pl[0:4]))
                pl = pl[4:]
                policy_n_t['value'].append(pl[0:pl.find(b'\x00')])
                pl = pl[256:]
            else:
                break
        
        return policy_n_t
    
    def readMsg(self, payload):
        cmdlen = 8
        msglen = 2
        #msg 시작 지점
        msgsp = cmdlen + msglen
        plen = byteToNum(payload[cmdlen:msgsp])
        pvalue = payload[msgsp:msgsp+plen]
        try:
            pvalue = pvalue.decode()
        except Exception as e:
            pass
        return pvalue
            
    def readServiceRes(self, payload):
        payload = payload[8:]
        services = []
        while True:
            temp = self.readMsg(payload)
            services.append(temp)
            len_rm = len(temp) + 10
            if len(payload) > len_rm:
                payload = payload[len_rm:]
            else:
                break
        return len(services), services[0]
    
    def readPayload(self, payload):
        read_func_list = {
            usToB(VERSION_RET):self.readMsg,
            usToB(POLICY_RET):self.readPolicyRes,
            usToB(IP_CHECK_RET):self.readMsg,
            usToB(CERTID_NOT_LOGGED_IN):CERTID_NOT_LOGGED_IN,
            usToB(CERTID_LOGGED_IN):CERTID_LOGGED_IN,
            usToB(CERTID_LOGIN_ERR):CERTID_LOGIN_ERR,
            usToB(LOGIN_RET):LOGIN_RET,
            usToB(LOGIN_RET_SHA256):LOGIN_RET_SHA256,
            usToB(LOGIN_ERR):LOGIN_ERR,
            usToB(LOGIN_ERR_PASSWD):LOGIN_ERR_PASSWD,
            usToB(LOGIN_ERR_LOCK_TEMP):LOGIN_ERR_LOCK_TEMP,
            usToB(LOGIN_ERR_LOCK):LOGIN_ERR_LOCK,
            usToB(LOGIN_ERR_EXPIRY):LOGIN_ERR_EXPIRY,
            usToB(LOGIN_ERR_DOUBLE_ACCESS_DENY):
                LOGIN_ERR_DOUBLE_ACCESS_DENY,
            usToB(LOGIN_ERR_NOT_EXIST):LOGIN_ERR_NOT_EXIST,
            usToB(SAVE_ENV_RET):SAVE_ENV_RET,
            usToB(SAVE_ENV_ERR):SAVE_ENV_ERR,
            usToB(SERIAL_RET):self.readMsg,
            usToB(SERIAL_ERR):SERIAL_ERR,
            usToB(SERIAL_LOGOUT):SERIAL_LOGOUT,
            usToB(SERIAL_SAME_IP):SERIAL_SAME_IP,
            usToB(LOOPBACK_RET):LOOPBACK_RET,
            usToB(SERVICE_0111_START_RET):self.readServiceRes,
            usToB(SERVICE_0112_START_RET):self.readServiceRes,
            usToB(LOOPBACK_RET):LOOPBACK_RET,
            usToB(LOGOUT_RET):LOGOUT_RET,
            usToB(LOGOUT_ERR):LOGOUT_ERR
        }
        try:
            value = read_func_list[payload[0:2]]
        except Exception as e:
            return -1
        
        if type(value) in [int, str]:
            return value
        else:
            return value(payload)
       
class OmsPktSender:
    '''
    패킷을 전송하는 클래스
    '''
    # setConf() 실행여부 Flag
    conf_flag = False
        
    def __init__(self):
        self.maker = OmsPktMaker()
        self.parser = OmsPktParser()
        
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
        self.unikey = b'87443DE767DDB0BEDD5D7EDE8B79A923490FF50FC0DA8D2513869BA73132D4C1'
        self.conf_flag = True
        
    def connect(self):
        '''
        Make Connection to Target OMS_DMS
        
        @return
            socket
        '''
        AFTER_IDLE_SEC = 100
        INTERVAL_SEC = 100
        MAX_FAILS = 2
        sock = skt.socket(skt.AF_INET, skt.SOCK_STREAM)
        if pf.system().lower() == 'windows':
            sock.ioctl(skt.SIO_KEEPALIVE_VALS,(1,30000,3000))
        else:
            sock.setsockopt(skt.SOL_SOCKET, skt.SO_KEEPALIVE, 1)
            sock.setsockopt(skt.IPPROTO_TCP, skt.SO_KEEPALIVE, AFTER_IDLE_SEC)
            sock.setsockopt(skt.IPPROTO_TCP, skt.SO_KEEPALIVE, INTERVAL_SEC)
            sock.setsockopt(skt.IPPROTO_TCP, skt.SO_KEEPALIVE, MAX_FAILS)
        sock.settimeout(TIME_OUT_SEC)
        sock.connect((self.host, OMS_DMS_PORT))    
        return sock
    
    def sendPacket(self, step_num):
        funclist = [
                    [eval('self.makeVersionReq')],
                    
                    [eval('self.makeVersionReq'),
                     eval('self.makePolicyReq'),
                     eval('self.makeIPCheckReq'),],
                    
                    [eval('self.makeLoginUnikeyReq'),
                     eval('self.makeLoginReq'),
                     eval('self.makeSaveEnvReq')],
                    
                    [eval('self.makeSerialCheckReq'),
                     eval('self.makeServiceReq'),],
                    
                    [eval('self.makeLoopBackMsgReq')],
                    
                    [eval('self.makeLogoutReq')]
                   ]
        
        ret_data = []
        readpkt = self.parser.readPayload
        sock = self.connect()

        for func in funclist[step_num]:
            data = b''
            payload = func()
            sock.send(payload)
            
            while True:
                buf = sock.recv(MAX_RECV_SIZE)
                data += buf
                
                if func == self.makeServiceReq:
                    # 서비스 목록 Payload 뒷쪽에 DATA END 시그널이 있는지 확인
                    if buf[-8:] == b'\x01?\xff\xff\x00\x00CK' or b'' == buf:
                        break
        
                elif func == self.makePolicyReq:
                    # 정책 목록 Payload 뒷쪽에 DATA END 시그널이 있는지 확인
                    if  buf[-8:] == b'\x00\x1c\xff\xff\x00\x00CK' or b'' == buf:
                        break

                else:
                    # 0바이트거나 최대 받는 크기보다 작은 내용을 받았을 경우(1회성 Recv)            
                    if buf == b'' or len(buf) < MAX_RECV_SIZE:
                        break
                    
            temp = readpkt(data)
            ret_data.append(temp)
            
        sock.setsockopt(skt.SOL_SOCKET, skt.SO_LINGER, pack('ii', 1, 0))
        sock.close()
        return ret_data
    
    def makeVersionReq(self):
        payload = self.maker.makeCommandInfo(VERSION_REQ, 
                                                 COMMAND_LENGTH,
                                                 DEFAULT_STRUCTHASH,
                                                 CHECK_CODE)
        return payload
        
    def makePolicyReq(self):
        payload = self.maker.makeCommandInfo(POLICY_REQ,
                                                 COMMAND_LENGTH,
                                                 DEFAULT_STRUCTHASH,
                                                 CHECK_CODE)
        return payload
        
    def makeIPCheckReq(self):
        payload = self.maker.makeCommandInfo(IP_CHECK_REQ,
                                                 COMMAND_LENGTH,
                                                 DEFAULT_STRUCTHASH,
                                                 CHECK_CODE)
        return payload

    def makeLoginUnikeyReq(self):
        payload = self.maker.makeCommandInfo(LOGIN_UNIKEY_REQ,
                                             COMMAND_LENGTH,
                                             LOGIN_UNIKEY_STRUCTHASH,
                                             CHECK_CODE)
        payload += self.maker.makeLoginInfo('Unikey',
                                            self.sno,
                                            self.pw,
                                            self.privip,
                                            self.pubip,
                                            self.name,
                                            self.tel,
                                            self.part,
                                            self.position,
                                            self.business)
        return payload
        
    def makeLoginReq(self):
        payload = self.maker.makeCommandInfo(LOGIN_REQ,
                                             COMMAND_LENGTH,
                                             LOGIN_V4_STRUCTHASH,
                                             CHECK_CODE)
        payload += self.maker.makeLoginInfo('v4',
                                            self.sno,
                                            self.pw,
                                            self.privip,
                                            self.pubip,
                                            self.name,
                                            self.tel,
                                            self.part,
                                            self.position,
                                            self.business)
        return payload

    def makeSaveEnvReq(self):
        payload = self.maker.makeCommandInfo(SAVE_CLIENT_REQ,
                                            COMMAND_LENGTH,
                                            ENV_UNIKEY_STRUCTHASH,
                                            CHECK_CODE)
        payload += self.maker.makeEnvUnikeyInfo(self.envip,
                                                self.mac,
                                                self.nic,
                                                self.natver,
                                                self.comname,
                                                self.cpu,
                                                self.mem,
                                                self.ipaddr)
        return payload
        
    def makeSerialCheckReq(self):
        payload = self.maker.makeCommandInfo(CHECK_SERIAL_REQ,
                                            COMMAND_LENGTH,
                                            LOGIN_UNIKEY_STRUCTHASH,
                                            CHECK_CODE)
        payload += self.maker.makeLoginInfo('unikey',
                                            self.sno,
                                            self.pw,
                                            self.privip,
                                            self.pubip,
                                            self.name,
                                            self.tel,
                                            self.part,
                                            self.position,
                                            self.business)
        return payload
    
    def makeServiceReq(self, svcver='0112'):
        if '0111' == svcver:
            command = SERVICE0111_REQ
            struct_type = 'ex'
            struct_hash = LOGIN_EX_STRUCTHASH
        else:
            command = SERVICE0112_REQ
            struct_type = 'v4nopw'
            struct_hash = LOGIN_V4_STRUCTHASH
            
        payload = self.maker.makeCommandInfo(command,
                                             COMMAND_LENGTH,
                                             struct_hash,
                                             CHECK_CODE)
        payload += self.maker.makeLoginInfo(struct_type,
                                            self.sno,
                                            self.pw,
                                            self.privip,
                                            self.pubip,
                                            self.name,
                                            self.tel,
                                            self.part,
                                            self.position,
                                            self.business)
        return payload
                      
    def makeLoopBackMsgReq(self):
        payload = self.maker.makeCommandInfo(LOOPBACK_REQ,
                                             COMMAND_LENGTH,
                                             DEFAULT_STRUCTHASH,
                                             CHECK_CODE)
        return payload
                
    def makeLogoutReq(self):
        payload = self.maker.makeCommandInfo(LOGOUT_REQ,
                                             COMMAND_LENGTH,
                                             LOGIN_UNIKEY_STRUCTHASH,
                                             CHECK_CODE)
        payload += self.maker.makeLoginInfo('unikey', 
                                            self.sno,
                                            self.pw,
                                            self.privip,
                                            self.pubip,
                                            self.name,
                                            self.tel,
                                            self.part,
                                            self.position,
                                            self.business)
        return payload
    
    def makeAliveCheckReq(self):
        payload = self.maker.makeCommandInfo(ALIVE_CHECK_REQ,
                                             COMMAND_LENGTH,
                                             LOGIN_UNIKEY_STRUCTHASH,
                                             CHECK_CODE)
        return payload
                                                       

class OmsTestData:
    """
    OMS_DMS 테스트에 필요한 각종 설정
    테스트 주체 및 대상에 대한 정보를 수록
    Global Config
        
    Vuser Info
        Vuser Config
        Target Server IP
        Scenario and Expected result
    """
    def getConfFile(self):
        pass
    

def prepareTest():
    '''
    테스트 준비 함수
    설정 파일을 통해 내용을 가져와야 한다.
    '''
    # 서비스 리스트 
    pktsender = OmsPktSender()
    pktsender.setConf('192.168.4.200',
                      'trollking',
                      'dbsafer00',
                      '10.77.160.180',
                      '10.77.160.180',
                      '',
                      '',
                      '',
                      '',
                      '',
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
    '''
    실제 테스트 실행부
    '''
    for _ in range(1):
        ret = pkts.sendPacket(0)
        ret = pkts.sendPacket(1)
        ret = pkts.sendPacket(2)
        ret = pkts.sendPacket(3)
        ret = pkts.sendPacket(4)
        
def closeTest():
    pass

if __name__ == '__main__':
    pktsender = prepareTest()
    runTest(pktsender)