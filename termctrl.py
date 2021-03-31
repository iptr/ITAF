import os
import time
from struct import pack
from ipaddress import IPv4Address
import socket as skt
import telnetlib as tl
import ftplib as fl
import paramiko as pm
from taiflogger import *
from dbctrl import *
from commonlib import *

class NatIdPkt:
    """
    DBSAFER 사용자 식별을 위한 패킷 구조 class
    """
    idcode = b'NATIDENTITY'
    pktver = pack('>H',1)
    totlen = pack('>H',0)
    encrypt = pack('>B',0)
    svctype = pack('>I',4)
    rdplog = pack('>I',0)
    svcnum = pack('>I',0)
    localip = b''
    localport = b''
    targetip = b''
    targetport = b''
    gwip = IPv4Address('0.0.0.0').packed
    gwport = pack('>H',0)
    cert_id_len = pack('>H',9)  
    cert_id = b'trollking'
    proglen = pack('>H',11)
    progname = b'trolltester'
    assistkeylen = pack('>H',0)
    assistkey = b''
    proghashlen = pack('>H',0)
    proghash = b''
    webassist = pack('>I',0)
    ostype = pack('>H',0)
    msgtunnel = pack('>H',0)
    payload = b''

    def __init__(self):
        pass

    def set(self, svcnum=b'', tgip=b'', tgport=b'', gwip=b'', 
            gwport=b'', cert_id=b'', loip=b'', loport=b''):
        """사용자 식별 기능을 사용하기 위해 패킷의 데이터를 입력한다.
        모든 파라메터는 옵션이며 입력되지 않을 경우 디폴트 값을 사용한다
        
        Args:
            svcnum (bytes, optional): DBSAFER의 서비스 번호. Defaults to b''.
            tgip (bytes, optional): 대상서버의 IP주소. Defaults to b''.
            tgport (bytes, optional): 대상서버의 포트번호. Defaults to b''.
            gwip (bytes, optional): DBSAFER GATEWAY IP주소. Defaults to b''.
            gwport (bytes, optional): DBSAFER GATEWAY Port. Defaults to b''.
            cert_id (bytes, optional): DBSAFER 보안계정. Defaults to b''.
            loip (bytes, optional): 세션IP(로컬IP). Defaults to b''.
            loport (bytes, optional): 세션Port(로컬Port). Defaults to b''.
        """
        # 필수정보 교체: 대상서비스번호, 대상IP, port, 로컬IP, 로컬port, dbsIP, dbsport, 
        #               보안계정)
        if loip != b'':
            self.localip = IPv4Address(loip).packed
        if loport != b'':
            self.localport = pack('>H',loport)
        if svcnum != b'':
            self.svcnum = pack('>I',int(svcnum))
        if tgip != b'':
            self.targetip = IPv4Address(tgip).packed 
        if tgport != b'':
            self.targetport = pack('>H',int(tgport))
        if gwip != b'':
            self.gwip = IPv4Address(gwip).packed
        if gwport != b'':
            self.gwport = pack('>H',int(gwport))
        if cert_id != b'':
            try:
                self.cert_id = cert_id.encode()
            except Exception as e:
                print('debug : %s, %s'%(e,cert_id))
        self.assistkey = get_hash('TrollkingTester').encode()
        # 가변 길이 입력
        self.cert_id_len = pack('>H',len(self.cert_id))
        self.assistkeylen = pack('>H',len(self.assistkey))

        # 전체 길이 계산(encrypt ~ 끝까지)
        payload = self.encrypt + self.svctype + self.rdplog + self.svcnum
        payload += self.localip + self.localport + self.targetip + self.targetport
        payload += self.gwip + self.gwport + self.cert_id_len + self.cert_id
        payload += self.proglen + self.progname + self.assistkeylen + self.assistkey
        payload += self.proghashlen + self.proghash + self.webassist + self.ostype + self.msgtunnel
        self.totlen = pack('>H', len(payload))
        self.payload = self.idcode + self.pktver + self.totlen + payload

    def show_payload(self):
        """디버깅용 패킷 출력 함수
        """
        print("idcode : ",self.idcode)
        print("pktver : ",self.pktver)
        print("totlen : ",self.totlen)
        print("encryp : ",self.encrypt)
        print("svctyp : ",self.svctype)
        print("rdplog : ",self.rdplog)
        print("svcnum : ",self.svcnum)
        print("loc_ip : ",self.localip)
        print("loPort : ",self.localport)
        print("tg  IP : ",self.targetip)
        print("tgPort : ",self.targetport)
        print("gw  IP : ",self.gwip)
        print("gwPort : ",self.gwport)
        print("Crtlen : ",self.cert_id_len)
        print("CertID : ",self.cert_id)
        print("Prolen : ",self.proglen)
        print("pronam : ",self.progname)
        print("keylen : ",self.assistkeylen)
        print("unikey : ",self.assistkey)
        print("phshln : ",self.proghashlen)
        print("prhash : ",self.proghash)
        print("webass : ",self.webassist)
        print("ostype : ",self.ostype)
        print("msgtur : ",self.msgtunnel)

    def tosegment(self, rawdata):
        """Wireshark에서 수집된 Hex Binary bytes를 입력받아서
        사용자 식별 패킷 형태로 값들을 출력하는 디버깅용 함수

        Args:
            rawdata (str): [description]
        """
        label = ["idcode","pktver","totlen","encryp","svctyp","rdplog",
                 "svcnum","loc_ip","loPort","targIP","tgPort","gw  IP",
                 "gwPort","Crtlen","CertID","Prolen","pronam","keylen",
                 "unikey","phshln","prhash","webass","ostype","msgtur"]
        segments = [11,2,2,1,4,4,4,4,2,4,2,4,2,2,0,2,0,2,0,2,0,4,2,2]
        hexdata = []
        for x in map(''.join,zip(*[iter(rawdata)]*2)):
            hexdata.append(x)
        
        idx = 0
        for i, seg in enumerate(segments):
            if len(segments) <= (i+1):
                pass
            else:
                if segments[i+1] == 0:
                    segments[i+1] = int(''.join(hexdata[idx:idx+seg]),16)

            print(label[i], ''.join(hexdata[idx:idx+seg]))
            idx += seg

        
