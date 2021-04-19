import os
import socket as skt
import multiprocessing as mp
import threading
from ipaddress import IPv4Network
from glob import glob
import binascii as ba
import platform as pf
import time
import psutil as pu
from commonlib import *

PERF_TESTER_CONF = 'omsconf/perf_tester.conf'
OMS_DMS_PORT = 50011
MAX_RECV_SIZE = 4192
TIME_OUT_SEC = 30
SCENARIO_COLS_MIN = 3
SCENARIO_COLS_MAX = 5

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
    
    def setConf(self, cert_id):
        self.cert_id = cert_id[0]
        self.cert_pw = cert_id[1]
        self.nic_name = cert_id[2]
        self.priv_ip = cert_id[3]
        self.public_ip = cert_id[4]
        self.target_host = cert_id[5]
        self.mac_addr = cert_id[6]
        self.com_name = cert_id[7]
        self.nat_version = cert_id[8]
        self.cpu_info = cert_id[9]
        self.mem_info = cert_id[10]
        self.nic_count = cert_id[11]
        self.user_name = ''
        self.tel = ''
        self.part = ''
        self.position = ''
        self.business = ''
        self.env_ip = str(self.priv_ip + ',' + self.public_ip)
        self.mac_addr = self.mac_addr
        self.ipaddr = self.priv_ip
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
        payload += usToB(len(self.cert_id)) + self.cert_id.encode()
        
        if struct_type == 'v4nopw':
            payload += usToB(0)
        else:
            payload += usToB(44) + encode_b64(get_hash_bytes(self.cert_pw))
        
        payload += usToB(len(self.user_name)) + self.user_name.encode()
        payload += usToB(len(self.tel)) + self.tel.encode()
        payload += usToB(len(self.part)) + self.part.encode()
        payload += usToB(len(self.position)) + self.position.encode()
        payload += usToB(len(self.business)) + self.business.encode()
        payload += usToB(len(self.priv_ip)) + self.priv_ip.encode()
        
        if strtype in ('unikey', 'v4', 'v4nopw') :
            #unikey
            payload += usToB(64)
            payload += self.unikey
                
            if strtype == 'v4':
                #pw_sha256
                payload += usToB(44) + encode_b64(get_hash_bytes(self.cert_pw))
                #pw_sha512
                payload += usToB(128)
                payload += ba.hexlify(get_hash_bytes(self.cert_pw, algorithm='sha512'))
                #public ip
                payload += usToB(len(self.public_ip)) + self.public_ip.encode()
                #login_tool
                payload += longToB(0)
            
            if strtype == 'v4nopw':
                payload += (longToB(0) * 2) + usToB(0)
                
        return payload
        
    def makeEnvUnikeyInfo(self):
        payload = usToB(len(self.env_ip)) + self.env_ip.encode()
        payload += usToB(len(self.mac_addr)) + self.mac_addr.encode()
        payload += usToB(len(self.nic_count)) + self.nic_count.encode()
        payload += usToB(len(self.nat_version)) + self.nat_version.encode()
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
                                       DEFAULT_STRUCTHASH,
                                       CHECK_CODE)
        return payload


class OmsPktParser:
    '''
    요청에 대한 응답값을 파싱하는 클래스
    '''
    
    def readPolicyRes(self, payload):      
        SIGN_EOF_POLICY_RES = b'\x00\x1b\xff\xff\xa9YCK'
        policy_n_t = {}
        policy_n_t['num'] = []
        policy_n_t['title'] = []
        policy_n_t['exception'] = []
        policy_n_t['value'] = []
        pl = payload
        while True:
            startp = pl.find(SIGN_EOF_POLICY_RES)
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
    
    def errorHandler(self, payload):
        print('Unknown Response Code : ', payload[0:8])
        f = open('unknown_error.bin','wb')
        f.write(payload)
        f.close()
        return 'Unknown Response Code'
                
    def readPayload(self, payload, parse_msg = False):
        '''
        @param
            payload : OMS_DMS에 요청했던 응답값(응답코드 + 메시지)
        @returns
            (응답 코드, payload길이, payload 해쉬, 
            메시지 또는 메시지가 없을 경우 Payload 원문)
        
        '''
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
            usToB(LOGOUT_ERR):LOGOUT_ERR,
            usToB(ALIVE_RET):ALIVE_RET,
            usToB(ALIVE_ERR):ALIVE_ERR,
            usToB(ALIVE_LOGOUT):ALIVE_LOGOUT,
            usToB(ALIVE_SAME_IP):ALIVE_SAME_IP,
            usToB(0):self.errorHandler,
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
            print('DEBUG# : ',e)
            return -1
        
        if type(read_func) == int:
            return (read_func, 
                    len(payload), 
                    get_hash(payload), 
                    payload)
        else:
            return (byteToNum(payload[0:2]), 
                    len(payload), 
                    get_hash(payload), 
                    read_func(payload))
       
