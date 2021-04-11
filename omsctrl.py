import os
import socket as skt
import multiprocessing as mp
import binascii as ba
import platform as pf
import time
import psutil as pu
from commonlib import *

OMS_DMS_PORT = 50011
MAX_RECV_SIZE = 4192
TIME_OUT_SEC = 30
VUSER_LIST_COLS_MIN = 3
SCENARIO_COLS_MIN = 7


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
    def setConf(self, conf):
        self.host = conf['DBSAFER']['gw']
        cert_id_pw = conf['OMSDMS']['cert_id_pw'].split() 
        self.sno = cert_id_pw[0]
        self.pw = cert_id_pw[1]
        self.privip = conf['Common']['vuser_ip']
        self.pubip = conf['OMSDMS']['public_ip']
        self.name = conf['OMSDMS']['user_name']
        self.tel = conf['OMSDMS']['tel']
        self.part = conf['OMSDMS']['part']
        self.position = conf['OMSDMS']['position']
        self.business = conf['OMSDMS']['business']
        self.env_ip = conf['OMSDMS']['env_ip']
        self.mac_addr = conf['OMSDMS']['mac_addr']
        self.nic_count = conf['OMSDMS']['nic_count']
        self.nat_ver = conf['OMSDMS']['nat_version']
        self.com_name = conf['OMSDMS']['com_name']
        self.cpu_info = conf['OMSDMS']['cpu_info']
        self.mem_info = conf['OMSDMS']['mem_info']
        self.ipaddr = self.privip
        self.unikey = self.makeUnikey()
    
    def makeUnikey(self):
        ASSIST_UNIQUE_NAME='DSASSIST'
        SESSION_ID = 123
        assist_key = '%s%s%s_%lu'%(ASSIST_UNIQUE_NAME,
                                   self.com_name,
                                   self.mac_addr,
                                   SESSION_ID)
        return get_hash(assist_key).upper().encode()
        
    
    def makeCommandInfo(self, cmd, length, structhash, checkcode):
        '''
        OMS_DMS 명령어 부분 만드는 함수
        '''
        payload = usToB(cmd)
        payload += usToB(length)
        payload += usToB(structhash)
        payload += checkcode
        return payload

    def makeLoginInfo(self, struct_type):
        '''
        로그인 패킷 만들때 명령어 뒷부분에 붙는 내용
        Struct_type : 구조체 종류 (unikey, v4, ex, v4nopw)
        '''
        strtype = struct_type.lower()
        payload = longToB(2)
        payload += usToB(len(self.sno)) + self.sno.encode()
        
        if struct_type == 'v4nopw':
            payload += usToB(0)
        else:
            payload += usToB(44) + encode_b64(get_hash_bytes(self.pw))
        
        payload += usToB(len(self.name)) + self.name.encode()
        payload += usToB(len(self.tel)) + self.tel.encode()
        payload += usToB(len(self.part)) + self.part.encode()
        payload += usToB(len(self.position)) + self.position.encode()
        payload += usToB(len(self.business)) + self.business.encode()
        payload += usToB(len(self.privip)) + self.privip.encode()
        
        if strtype in ('unikey', 'v4', 'v4nopw') :
            #unikey
            payload += usToB(64)
            payload += self.unikey
                
            if strtype == 'v4':
                #pw_sha256
                payload += usToB(44) + encode_b64(get_hash_bytes(self.pw))
                #pw_sha512
                payload += usToB(128)
                payload += ba.hexlify(get_hash_bytes(self.pw, algorithm='sha512'))
                #public ip
                payload += usToB(len(self.pubip)) + self.pubip.encode()
                #login_tool
                payload += longToB(0)
            
            if strtype == 'v4nopw':
                payload += (longToB(0) * 2) + usToB(0)
                
        return payload
        
    def makeEnvUnikeyInfo(self):
        payload = usToB(len(self.env_ip)) + self.env_ip.encode()
        payload += usToB(len(self.mac_addr)) + self.mac_addr.encode()
        payload += usToB(len(self.nic_count)) + self.nic_count.encode()
        payload += usToB(len(self.nat_ver)) + self.nat_ver.encode()
        payload += usToB(len(self.com_name)) + self.com_name.encode()
        payload += usToB(len(self.cpu_info)) + self.cpu_info.encode()
        payload += usToB(len(self.mem_info)) + self.mem_info.encode()
        payload += usToB(len(self.ipaddr)) + self.ipaddr.encode()
        payload += usToB(64) + self.unikey
        return payload
    
    def makeVersionReq(self):
        payload = self.makeCommandInfo(VERSION_REQ, 
                                       COMMAND_LENGTH,
                                       DEFAULT_STRUCTHASH,
                                       CHECK_CODE)
        return payload
        
    def makePolicyReq(self):
        payload = self.makeCommandInfo(POLICY_REQ,
                                       COMMAND_LENGTH,
                                       DEFAULT_STRUCTHASH,
                                       CHECK_CODE)
        return payload
        
    def makeIPCheckReq(self):
        payload = self.makeCommandInfo(IP_CHECK_REQ,
                                       COMMAND_LENGTH,
                                       DEFAULT_STRUCTHASH,
                                       CHECK_CODE)
        return payload

    def makeLoginUnikeyReq(self):
        payload = self.makeCommandInfo(LOGIN_UNIKEY_REQ,
                                       COMMAND_LENGTH,
                                       LOGIN_UNIKEY_STRUCTHASH,
                                       CHECK_CODE)
        payload += self.makeLoginInfo('Unikey')
        return payload
        
    def makeLoginReq(self):
        payload = self.makeCommandInfo(LOGIN_REQ,
                                       COMMAND_LENGTH,
                                       LOGIN_V4_STRUCTHASH,
                                       CHECK_CODE)
        payload += self.makeLoginInfo('v4')
        return payload

    def makeSaveEnvReq(self):
        payload = self.makeCommandInfo(SAVE_CLIENT_REQ,
                                       COMMAND_LENGTH,
                                       ENV_UNIKEY_STRUCTHASH,
                                       CHECK_CODE)
        payload += self.makeEnvUnikeyInfo()
        return payload
        
    def makeSerialCheckReq(self):
        payload = self.makeCommandInfo(CHECK_SERIAL_REQ,
                                       COMMAND_LENGTH,
                                       LOGIN_UNIKEY_STRUCTHASH,
                                       CHECK_CODE)
        payload += self.makeLoginInfo('unikey')
        return payload

    def makeService0111Req(self):
        payload = self.makeCommandInfo(SERVICE0111_REQ,
                                       COMMAND_LENGTH,
                                       LOGIN_EX_STRUCTHASH,
                                       CHECK_CODE)
        payload += self.makeLoginInfo('ex')
    
    def makeService0112Req(self):    
        payload = self.makeCommandInfo(SERVICE0112_REQ,
                                       COMMAND_LENGTH,
                                       LOGIN_V4_STRUCTHASH,
                                       CHECK_CODE)
        payload += self.makeLoginInfo('v4nopw')
        return payload
                      
    def makeLoopBackMsgReq(self):
        payload = self.makeCommandInfo(LOOPBACK_REQ,
                                       COMMAND_LENGTH,
                                       DEFAULT_STRUCTHASH,
                                       CHECK_CODE)
        return payload
                
    def makeLogoutReq(self):
        payload = self.makeCommandInfo(LOGOUT_REQ,
                                       COMMAND_LENGTH,
                                       LOGIN_UNIKEY_STRUCTHASH,
                                       CHECK_CODE)
        payload += self.makeLoginInfo('unikey')
        return payload
    
    def makeAliveCheckReq(self):
        payload = self.makeCommandInfo(ALIVE_CHECK_REQ,
                                       COMMAND_LENGTH,
                                       LOGIN_UNIKEY_STRUCTHASH,
                                       CHECK_CODE)
        return payload