class TermCtrl:
    """
    Telnet,FTP, SSH프로토콜을 사용하여 대상서버에서 작업하는 클래스
    대상서버 접속정보는 DB 또는 File에서 가져올 수 있다.

    Attr:
    server_list(DataFrame) : 대상서버 접속정보 및 client 객체
            name, svc_type(telnet, ftp, ssh), ip, port, userid, password
    conf(dic) : 설정정보
    lgr (Logger) : 로깅을 위한 인스턴스
    """
    lgr = None
    conf = None
    cols = None
    server_list = {}

    def __init__(self):
        self.lgr = Logger().getlogger("TermCtrl")
        self.conf = get_file_conf(CONF_PATH)
        cols = self.conf['Tables']['server_list_cols'].split(',')
        self.cols=[]
        for col in cols:
            self.server_list[col.strip()] = []
            self.cols.append(col.strip())
        self.server_list['client'] = []
        self.cols.append('client')
        
    def set_server_list(self):
        slist = get_server_list_csv(self.conf['File']['server_list_file'])
        for row in slist:
            for i,col in enumerate(self.cols[:-1]):
                try:
                    self.server_list[col.strip()].append(row[i])
                except Exception:
                    print(i, col, row, self.cols, slist)
            self.server_list['client'].append('None')
            
    def connect(self, proto, host, port, user, passwd, timeout=5, ifc=None, 
                usenatid=False, NatIdPkt=None):
        """ SSH, Telnet, FTP 접속 후 해당 접속 객체를 리턴함
        Args:
            proto (str): Protocol 'ssh','sftp','TELNET','FTP'
            host (str): host ip
            port (int or str): port
            user (str): user id
            passwd (str): passwd

        Returns:
            client(obj) : connected session object
        """
        proto = proto.lower()
        client = None
        if proto == 'telnet':
            client = tl.Telnet()
            try:
                client.open(host, int(port), int(timeout))
                client.read_until(b'login:')
                client.write(user.encode() + b'\n')
                client.read_until(b'Password:')
                client.write(passwd.encode() + b'\n')
            except Exception as e:
                self.lgr.error(e)
                print('%s:%s'%(host,port),e)
                return -1
        elif proto == 'ftp':
            client = fl.FTP()
            try:
                client.connect(host, int(port), int(timeout))
                client.login(user, passwd)
            except Exception as e:
                self.lgr.error(e)
                return -2
        elif proto in ['ssh', 'sftp']:
            sock = None
            if ifc != None:
                sock = skt.socket(skt.AF_INET, skt.SOCK_STREAM)
                sock.setsockopt(skt.SOL_SOCKET, skt.SO_BINDTODEVICE, (ifc+'\0').encode('utf8'))
                try:
                    sock.connect((host, int(port)))
                except Exception as e:
                    print(e, host+':'+str(port))
                    return -3
                if usenatid == True and NatIdPkt != None:
                    skt_name = sock.getsockname()
                    NatIdPkt.set(loport=skt_name[1])
                    sock.send(NatIdPkt.payload)
            client = pm.SSHClient()
            client.set_missing_host_key_policy(pm.AutoAddPolicy())
            try:
                test = client.connect(host, port=int(port), username=user,
                               password=passwd, timeout=int(timeout),
                               allow_agent=False, sock=sock,
                               banner_timeout=30, auth_timeout=30)
            except Exception as e:
                self.lgr.error("Connect SSH : ",e)
                print("Connect SSH : ", e)
                return -41

            if proto == 'ssh':
                try:
                    sh = client.invoke_shell()
                except Exception as e:
                    print("Invoke_shell : ", e)
                    return -42
                return (client, sh)
            
            if proto == 'sftp':
                try:
                    sftp = pm.SFTPClient.from_transport(client.get_transport())
                except Exception as e:
                    print("SFTP Connect : ",e)
                    self.lgr.error(e)
                    return -43
                return (client, sftp)
        else:
            self.lgr.error('Wrong protocol : %s' % proto)
            return -5
        return client
    
    def connect_list(self, cno = None):
        """ 
        server_list 서버 목록의 일부 또는 전체 서버에 접속을 시도하고 
        server_list에 접속 객체를 갱신함

        Args:
            cno(None,list,int): server_list의 index, 
                                None = 전체
                                list = 일부 ex. [1,4]
                                int = 특정 서버
        """
        ci = self.server_list
        if cno == None:
            cno = range(len(self.server_list['name']))
        for rc in cno:
            if ci['client'][rc] not in ('', 'None', '-1'):
                continue
            else:
                ci['client'][rc] = self.connect(str(ci['svc_type'][rc]),
                                                str(ci['host'][rc]), 
                                                int(ci['port'][rc]), 
                                                str(ci['userid'][rc]), 
                                                str(ci['passwd'][rc]))

    def show_clients(self):
        max_col_size = [0 for col in self.cols]
        data = []
        for i in range(len(self.server_list['name'])):
            row = []
            for c, col in enumerate(self.cols):
                try:
                    if max_col_size[c] < len(self.server_list[col][i]):
                        max_col_size[c] = len(self.server_list[col][i])
                except Exception as e:
                    max_col_size[c] = 32
                row.append(str(self.server_list[col][i]))
            data.append(row)
        
        row = ''
        for c, col in enumerate(self.cols):
            tmp = '{0:^%s}'%(max_col_size[c]+4)
            row += tmp.format(col) 
        print(row)
        
        for line in data:
            row = ''
            for c, col in enumerate(self.cols):
                tmp = '{0:^%s}'%(max_col_size[c]+4)
                row += tmp.format(line[c])
            print(row)

    def close_all(self):
        for i in range(len(self.server_list['name'])):
            c1 = self.server_list['client'][i] not in ['None','-1']
            if c1:
                try:
                    self.server_list['client'][i].close()
                except Exception as e:
                    self.lgr.error(e)
                self.server_list['client'][i] = -1