class OmsTester:
    '''
    패킷을 쏘고 받는 클래스
    '''
    # shooter id
    shooter_id = None
    # Global status
    gconf = None
    # 처리할 보안계정 목록
    cert_id_list = None
    # 진행 시나리오 목록
    scenario = None
    # 예상 결과값(사전에 결과값을 저장하기 위해 사용)
    exp_data = {}
    # 슈터의 상태를 누적하기 위한 dictionary
    # [0] 평균 수행시간, [1] 수행 횟수, [2] 성공 횟수, [3] 실패 횟수
    cur_status = {}
    
    def __init__(self, seqnum, scen_path):
        self.maker = OmsPktMaker()
        self.parser = OmsPktParser()
        self.seqnum = seqnum
        self.scenario_name = os.path.basename(scen_path)
        self.shooter_id = (self.scenario_name.split('.')[0] 
                           + ' - Proc #' + str(self.seqnum))
        
    def setConf(self, gconf:dict = None, 
                cert_id_list:list = None, 
                scenario = None):
        
        if type(gconf) == dict:
            self.gconf = gconf

        if type(cert_id_list) == list:
            self.cert_id_list = cert_id_list
        
        if type(scenario) == list:
            self.scenario = scenario

        if None in [self.gconf, self.cert_id_list, self.scenario]:
            raise Exception('Not enough Configuration')

        self.scenario = []
        cols_types = [int, "\'self.maker.make\' + \'%s\'",
                      eval, str, int]
        
        for line in scenario:
            # 시나리오 컬럼이 필요한 최소 컬럼보다 작을 경우 무시함
            if len(line) < SCENARIO_COLS_MIN:
                continue
            
            # 임시 레코드 생성
            temp_col = ['' for i in range(SCENARIO_COLS_MAX)]
            
            for i, col in enumerate(line):
                if i == 1:
                    # 요청 코드별 상태값 초기화
                    # [0] 평균 수행시간, [1] 수행 횟수, [2] 성공 횟수, [3] 실패 횟수
                    col_text = str(eval((cols_types[i]%col)))
                    key_name = col_text.split('self.maker.make')[1]
                    if key_name not in self.cur_status:
                        self.cur_status[key_name] = [0.0, 0, 0, 0]

                    temp_col[i] = eval(col_text)
                else:
                    temp_col[i] = cols_types[i](col)                    
            self.scenario.append(temp_col)
            
        self.gconf['CONF']['start_after_deploy'] = (
            getBoolStr(self.gconf['CONF']['start_after_prepare']))
        
    def setVIP(self, nic_name, vip):
        ifcs = pu.net_if_addrs()
        if None == nic_name:
            nic_name = self.gconf['CONF']['nic_name'].lower()
        cur_nic_list = list(ifcs.keys())
        
        # 설정의 NIC 이름이 잘못된 값일 경우 예외 발생
        if nic_name not in cur_nic_list:
            raise Exception('%s Interface Not exist!'%nic_name)
                
        # 가상 IP 등록
        cidr = IPv4Network('0.0.0.0/' 
                           + ifcs[nic_name][0][2]).prefixlen
        cmd = 'ip addr add %s/%s dev %s 2> /dev/null'
        os.system(cmd%(vip, cidr, nic_name))
                
    def cleanUpVIP(self, vip, netmask, nic_name=None):
        if None == nic_name:
            nic_name = self.gconf['CONF']['nic_name'].lower()
        # 가상 IP 제거
        cmd = 'ip addr del %s/%s dev %s 2> /dev/null'
        os.system(cmd%(vip, netmask, nic_name))
            
    def connect(self, src_ip, nic, dst_ip, port=OMS_DMS_PORT):
        '''
        Make Connection to Target OMS_DMS
        
        @return
            socket
        '''
        AFTER_IDLE_SEC = 100
        INTERVAL_SEC = 100
        MAX_FAILS = 2
        self.setVIP(nic, src_ip)
        sock = skt.socket(skt.AF_INET, skt.SOCK_STREAM)
        sock.bind((src_ip,0))
        if pf.system().lower() == 'windows':
            sock.ioctl(skt.SIO_KEEPALIVE_VALS,(1,30000,3000))
        else:
            sock.setsockopt(skt.SOL_SOCKET, skt.SO_KEEPALIVE, 1)
            sock.setsockopt(skt.IPPROTO_TCP, skt.SO_KEEPALIVE, AFTER_IDLE_SEC)
            sock.setsockopt(skt.IPPROTO_TCP, skt.SO_KEEPALIVE, INTERVAL_SEC)
            sock.setsockopt(skt.IPPROTO_TCP, skt.SO_KEEPALIVE, MAX_FAILS)
        
        sock.setsockopt(skt.SOL_SOCKET, skt.SO_LINGER, pack('ii', 1, 0))
        nic_name = (nic+'\0').encode('utf8')
        sock.setsockopt(skt.SOL_SOCKET, skt.SO_BINDTODEVICE, nic_name)
        sock.settimeout(TIME_OUT_SEC)
        try:
            sock.connect((dst_ip, port))
        except Exception as e:
            print(e, src_ip, nic, dst_ip, port)
        
        return sock
    
    def parseCols(self, col):
        '''
        @return
            문자열 앞에 붙는 기호가
            변수명('%')일 경우 (변수명, None)
            경로명('@')일 경우 (None, 경로명)
            둘 다 있을 경우    (변수명, 경로명)
        '''
        path = None
        var = None
        pos_var = col.find('%')
        pos_path = col.find('@')
        
        if pos_var > -1 and pos_path > -1:
            # 경로가 먼저인 경우
            if pos_var > pos_path:
                col.strip('@ ')
                temp = col.split('%')
                path = temp[0].strip()
                var = temp[1].strip()
            # 변수가 먼저인 경우
            else:
                col.strip('% ')
                temp = col.split('@')
                var = temp[0].strip()
                path = temp[1].strip()
        elif pos_var > -1:
            var = col.strip('% ')
        elif pos_path > -1:
            path = col.strip('@ ')
        else:
            pass
        
        return (var, path)
    
    def saveExpResult(self, exp_ret_col, ret_value):
        ret = self.parseCols(exp_ret_col)
        #ret[0] = 예상결과를 저장할 key 이름
        #ret[1] = 예상 결과를 저장할 파일경로
        if None != ret[0]:
            self.exp_data[ret[0]] = ret_value
        
        if None != ret[1]:
            f = open(ret[1],'wb')
            f.write(ret_value)
            f.close()
    
    def verifyResData(self, exp_ret_row, ret_value):
        '''
        1. Ret 값 비교
        2. payload hash 비교
        '''
        RET_DATA_SIZE = 6
        RES_RET = 0
        HASH_RET = 1
        FILE_RET = 2
        RES_ERR = 3
        HASH_ERR = 4
        FILE_ERR = 5
        ret_data = [None for i in range(RET_DATA_SIZE)]

        # 기대 값 컬럼 파싱
        ret_data[RES_RET] = (int(ret_value[0]) == 
                             int(exp_ret_row[2]))
        
        if ret_data[RES_RET] == False:    
                ret_data[RES_ERR] = (int(ret_value[0]),
                                     int(exp_ret_row[2]))
        
        if ((exp_ret_row[3].find('%') == -1 and 
            exp_ret_row[3].find('@') == -1) or 
            exp_ret_row[3] == ''):
        
            return ret_data 
        
        tmp = self.parseCols(exp_ret_row[3])
        var = tmp[0]
        path = tmp[1]
        
        if None != var:
            ret_data[HASH_RET] = (get_hash(self.exp_data[var])
                                == ret_value[2])
            if ret_data[HASH_RET] == False:
                ret_data[HASH_ERR] = (get_hash(self.exp_data[var]),
                                      ret_value[2])
                
        if None != path:
            # 검증 파일 읽기
            f = open(path, 'rb')
            buf = f.read()
            f.close()
            
            # 파일 내용과 결과와 비교
            ret_data[FILE_RET] = (buf == ret_value[3])
            if ret_data[FILE_RET] == False:
                ret_data[FILE_ERR] = (buf, ret_value[3])
        
        return ret_data
    
    def recvResponse(self, sock, step):
        '''
        요청에 대한 응답값과 메시지를 받는 함수
        @params
            sock : 응답값을 받을 소켓
            step : 시나리오의 스탭 레코드
        @returns
            (응답 코드, payload길이, payload 해쉬, 메시지)
        '''
        res = b''
        
        while True:
            SIGN_EOF_SERVICE_RES = b'\x01?\xff\xff\x00\x00CK'
            SIGN_EOF_POLICY_RES = b'\x00\x1c\xff\xff\x00\x00CK'
            buf = sock.recv(MAX_RECV_SIZE)
            res += buf
            
            if step[1] in (self.maker.makeService0111Req,
                           self.maker.makeService0112Req):
                # 서비스 목록 Payload 뒷쪽에 DATA END 시그널이 있는지 확인
                if buf[-8:] == SIGN_EOF_SERVICE_RES or b'' == buf:
                    break
                
            elif step[1] == self.maker.makePolicyReq:
                # 정책 목록 Payload 뒷쪽에 DATA END 시그널이 있는지 확인
                if buf[-8:] == SIGN_EOF_POLICY_RES or b'' == buf:
                    break
                
            else:
                # 0바이트거나 최대 받는 크기보다 작은 내용을 받았을 경우(1회성 Recv)
                if buf == b'' or len(buf) < MAX_RECV_SIZE:
                    break
        
        if b'' == res:
            print("No data")
            return -1

        # 파싱된 응답값
        ret = self.parser.readPayload(res, parse_msg=False)
        return ret
    
    def runScenario(self, cert, resq:mp.Queue, signal:mp.Value,
                    prepare_mode = False):
        sock = None
        cur_session = -1
        
        # 시나리오 시작
        for step in self.scenario:
            # 보안계정관련 정보 설정
            self.maker.setConf(cert)

            # 시나리오에서 추가 옵션 처리 부분
            if len(step) > SCENARIO_COLS_MAX:
                for line in step[SCENARIO_COLS_MAX:len(step)]:
                    if line.find('=') > -1:
                        tmp = line.split('=')
                        key = tmp[0].split('.')
                        value = tmp[1].strip()
                        grp = key[0].strip()
                        name = key[1].lower().strip()
                        self.gconf[grp][name] = value
                self.setConf()
            
            # 현재 세션을 유지할지 확인
            if int(step[0]) > cur_session:
                if None != sock:
                    sock.close()
                sock = self.connect(cert[4], cert[2], cert[5])
                cur_session = int(step[0])        
            
            stime = time.time()
            # 패킷 작성 후 전송
            payload = step[1]()
            sock.send(payload)
            
            # 응답 수신
            res = self.recvResponse(sock, step)
            if res[3] == 'Unknown Response Code':
                print(self.scenario_name, cert[0], step[1], payload)
            
            # 시간 측정
            cur_runtime = time.time() - stime
            
            # res값을 검증할지 저장할지 결정
            if False == prepare_mode:
                result = self.verifyResData(step, res)
                key_name = str(step[1]).split(' ')[2].split('.make')[1]

                # 수행 횟수 증가
                self.cur_status[key_name][1] += 1
                
                if False in result[0:3]:
                    # 실패 횟수 증가
                    self.cur_status[key_name][3] += 1
                    print('[%s][%s][%s] %s'
                          %(self.shooter_id,
                            step[0],
                            key_name,
                            str(result[:])))
                else:
                    pre_avg_runtime = self.cur_status[key_name][0]
                    hit_times = self.cur_status[key_name][2]
                    
                    if (pre_avg_runtime == 0 or
                        hit_times == 0):
                        self.cur_status[key_name][0] = cur_runtime
                    else:
                    # 평균시간 계산 ((기존 평균 * 성공횟수) + 현재 수행시간) / 성공 횟수+1
                        self.cur_status[key_name][0] = (
                        ((pre_avg_runtime * hit_times) + cur_runtime)
                        /(hit_times + 1))
                    
                    # 성공 횟수 증가
                    self.cur_status[key_name][2] += 1
                
                # 중간 결과 전달
                resq.put((self.shooter_id,'itmres',self.cur_status))
                
                if signal == 2:
                    while True:
                        time.sleep(1)
                if signal == 3:
                    return -3
                # 지연
                try:
                    time.sleep(int(step[4]))
                except:
                    pass
            else:
                self.saveExpResult(step[3], res[3])
        
        # 최종결과 리턴
        resq.put((self.shooter_id, 'endres', self.cur_status))
        
    def runTest(self, resq:mp.Queue, signal:mp.Value):
        '''
        @param
            resq : 중간 및 최종결과를 부모 프로세스에 전달하기 위한 큐
                ready : 준비 단계가 끝난 시그널
                error : 테스트 중 에러 발생 시그널
                itmres : 테스트 중간 결과 시그널
                endres : 테스트 종료 및 최종 결과 시그널
            signal : 부모 -> 자식 테스트 시그널 전달용 공유 메모리
                0 : 프로세스 시작시 기본 값
                1 : 테스트 수행
                2 : 테스트 일시 정지
                3 : 테스트 강제 종료
        '''
    
        # 보안계정 목록 순서대로 진행
        for i, cert in enumerate(self.cert_id_list):
            # 시나리오를 한번 실행해서 예상 결과 저장
            thread = threading.Thread(target = self.runScenario,
                                      args = (cert, resq, signal, True,))
            thread.start()
            #self.runScenario(cert, resq, signal, True)
            
        if 0 == int(signal.value):
            resq.put((self.shooter_id, 'ready'))
            
            while True:
                if int(signal.value) > 0:
                    break
                time.sleep(1)
                
        for _ in range(int(self.gconf['CONF']['repeat_count'])):
            for cert in self.cert_id_list:           
                # 시나리오 시작
                thread = threading.Thread(target = self.runScenario,
                                          args = (cert, resq, signal, False,))
                thread.start()
                #self.runScenario(cert, resq, signal, True)
                        