class OmsPktParser:
    '''
    요청에 대한 응답값을 파싱하는 클래스
    '''
    
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
        message = payload[msgsp:msgsp+plen]
        
        try:
            message = message.decode()
        except Exception as e:
            pass
       
        return message
            
    def readServiceRes(self, payload):
        pl = payload[8:]
        services = []
        
        while True:
            temp = self.readMsg(pl)
            services.append(temp)
            len_rm = len(temp) + 10
            
            if len(pl) > len_rm:
                pl = pl[len_rm:]
            else:
                break
        message = payload[10:]
        
        return message
                
    
    def readPayload(self, payload, parse_msg = False):
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
        if False == parse_msg:
            read_func_list[usToB(VERSION_RET)] = VERSION_RET
            read_func_list[usToB(POLICY_RET)] = POLICY_RET
            read_func_list[usToB(IP_CHECK_RET)] = IP_CHECK_RET
            read_func_list[usToB(SERIAL_RET)] = SERIAL_RET
            read_func_list[usToB(SERVICE_0111_START_RET)] = SERVICE_0111_START_RET
            read_func_list[usToB(SERVICE_0112_START_RET)] = SERVICE_0112_START_RET
        
        try:
            read_func = read_func_list[payload[0:2]]
        except Exception as e:
            return -1
        
        if type(read_func) == int:
            return (read_func, 
                    len(payload), 
                    get_hash(payload), 
                    payload)
        else:
            return (payload[0:2], 
                    len(payload), 
                    get_hash(payload), 
                    read_func(payload))
       