class CMDRunner():
    """
    명령어 테스트를 위한 클래스
    """
    lgr = None
    def __init__(self):
        self.lgr = Logger().getlogger("CMDRunner")

    def run_cmd(self, client, cmd, expected_result=''):
        buf = ''
        if type(client) == tl.Telnet or type(client) == pm.channel.Channel:
            self.wait_recv(client)
        if type(client) == pm.client.SSHClient:
            try:
                stdin, stdout, stderr = client.exec_command(cmd)
            except Exception as e:
                self.lgr.error(e)
                return -1
            buf = stdout.read() + stderr.read()
        elif type(client) == pm.channel.Channel:
            try:
                client.send(cmd+'\n')
                buf = self.wait_recv(client)
            except Exception as e:
                self.lgr.error(e)
        elif type(client) == tl.Telnet:
            try:
                client.write(cmd.encode() + b'\n')
                buf = self.wait_recv(client)
            except Exception as e:
                self.lgr.error(e)
        else:
            self.lgr.error('Wrong type client')
            return -1

        if type(buf) == str:
            pass
        else:
            buf = buf.decode()

        if buf.find(expected_result) > -1:
            return (True, buf)
        else:
            return (False, buf)
            
    def wait_recv(self, client, wait_count=3, decoding=False):
        """ Waiting for receiving the result of telnet command 

        Args:
            client (telnetlib.Telnet): telnet client object
            wait_count (int) : Seconds of waiting          
            decoding (bool) : whether make return data decoded or not
        Returns:
            received data (bytestring or str)
        """
        read_count = 0
        pre_read = 0
        read_wait = 0
        buf = b''
        # when SSH on invoke shell Client
        if type(client) == pm.channel.Channel:
            while True:
                if client.recv_ready():
                    buf += client.recv(65535)
                    read_count += 1
                else:
                    if pre_read < read_count :
                        pre_read = read_count
                        read_wait = 0
                    else:
                        if read_wait > wait_count:
                            break
                    read_wait += 1
                    time.sleep(0.1)
        # when Telnet Client
        elif type(client) == tl.Telnet:
            while True:
                tmp = client.read_eager()
                if tmp != b'':
                    buf += tmp
                    read_count += 1
                else:
                    if pre_read < read_count :
                        pre_read = read_count
                        read_wait = 0
                    else:
                        if read_wait > wait_count:
                            break
                    read_wait += 1
                    time.sleep(0.1)
        else:
            self.lgr.error('client type error: %s'%client)
            return -1
                
        if decoding:
            return buf.decode()
        else:
            return buf