def setShooters():
    """
    실제 테스트를 수행하는 주체 프로세스를 생성함
    테스트 주체 및 대상에 대한 정보를 수록
    Global Config : perf_tester.conf
        
    Vuser Info
        vuser id
        Vuser Config
        Scenario
    """
    shooters = []
    gconf = get_file_conf(PERF_TESTER_CONF)
    cert_id_list = get_list_from_csv(gconf['CONF']['cert_id_csv'])
    scen_list = glob(gconf['CONF']['scenario_csvs'])
    scen_list.sort()
    proc_count = int(gconf['CONF']['proc_count'])
    
    # 보안계정 목록 분배
    cnt_per_scen = int(len(cert_id_list) / (len(scen_list) * proc_count))
    dist_cert_ids = divList(cert_id_list, cnt_per_scen)
    
    for i, scen_path in enumerate(scen_list):
        for rep in range(proc_count):
            shooter_idx = (i * proc_count) + rep
            
            # 슈터 객체 생성
            shooter = OmsTester(shooter_idx, scen_path)
        
            # 시나리오 파일 세팅하기
            scenario = get_list_from_csv(scen_path)
            
            # 슈터에 설정 내용 세팅
            shooter.setConf(gconf, dist_cert_ids[shooter_idx], scenario)
            shooters.append(shooter)
            
    return shooters