class OmsTester:
    '''
    패킷을 쏘고 받는 클래스
    '''
    uid = None
    conf = None
    scenario = None
    vnic = None
    exp_data = {}
    
    def __init__(self):
        self.maker = OmsPktMaker()
        self.parser = OmsPktParser()
        
    def setVIP(self):
        ifcs = pu.net_if_addrs()
        vuser_nic = self.conf['Common']['vuser_nic'].lower()
        vuser_ip = self.conf['Common']['vuser_ip'].lower()
        netmask = self.conf['Common']['vuser_netmask'].lower()
        cur_nic_list = list(ifcs.keys())
        # 설정의 VUSER_NIC가 잘못된 값일 경우 예외 발생

        if vuser_nic not in cur_nic_list:
            raise Exception('%s Interface Not exist!'%vuser_nic)
        
        # IP가 등록되어 있는지 확인
        for nic in cur_nic_list:
            if ifcs[nic][0][1] == vuser_ip:
                self.vnic = nic
                return self.vnic
        
        # 가상 IP 등록
        cmd = 'ifconfig %s %s netmask %s up'
        for i in range(65536):
            vnic = vuser_nic + ':' + str(i)
            if vnic not in cur_nic_list:
                if 0 != os.system(cmd%(vnic, vuser_ip, netmask)):
                    raise Exception('Failed to add VIP!')
                self.vnic = vnic
                return self.vnic
                
    def cleanUpVIP(self):
        # 가상 IP 제거
        cmd = 'ifconfig %s down'
        if 0 != os.system(cmd%self.vnic):
            raise Exception("Failed to remove VIP")
        self.vnic == None
        
    def setConf(self, uid = None, conf:dict = None, scenario:list = None):
        if None == self.uid:
            if str != type(uid):
                raise Exception('Wrong vuserID')
            self.uid = uid
        
        if None == self.conf and dict != type(conf):
            raise Exception('Config Dict needed')
        if dict == type(conf):
            self.conf = conf
            
        if None == self.scenario and list != type(scenario):
            raise Exception('Scenario List needed')

        if list == type(scenario):
            self.scenario = []    
            for line in scenario:
                temp_col = []
                for i,col in enumerate(line):
                    if i == 0:
                        temp_col.append(int(col))
                        continue
                    if i == 1:
                        temp_col.append(eval(('self.maker.make' + col)))
                        continue
                    if i == 2:
                        temp_col.append(int(col))
                        continue
                    if i == 3:
                        temp_col.append(eval(col))
                        continue
                    temp_col.append(col)
                if len(temp_col) < SCENARIO_COLS_MIN:
                    temp_col += ['' for i in range(SCENARIO_COLS_MIN - len(temp_col))]
                self.scenario.append(temp_col)
            
        self.host = self.conf['DBSAFER']['gw']
        
        self.maker.setConf(conf)
        
        if self.vnic != None:
            self.cleanUpVIP()
        self.setVIP()
            
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
        sock.setsockopt(skt.SOL_SOCKET, skt.SO_LINGER, pack('ii', 1, 0))
        nic_name = (self.conf['Common']['vuser_nic']+'\0').encode('utf8')
        sock.setsockopt(skt.SOL_SOCKET, skt.SO_BINDTODEVICE, nic_name)
        sock.settimeout(TIME_OUT_SEC)
        sock.connect((self.host, OMS_DMS_PORT))
        return sock
    
    def getExpectedResult(self, ex_ref, ex_result):
        ex_path = None
        ex_var = None
        pos_var = ex_ref.find('%')
        pos_path = ex_ref.find('@')
        
        if pos_var > -1 and pos_path > -1:
            # 경로가 먼저인 경우
            if pos_var > pos_path:
                ex_ref.strip('@ ')
                temp = ex_ref.split('%')
                ex_path = temp[0].strip()
                ex_var = temp[1].strip()
            # 변수가 먼저인 경우
            else:
                ex_ref.strip('% ')
                temp = ex_ref.split('@')
                ex_var = temp[0].strip()
                ex_path = temp[1].strip()
        elif pos_var > -1:
            ex_var = ex_ref.strip('% ')
        elif pos_path > -1:
            ex_path = ex_ref.strip('@ ')
        else:
            pass
        
        if None != ex_path:
            f = open(ex_path,'wb')
            f.write(ex_result)
            f.close()
        
        if None != ex_var:
            self.exp_data[ex_var] = ex_result
    
    def verifyResData(self, origin, ret):
        result = 'ChkResCode : %s'%str(ret[0] == origin[3])
        print(result, ret[0], origin[3])
    
    def runTest(self, prepare=False):
        sock = None
        cur_session = -1
        pktparser = self.parser.readPayload
        
        for step in self.scenario:
            if int(step[0]) > cur_session:
                if None != sock:
                    sock.close()
                sock = self.connect()
                cur_session = int(step[0])        
            
            data = b''
            payload = step[1]()
            stime = time.time()
            sock.send(payload)
            
            while True:
                buf = sock.recv(MAX_RECV_SIZE)
                data += buf
                
                if step[1] in (self.maker.makeService0111Req,
                               self.maker.makeService0112Req):
                    # 서비스 목록 Payload 뒷쪽에 DATA END 시그널이 있는지 확인
                    if buf[-8:] == b'\x01?\xff\xff\x00\x00CK' or b'' == buf:
                        break
                    
                elif step[1] == self.maker.makePolicyReq:
                    # 정책 목록 Payload 뒷쪽에 DATA END 시그널이 있는지 확인
                    if  buf[-8:] == b'\x00\x1c\xff\xff\x00\x00CK' or b'' == buf:
                        break
                    
                else:
                    # 0바이트거나 최대 받는 크기보다 작은 내용을 받았을 경우(1회성 Recv)
                    if buf == b'' or len(buf) < MAX_RECV_SIZE:
                        break
            
            # 파싱된 응답값
            ret = pktparser(data, parse_msg=False)
            print(str(step[1]).split()[2], time.time() - stime)
            
            # result값을 검증할지 저장할지 결정
            if False == prepare:
                self.verifyResData(step, ret)
                
                pass
            else:
                self.getExpectedResult(step[4], ret[3])
                    
                    