class FTRunner():
    """
    파일 전송 테스트를 위한 클래스
    """
    lgr = None
    localcwd = None
    
    def __init__(self):
        self.lgr = Logger().getlogger('FTRunner')
        self.localcwd = os.getcwd()

    def get_file(self, client, dst_path, local_path=localcwd):
        '''
        dst_path(str) : 받아올 파일(절대 경로입력 필요)
        local_path(str) : 가져올 로컬 경로(절대 경로)
        '''
        if os.path.basename(local_path) == '':
            local_file = local_path + os.sep() + os.path.basename(dst_path)
        else:
            local_file = local_path
        # Client객체가 FTP인지 SFTP인지 체크한다
        if type(client) == fl.FTP:
            try:
                f = open(local_file,'wb')
                ftp_cmd = 'RETR ' + os.path.abspath(dst_path)
                client.retrbinary(ftp_cmd, f.write, blocksize=8192, rest=None)
                f.close()
            except Exception as e:
                print('DEBUG1:', e, dst_path)
                return -1
        elif type(client) == pm.sftp_client.SFTPClient:
            try:
                client.get(dst_path, local_path)
            except Exception as e:
                print('DEBUG2:', e, dst_path, local_path)
                return -1
        else:
            self.lgr.error("Wrong type Client")
            return -2
        return 0
        
    def put_file(self, client, src_path, dst_path):
        '''
        ftp 또는 ssh 클라이언트를 통해 원본경로의 내용을 대상경로로 업로드한다.
        :client: ssh client object
        :src_path: source path to upload
        :dst_path: target path to upload
        '''
        if os.path.basename(dst_path) == '': 
            dst_file = dst_path + os.sep() + os.path.basename(src_path)
        else:
            dst_file = dst_path
        # Client객체가 FTP인지 SFTP인지 체크한다
        if type(client) == fl.FTP:
            try:
                ftp_cmd = 'STOR ' + os.path.abspath(dst_file)
                client.storbinary(ftp_cmd, open(src_path,'rb'), blocksize=8192, callback=None, rest=None)
            except Exception as e:
                print(e)
                return -1
        elif type(client) == pm.sftp_client.SFTPClient:
            try:
                client.put(src_path, dst_file)
            except Exception as e:
                print('DEBUG:', e)
                return -2
        else:
            self.lgr.error("Wrong type Client")
        return 0
        # Check source path exists
        # Check destination path on target server exist
        # If directory does not exist, create directory
        

if __name__ == '__main__':
    pass