def runShooters(shooters):
    '''
    실제 테스트 실행부
    '''
    # 결과 전달용 큐 (자식 -> 부모)
    resq = mp.Queue()
    # 신호 전달용 공유메모리 (부모 -> 자식)
    signal = mp.Value('d', 0)
    
    start_after_prepare = (
        getBoolStr(shooters[0].gconf['CONF']['start_after_prepare']))
    
    if start_after_prepare == False:
        signal.value = 1
    
    procs = []
    procs_ready = []
    cur_procs_stats = {}
    procs_finish = []
    result = []
    
    # Create Processes
    for shooter in shooters:
        proc = mp.Process(target=shooter.runTest,
                          args=(resq, signal,))
        proc.start()
        procs.append(proc)
    procs_cnt = len(procs)
    
    # Getting all kinds of data from child processes  
    while True:
        # Getting status from process
        if resq.empty() == False:
            buf = resq.get(block = False, timeout = 5)
            if 'ready' == buf[1] and int(signal.value) == 0:
                procs_ready.append(buf[0])
                
                if len(procs_ready) == procs_cnt:
                    signal.value = 1
                    print("%s Processes are start to run"
                          %len(procs_ready))
            
            if 'error' == buf[1]:
                procs_cnt -= 1
                print('Error occured on #%s Process')
            
            if 'itmres' == buf[1]:
                cur_procs_stats[buf[0]] = buf[2]
                printStatus(cur_procs_stats)
                        
            if 'endres' == buf[1]:
                procs_finish.append(buf[0])
                #result.append((buf[0],buf[2]))
                if len(procs_finish) == procs_cnt:
                    signal.value = 3
                    printStatus(cur_procs_stats)
                    break

            time.sleep(1)
            
    for proc in procs:
        proc.join()
        
    return result

def printStatus(procs_stats):
    tables = []
    result_header = ['Request Code', 'Average RunTime', 'Run Count', 
                     'Success Count', 'Failure Count']
    for key in procs_stats:
        table = []
        for code in procs_stats[key]:
            row = []
            row.append(code)
            row.append(procs_stats[key][code][0])
            row.append(procs_stats[key][code][1])
            row.append(procs_stats[key][code][2])
            row.append(procs_stats[key][code][3])
            table.append(row)
        tables.append((key, table))

    os.system('clear')

    print('[Current Processes status]')

    for table in tables:
        print('\n[ %s ]'%table[0])
        printTable(table[1], result_header)

def showTotalResult(result):
    print(result)
    pass

if __name__ == '__main__':
    
    shooters = setShooters()
    result = runShooters(shooters)