def makeVusers(vuser_list_csv):
    """
    OMS_DMS 테스트에 필요한 각종 설정
    테스트 주체 및 대상에 대한 정보를 수록
    Global Config
        
    Vuser Info
        vuser id
        Vuser Config
        Scenario
    """
    vusers = []
    
    for line in get_list_from_csv(vuser_list_csv):
        vuser = OmsTester()
        vuserid = line[0]
        conf = get_file_conf(line[1])
        scenario = get_list_from_csv(line[2])
        if len(line) > VUSER_LIST_COLS_MIN:
            for i in range(VUSER_LIST_COLS_MIN, len(line)):
                if '' != line[i]:
                    temp = line[i].split('=')
                    key = temp[0].split('.')
                    grp = key[0].strip()
                    name = key[1].strip().lower()
                    conf[grp][name] = temp[1].strip()
        vuser.setConf(vuserid, conf, scenario)
        vusers.append(vuser)
        
    return vusers

def runTest(vusers):
    '''
    실제 테스트 실행부
    '''
    
    procs = []
    for vuser in vusers:
        proc = mp.Process(target=vuser.runTest, args=(True,))
        proc.start()
        procs.append(proc)
    
    for proc in procs:
        proc.join()
        
    procs = []
    for vuser in vusers:
        proc = mp.Process(target=vuser.runTest, args=(False,))
        proc.start()
        procs.append(proc)
    
    for proc in procs:
        proc.join()


def closeTest():
    pass

if __name__ == '__main__':
    # 준비과정에서 저거... NIC에 가상 IP 추가 내용 들어가줘야 됨 
    vusers = makeVusers('omsconf/vuser_list.csv')
    result = runTest(vusers)